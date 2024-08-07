#!/usr/bin/env python3
from collections.abc import Mapping

import json
import os
import subprocess
import logging
import enum
import random
import re

import colors
import timer_exceptions


@enum.unique
class Button(enum.Enum):
    NONE = None
    LEFT = "1"
    MIDDLE = "2"
    RIGHT = "3"
    SCROLL_UP = "4"
    SCROLL_DOWN = "5"


@enum.unique
class TimerState(enum.Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@enum.unique
class ColorOption(enum.Enum):
    NEVER = "never"
    COLORFUL = "colorful"
    COLORFUL_ON_NEGATIVES = "colorful_on_negatives"
    RED_ON_NEGATIVES = "red_on_negatives"


def pretty_time_to_seconds(text: str) -> int:
    text = text.strip()
    if text.isnumeric():
        return int(text)
    regex = re.compile(r"(\d+h)?(\d+m)?(\d+s)?")
    if not regex.fullmatch(text):
        raise timer_exceptions.BadPrettyTime(f'bad pretty time "{text}"')
    res = 0
    if "h" in text:
        hrs, text = text.split("h")
        res += 3600 * int(hrs)
    if "m" in text:
        mins, text = text.split("m")
        res += 60 * int(mins)
    if "s" in text:
        secs, text = text.split("s")
        res += int(secs)
    return res


def clock_format_to_seconds(text: str) -> int:
    text = text.strip()
    if text.isnumeric():
        return int(text)
    regex = re.compile(r"(\d+:)?\d+:\d+")
    if not regex.fullmatch(text):
        raise timer_exceptions.BadClockTime(f'bad clock time "{text}"')
    parts = text.split(":")
    secs = 0
    for part in parts:
        part = int(part)
        secs = (secs * 60) + part
    return secs


def seconds_to_clock_format(secs: int) -> str:
    res = ""
    if secs < 0:
        res += "-"
        secs = secs * -1

    if secs == 0:
        return res + "0s"

    hrs, secs = divmod(secs, 3600)
    mins, secs = divmod(secs, 60)
    if hrs:
        res += f"{hrs}:"
    res += f"{mins}:{secs:02d}"
    return res


def seconds_to_pretty_time(secs: int) -> str:
    res = ""
    if secs < 0:
        res += "-"
        secs = secs * -1

    if secs == 0:
        return res + "0s"

    hrs, secs = divmod(secs, 3600)
    mins, secs = divmod(secs, 60)
    if hrs:
        res += f"{hrs}h"
    if mins:
        res += f"{mins}m"
    if secs > 0:
        res += f"{secs}s"
    return res


def set_font(text: str, font: str) -> str:
    return f"<span font_family='{font}'>{text}</span>"


def red(text: str) -> str:
    return f"<span color='{colors.RED}'>{text}</span>"


def colorize(text: str) -> str:
    result = ""
    for c in text:
        result += f"<span color='{random.choice(colors.COLORS)}'>{c}</span>"
    return result


def get_label(state: TimerState) -> str:
    match state:
        case TimerState.RUNNING:
            # \uf04b
            return ""
        case TimerState.PAUSED:
            # \uf04c
            return ""
        case TimerState.STOPPED:
            # \uf251
            return ""


@enum.unique
class TimeFormat(enum.Enum):
    PRETTY = "pretty"
    CLOCK = "clock"

    def seconds_to_text(self, seconds) -> str:
        if self == TimeFormat.PRETTY:
            return seconds_to_pretty_time(seconds)
        if self == TimeFormat.CLOCK:
            return seconds_to_clock_format(seconds)

    def text_to_seconds(self, text) -> int:
        if self == TimeFormat.PRETTY:
            return pretty_time_to_seconds(text)
        if self == TimeFormat.CLOCK:
            return clock_format_to_seconds(text)


def get_int(mapping: Mapping[str, str], key: str, default: int) -> int:
    res = mapping.get(key)
    if res is None:
        return default
    if res.isdigit():
        return int(res)
    raise timer_exceptions.BadInteger(f'{key}="{res}" not an int')


def get_enum(
    mapping: Mapping[str, str], enum_type: enum.EnumMeta, key: str, default: enum.Enum
) -> enum.Enum:
    raw = mapping.get(key)
    if raw is None and default is not None:
        return default
    try:
        return enum_type(raw)
    except ValueError:
        raise timer_exceptions.BadEnum(f'"{raw}" is not a {enum_type.__name__}')


def build_next_state():
    start_time = get_int(os.environ, "start_time", 300)
    elapsed_time = get_int(os.environ, "elapsed_time", 0)
    increments = get_int(os.environ, "increments", 60)
    timer_state = get_enum(os.environ, TimerState, "state", TimerState.STOPPED)
    button = get_enum(os.environ, Button, "button", Button.NONE)
    color_option = get_enum(os.environ, ColorOption, "colorize", ColorOption.NEVER)
    time_format = get_enum(os.environ, TimeFormat, "time_format", TimeFormat.PRETTY)
    font = os.environ.get("font")
    alarm_command = os.environ.get("alarm_command")
    read_input_command = os.environ.get("read_input_command")
    match button:
        case Button.LEFT:
            if timer_state == TimerState.RUNNING:
                timer_state = TimerState.PAUSED
            else:
                timer_state = TimerState.RUNNING
        case Button.MIDDLE:
            if read_input_command:
                input = subprocess.check_output(
                    read_input_command, shell=True, encoding="utf-8"
                )
                start_time = time_format.text_to_seconds(input)
            timer_state = TimerState.STOPPED
            elapsed_time = 0
        case Button.RIGHT:
            timer_state = TimerState.STOPPED
            elapsed_time = 0
        case Button.SCROLL_UP:
            start_time = start_time + increments
        case Button.SCROLL_DOWN:
            start_time = max(start_time - increments, 0)

    elapsed_time = (
        elapsed_time + 1 if timer_state == TimerState.RUNNING else elapsed_time
    )
    remaining = start_time - elapsed_time
    if start_time > 0 and remaining == 0 and alarm_command:
        subprocess.call(
            alarm_command.format(start_time=time_format.seconds_to_text(start_time)),
            shell=True,
        )

    text = time_format.seconds_to_text(remaining)
    match color_option:
        case color_option.COLORFUL:
            text = colorize(text)
        case color_option.RED_ON_NEGATIVES:
            if remaining < 0:
                text = red(text)
        case color_option.COLORFUL_ON_NEGATIVES:
            if remaining < 0:
                text = colorize(text)
        case color_option.NEVER:
            pass

    if font is not None:
        text = set_font(text, font)

    res = {
        "full_text": text,
        "label": get_label(timer_state),
        "start_time": start_time,
        "elapsed_time": elapsed_time,
        "state": timer_state.value,
        "interval": 1,
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
        next_state = build_next_state()
        logging.debug(next_state)
        print(json.dumps(next_state))
    except Exception as e:
        logging.exception(e)
        full_text = str(e)[:40]
        short_text = str(e)[:20]
        if isinstance(e, timer_exceptions.TimerException):
            full_text = getattr(e, "message")
        error_log = {
            "full_text": full_text,
            "short_text": short_text,
            "background": "#FF0000",
            "color": "#FFFFFF",
        }
        logging.error(error_log)
        print(json.dumps(error_log))
