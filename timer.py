#!/usr/bin/env python3
import json
import os
import logging
import logging.handlers

import state as state_lib
import state_mutations


if __name__ == '__main__':
    log_file = os.getenv('log_file')
    if log_file:
        rotating_file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file, 
            mode='a',
            maxBytes=128*1024*1024, # 128 MB
            backupCount=2,
            encoding='utf-8',
            delay=0
        )
        logging.basicConfig(
            encoding='utf-8',
            level=logging.DEBUG,
            format='{asctime} {name} {levelname:8s} {message}',
            style='{',
            handlers=[rotating_file_handler]
        )
    button = state_lib.Button(os.environ.get('button'))
    state = state_lib.load_state(os.environ, state_lib.now())
    try:
        if button != state_lib.Button.NONE:
          state = state_mutations.handle_clicks(state, button)
        else:
          state = state_mutations.handle_increments(state)
        serialized = state.serializable()
    except Exception as e:
        logging.exception(e)
        # Since some I/O errors take longer to be generated,
        # refreshing the timestamp is necessary to avoid time-skips or
        # error messages shown for too little.
        state = state_mutations.add_error(state, e, state_lib.now())
        serialized = state.serializable()
    finally:
        logging.debug(serialized)
        print(json.dumps(serialized), flush=True)
