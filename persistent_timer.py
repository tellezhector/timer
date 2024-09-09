#!/usr/bin/env python3
import json
import os
import logging
import sys
import threading
import time
from typing import Any, Mapping

import logging_settings


import state as state_lib
import state_mutations


def main(mapping: Mapping[str, Any]):
    state = state_lib.load_state(mapping, state_lib.now())
    counter = 0
    clicks = 0
    lock = threading.Lock()

    def _update_state(new_state):
       nonlocal state
       lock.acquire()
       state = new_state
       lock.release()

    def listen_for_clicks():
      nonlocal clicks, state
      while True:
        line = sys.stdin.readline().strip()
        logging.debug('clicked!')
        try:
          clicks += 1
          mapping = json.loads(line)
          button = state_lib.get_button(mapping)
          logging.debug(f'{button=}')
          logging.debug(f'{mapping.get("button")=}')
          new_state = state_mutations.handle_clicks(state, button)
          logging.debug(f'{new_state.timer_state=}')
          _update_state(new_state)
          logging.debug(f'{state.timer_state=}')
        except Exception as e:
            logging.exception(e)
            state = _update_state(state_mutations.add_error(state, e, state_lib.now()))
        

    thread = threading.Thread(group=None, target=listen_for_clicks, name=None)
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
          logging.debug(serialized)
          print(json.dumps(serialized), flush=True)
      time.sleep(0.1)


if __name__ == '__main__':
    log_file = os.getenv('log_file')
    if log_file:
        logging_settings.log_to_file(log_file)
    main(os.environ)
