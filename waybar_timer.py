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

_PIPE_FILE_PATH = '/tmp/waybar_timer.action.pipe'
_LOG_FILE = os.getenv('log_file', '/tmp/timer_log.txt')

def main(mapping: Mapping[str, Any]):
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
        line = sys.stdin.readline().strip()
        try:
          mapping = json.loads(line)
          button = state_lib.get_button(mapping)
          new_state = state_mutations.handle_clicks(state, button)
          logging.debug('good line "%s"', line)
          _update_state(new_state)
        except Exception as e:
            logging.error('bad line "%s"', line)
            logging.exception(e)
            state = _update_state(state_mutations.add_error(state, e, state_lib.now()))
        

    thread = threading.Thread(group=None, target=listen_for_actions, name=None)
    thread.start()

    while True:
      counter += 1
      try:
          now_state = state_mutations.add_new_timestamp(state, state_lib.now())
          _update_state(state_mutations.handle_increments(now_state))
          serialized = state.serializable()
      except Exception as e:
          logging.exception(e)
          _update_state(state_mutations.add_error(state, e, state_lib.now()))
          serialized = state.serializable()
      finally:
          dump = json.dumps(serialized)
          logging.debug('state as it was dumped: "%s"', dump)
          print(dump, flush=True)
      time.sleep(0.07)


if __name__ == '__main__':
    if _LOG_FILE:
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
        main({})
    # If an action was passed, write it to a named pipe and exit.
    # Pipe path can be overridden with the ACTION_PIPE environment variable.
    elif args.action is not None:
        try:
            if not os.path.exists(_PIPE_FILE_PATH):
                os.mkfifo(_PIPE_FILE_PATH, 0o600)
        except Exception as e:
            logging.exception('Failed to ensure pipe exists: %s', _PIPE_FILE_PATH)
            # fall back to setting env var for compatibility, then exit non-zero
            sys.exit(1)

        try:
            # Opening a FIFO for writing will block until a reader opens it.
            # This writes the action followed by a newline.
            fd = os.open(_PIPE_FILE_PATH, os.O_WRONLY | os.O_NONBLOCK)
            with os.fdopen(fd, 'w') as pf:
                logging.debug('Writing action to pipe: %s', args.action)
                pf.write(args.action + "\n")
                pf.flush()
        except Exception as e:
            logging.exception('Failed to write action to pipe: %s', _PIPE_FILE_PATH)
            # fallback: set environment variable for compatibility
            sys.exit(1)

        # Successfully wrote action to pipe; exit.
        sys.exit(0)

