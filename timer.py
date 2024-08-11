#!/usr/bin/env python3
import json
import os
import subprocess
import logging

import exceptions
import state as state_lib

def build_output(init_state: state_lib.State):
    _, state = state_lib.apply_click(init_state)
    # TODO: do not assume that increment is of size 1
    _, state = state_lib.increase_elapsed_time_if_running(1)(state)

    if state.execute_alert_command:
        subprocess.call(
            state.build_alarm_command(),
            shell=True,
        )

    return state.reset_transient_state()


if __name__ == "__main__":
    try:
        log_file = os.getenv("log_file")
        if log_file:
            logging.basicConfig(
                filename=log_file,
                encoding="utf-8",
                level=logging.DEBUG,
                format="{asctime} {name} {levelname:8s} {message}",
                style="{",
            )
        init_state = state_lib.load_state(os.environ)
        final_state = build_output(init_state)
        logging.debug(final_state.serializable())
        print(json.dumps(final_state.serializable()))
    except Exception as e:
        logging.exception(e)
        full_text = str(e)
        short_text = str(e)[:40]
        if isinstance(e, exceptions.TimerException):
            full_text = getattr(e, "message")
            short_text = full_text[:40]
        error_log = {
            "full_text": full_text,
            "short_text": short_text,
            "background": "#FF0000",
            "color": "#FFFFFF",
        }
        logging.error(error_log)
        print(json.dumps(error_log))
