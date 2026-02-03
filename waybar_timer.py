#!/usr/bin/env python3
import json
import os
import logging
import sys
import threading
import time
import argparse
from typing import Any, Mapping

import logging_settings


import state as state_lib
import state_mutations

# Call like `log_file=/tmp/timer_log.txt ./waybar_timer.py` to enable logging to a file
_LOG_FILE = os.getenv('log_file', None)

_FIFO_FILE_PATH = os.getenv('fifo_path', '/tmp/waybar_timer.action.pipe')


def serve(mapping: Mapping[str, Any]):
    state = state_lib.load_state(mapping, state_lib.now())
    counter = 0
    lock = threading.Lock()

    def _update_state(new_state):
       nonlocal state
       lock.acquire()
       state = new_state
       lock.release()

    def listen_for_actions():
      nonlocal state
      while True:
        create_fifo_if_not_exists(_FIFO_FILE_PATH)
        with open(_FIFO_FILE_PATH, 'r') as pf:
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
                    _update_state(state_mutations.add_error(state, e, state_lib.now()))

        

    thread = threading.Thread(group=None, target=listen_for_actions, name=None)
    thread.start()

    while True:
      counter += 1
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
          print(dump, flush=True)
      time.sleep(0.07)


def create_fifo_if_not_exists(fifo_path: str):
    """Create a named FIFO at the specified path if it does not already exist."""
    try:
        if not os.path.exists(fifo_path):
            os.mkfifo(fifo_path, 0o600)
    except Exception:
        logging.exception('Failed to ensure FIFO exists: %s', fifo_path)
        # fall back to setting env var for compatibility, then exit non-zero
        sys.exit(1)

def write_action(action: str):
    """Write the specified action to the named FIFO."""
    create_fifo_if_not_exists(_FIFO_FILE_PATH)

    try:
        # Opening a FIFO for writing will block until a reader opens it.
        # This writes the action followed by a newline.
        fd = os.open(_FIFO_FILE_PATH, os.O_WRONLY | os.O_NONBLOCK)
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
        logging.exception(f'Failed to write action to FIFO: %s', _FIFO_FILE_PATH)
        # fallback: set environment variable for compatibility
        sys.exit(1)

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
        # serve mode: continue running
        serve({})
    # If an action was passed, write it to a named FIFO and exit.
    # FIFO path can be overridden with the `fifo_path` environment variable.
    elif args.action is not None:
        write_action(args.action)
        # Successfully wrote action to FIFO; exit.
        sys.exit(0)

