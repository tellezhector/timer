#!/usr/bin/env python3
import json
import os
import logging
import sys
import threading
import time
import argparse

import socket
import struct

import logging_settings


import state as state_lib
import state_mutations

# Call like `log_file=/tmp/timer_log.txt ./waybar_timer.py` to enable logging to a file
_LOG_FILE = os.getenv('log_file', None)

# Used to communicate actions to server process.
_FIFO_FILE_PATH = os.getenv('fifo_path', '/tmp/waybar_timer.action.pipe')

# A common local multicast test address and port.
_MCAST_ADDR = '224.1.1.1'
_MCAST_PORT = 5007

# A port for a simple TCP lock to ensure only one server is running.
_LOCK_PORT = 6000

# Time interval between publishes
_SLEEP_TIME_IN_SECONDS = 0.09


class MulticastPublisher:
    def __init__(self, mcast_addr: str, mcast_port: int):
        self.mcast_addr = mcast_addr
        self.mcast_port = mcast_port
        self.sock = None
        self.counter = 0

    def setup(self):
        # --- STEP 1: THE PUBLISHING ---
        # Create the socket (AF_INET = IPv4, SOCK_DGRAM = UDP)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # --- STEP 2: Enable loopback so we can receive our own packets ---
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        # --- STEP 3: Force the socket to send via the loopback interface ---
        local_interface = socket.inet_aton('127.0.0.1')
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, local_interface)

        # --- STEP 4: TTL ---
        # Set Time-to-Live (TTL) to 1 so packets don't leave the local network
        ttl = struct.pack('b', 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def publish(self, message: str):
        self.sock.sendto(message.encode('utf-8'), (self.mcast_addr, self.mcast_port))
        self.counter += 1

    @classmethod
    def build(cls, mcast_addr: str, mcast_port: int):
        publisher = cls(mcast_addr, mcast_port)
        publisher.setup()
        return publisher


class MulticastSubscriber:
    def __init__(self, mcast_addr: str, mcast_port: int, timeout_seconds: float):
        self.mcast_addr = mcast_addr
        self.mcast_port = mcast_port
        self.timeout_seconds = timeout_seconds
        self.sock = None

    def setup(self):
        # --- STEP 1: Create the socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # --- STEP 2: Allow multiple sockets to use the same port number
        # This is crucial so you can run multiple copies of this script at once
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # --- STEP 3: Bind to the port
        # '' (empty string) usually works for all interfaces.
        self.sock.bind(('', self.mcast_port))

        # --- STEP 4: Tell the OS to add this socket to the Multicast Group
        # This is the "Magic" part that makes it Pub/Sub
        group = socket.inet_aton(self.mcast_addr)
        local_interface = socket.inet_aton('127.0.0.1')
        mreq = struct.pack('4s4s', group, local_interface)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.settimeout(self.timeout_seconds)

    def receive(self) -> str:
        data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
        decoded = data.decode('utf-8')
        logging.debug('Received message from %s: %s', addr, decoded)
        return decoded

    @classmethod
    def build(cls, mcast_addr: str, mcast_port: int, timeout_seconds: float):
        subscriber = cls(mcast_addr, mcast_port, timeout_seconds)
        subscriber.setup()
        return subscriber


def serve(fifo_file_path: str, publisher: MulticastPublisher):
    state = state_lib.load_state({}, state_lib.now())
    lock = threading.Lock()

    def _update_state(new_state):
        nonlocal state
        lock.acquire()
        state = new_state
        lock.release()

    def listen_for_actions():
        nonlocal state
        while True:
            create_fifo_if_not_exists(fifo_file_path)
            with open(fifo_file_path, 'r') as pf:
                for raw in pf:
                    line = raw.strip()
                    if not line:
                        continue
                    try:
                        mapping = json.loads(line)
                        button = state_lib.get_button(mapping)
                        new_state = state_mutations.handle_clicks(state, button)
                        logging.debug('good line "%s"', line)
                        _update_state(new_state)
                    except Exception as e:
                        logging.error('bad line "%s"', line)
                        logging.exception(e)
                        _update_state(
                            state_mutations.add_error(state, e, state_lib.now())
                        )

    actions_thread = threading.Thread(group=None, target=listen_for_actions, name=None)
    actions_thread.start()

    def time_ticker():
        nonlocal state
        while True:
            try:
                now_state = state_mutations.add_new_timestamp(state, state_lib.now())
                _update_state(state_mutations.handle_increments(now_state))
                serialized = state.serializable_for_waybar()
            except Exception as e:
                logging.exception(e)
                _update_state(state_mutations.add_error(state, e, state_lib.now()))
                serialized = state.serializable_for_waybar()
            finally:
                dump = json.dumps(serialized)
                logging.debug('state as it was dumped: "%s"', dump)
                publisher.publish(dump)
            time.sleep(_SLEEP_TIME_IN_SECONDS)

    time_ticker_thread = threading.Thread(group=None, target=time_ticker, name=None)
    time_ticker_thread.start()


def create_fifo_if_not_exists(fifo_path: str):
    """Create a named FIFO at the specified path if it does not already exist."""
    try:
        if not os.path.exists(fifo_path):
            os.mkfifo(fifo_path, 0o600)
    except Exception:
        logging.exception('Failed to ensure FIFO exists: %s', fifo_path)
        # fall back to setting env var for compatibility, then exit non-zero
        sys.exit(1)


def write_action(fifo_file_path: str, action: str):
    """Write the specified action to the named FIFO."""
    create_fifo_if_not_exists(fifo_file_path)

    try:
        # Opening a FIFO for writing will block until a reader opens it.
        # This writes the action followed by a newline.
        fd = os.open(fifo_file_path, os.O_WRONLY | os.O_NONBLOCK)
        with os.fdopen(fd, 'w') as pf:
            logging.debug('Writing action to FIFO: %s', action)
            result = {}
            match action:
                case 'resume' | 'start' | 'pause' | 'start_pause':
                    result['button'] = state_lib.Button.LEFT.value
                case 'reset':
                    result['button'] = state_lib.Button.RIGHT.value
                case 'increase':
                    result['button'] = state_lib.Button.SCROLL_UP.value
                case 'decrease':
                    result['button'] = state_lib.Button.SCROLL_DOWN.value
                case _:
                    logging.error('Unknown action: %s', action)
                    sys.exit(1)
            pf.write(json.dumps(result) + "\n")
            pf.flush()
    except Exception as e:
        logging.exception(f'Failed to write action to FIFO: %s', fifo_file_path)
        # fallback: set environment variable for compatibility
        sys.exit(1)


def attempt_lock(lock_port: int) -> socket.socket | None:
    """Try to acquire the lock by binding to the lock port."""
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        lock_socket.bind(('127.0.0.1', lock_port))
    except OSError:
        logging.error(
            'Another instance is already running on port %d. Won\'t serve!', lock_port
        )
        return None
    logging.debug('will serve! %s is free!', lock_port)
    return lock_socket


def serve_or_take_over__then_listen(
    lock_port: int,
    mcast_addr: str,
    mcast_port: int,
    fifo_path: str,
    sleep_time_in_seconds: float,
):
    # If nothing else seems to be running, start a server and then
    # listen to it for messages.
    #
    # If another process is already serving, then just listen as a subscriber.
    while True:
        lock_socket = attempt_lock(lock_port)
        if lock_socket is not None:
            publisher = MulticastPublisher.build(mcast_addr, mcast_port)
            serve(fifo_path, publisher)

        subscriber = MulticastSubscriber.build(
            mcast_addr, mcast_port, sleep_time_in_seconds
        )
        try:
            while True:
                message = subscriber.receive()
                print(message, flush=True)
        except socket.timeout:
            logging.error(
                'No message received within timeout period (%.3f seconds); trying to take over as server.',
                sleep_time_in_seconds,
            )


if __name__ == '__main__':
    if _LOG_FILE is not None:
        logging_settings.log_to_file(_LOG_FILE)

    parser = argparse.ArgumentParser(description='Waybar timer')
    parser.add_argument('--serve', action='store_true', help='Run in serve mode')
    parser.add_argument('--action', type=str, help='Action to perform')
    args = parser.parse_args()

    logging.debug('Arguments: %s', args)
    logging.debug(f'{args.serve=}, {args.action=}')

    # Exactly one of --serve or --action must be provided
    if bool(args.serve) == bool(args.action):
        parser.error('Exactly one of --serve or --action must be specified')

    if args.serve:
        serve_or_take_over__then_listen(
            _LOCK_PORT,
            _MCAST_ADDR,
            _MCAST_PORT,
            _FIFO_FILE_PATH,
            _SLEEP_TIME_IN_SECONDS * 5,
        )

    # If an action was passed, write it to a named FIFO and exit.
    # FIFO path can be overridden with the `fifo_path` environment variable.
    elif args.action is not None:
        write_action(_FIFO_FILE_PATH, args.action)
        # Successfully wrote action to FIFO; exit.
        sys.exit(0)
