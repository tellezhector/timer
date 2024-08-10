#!/usr/bin/env python3
import json
import os
import subprocess
import logging
import random

import colors
import exceptions
import state as state_lib
from state import Button, TimerState

def set_font(text: str, font: str) -> str:
    return f"<span font_family='{font}'>{text}</span>"


def red(text: str) -> str:
    return f"<span color='{colors.RED}'>{text}</span>"


def colorize(text: str) -> str:
    result = ""
    for c in text:
        result += f"<span color='{random.choice(colors.COLORS)}'>{c}</span>"
    return result


def get_label(timer_state: TimerState) -> str:
    match timer_state:
        case TimerState.RUNNING:
            # \uf04b
            return ""
        case TimerState.PAUSED:
            # \uf04c
            return ""
        case TimerState.STOPPED:
            # \uf251
            return ""


def build_output(state: state_lib.State):
    # TODO: remove state mutations from here
    match state.button:
        case Button.LEFT:
            if state.timer_state == TimerState.RUNNING:
                state.timer_state = TimerState.PAUSED
            else:
                state.timer_state = TimerState.RUNNING
        case Button.MIDDLE:
            if state.read_input_command:
                input = subprocess.check_output(
                    state.read_input_command, shell=True, encoding="utf-8"
                )
                state.start_time = state.time_format.text_to_seconds(input)
            state.timer_state = TimerState.STOPPED
            state.elapsed_time = 0
        case Button.RIGHT:
            state.timer_state = TimerState.STOPPED
            state.elapsed_time = 0
        case Button.SCROLL_UP:
            state.start_time = start_time + state.increments
        case Button.SCROLL_DOWN:
            state.start_time = max(start_time - increments, 0)

    state.elapsed_time = (
        state.elapsed_time + 1 if state.timer_state == TimerState.RUNNING else state.elapsed_time
    )
    remaining = state.start_time - state.elapsed_time
    if state.start_time > 0 and remaining == 0 and state.alarm_command:
        subprocess.call(
            state.alarm_command.format(
                start_time=state.time_format.seconds_to_text(state.start_time)
            ),
            shell=True,
        )

    text = state.time_format.seconds_to_text(remaining)
    match state.color_option:
        case state_lib.ColorOption.COLORFUL:
            text = colorize(text)
        case state_lib.ColorOption.RED_ON_NEGATIVES:
            if remaining < 0:
                text = red(text)
        case state_lib.ColorOption.COLORFUL_ON_NEGATIVES:
            if remaining < 0:
                text = colorize(text)
        case state_lib.ColorOption.NEVER:
            pass

    if state.font is not None:
        text = set_font(text, state.font)

    res = {
        "full_text": text,
        "label": get_label(state.timer_state),
        "start_time": state.start_time,
        "elapsed_time": state.elapsed_time,
        "state": state.timer_state.value
    }

    return res


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
        output = build_output(init_state)
        logging.debug(output)
        print(json.dumps(output))
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
