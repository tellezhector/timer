#!/usr/bin/env python3
import datetime
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
    now = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    state = state_lib.load_state(os.environ, now)
    try:
        state = state_mutations.clicks_and_increments(state)
    except Exception as e:
        logging.exception(e)
        state = state_mutations.add_error(state, e)
    finally:
        logging.debug(state.serializable())
        print(json.dumps(state.serializable()), flush=True)
