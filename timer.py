#!/usr/bin/env python3
import json
import os
import logging

import state as state_lib
import state_mutations


if __name__ == "__main__":
    log_file = os.getenv("log_file")
    if log_file:
        logging.basicConfig(
            filename=log_file,
            encoding="utf-8",
            level=logging.DEBUG,
            format="{asctime} {name} {levelname:8s} {message}",
            style="{",
        )
    state = state_lib.load_state(os.environ, state_lib.now())
    try:
        state = state_mutations.clicks_and_increments(state)
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
