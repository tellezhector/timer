#!/usr/bin/env python3
import json
import os
import logging
import logging_settings

from typing import Any, Mapping

import state as state_lib
import state_mutations


def main(mapping: Mapping[str, Any]):
    button = state_lib.Button(mapping.get('button'))
    state = state_lib.load_state(mapping, state_lib.now())
    try:
        if button != state_lib.Button.NONE:
            state = state_mutations.handle_clicks(state, button)
        else:
            state = state_mutations.handle_increments(state)
        serialized = state.serializable()
    except Exception as e:
        logging.exception(e)
        state = state_mutations.add_error(state, e, state_lib.now())
        serialized = state.serializable()
    finally:
        logging.debug(serialized)
        print(json.dumps(serialized), flush=True)


if __name__ == '__main__':
    log_file = os.getenv('log_file')
    if log_file:
        logging_settings.log_to_file(log_file)
    main(os.environ)
