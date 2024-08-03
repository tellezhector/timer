#!/usr/bin/env python3

import json
import os
import subprocess
import logging
import enum
import random
import re


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
        raise ValueError(f'"{text}" does not satisfy {regex}')
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
        raise ValueError(f'"{text}" does not satisfy {regex}')
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


def monospace(text: str) -> str:
    return f"<span font_family='monospace'>{text}</span>"


def red(text: str) -> str:
    colors = [
        "#BB0A21",  # red
    ]
    result = ""
    for c in text:
        result += f"<span color='{random.choice(colors)}'>{c}</span>"
    return result


def colorize(text: str) -> str:
    colors = [
        "#F564A9",  # red
        "#FFBC42",  # Xanthous (yellow)
        "#5EB1BF",  # Moonstone (light blue)
        "#F564A9",  # Hot pink
        "#04F06A",  # Spring green
    ]
    result = ""
    for c in text:
        result += f"<span color='{random.choice(colors)}'>{c}</span>"
    return result


def get_label(state: TimerState) -> str:
    match state:
        case TimerState.RUNNING:
            return ""
        case TimerState.PAUSED:
            return ""
        case TimerState.STOPPED:
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


def main():
    start_time = int(os.getenv("start_time", 300))
    elapsed_time = int(os.getenv("elapsed_time", 0))
    increments = int(os.getenv("increments", 60))
    state = TimerState(os.getenv("state", "stopped"))
    button = Button(os.getenv("button"))
    colorOption = ColorOption(os.getenv("colorize", "never"))
    use_monospace = os.getenv("monospace") is not None
    time_format = TimeFormat(os.getenv("time_format", "pretty"))
    match button:
        case Button.LEFT:
            if state == TimerState.RUNNING:
                state = TimerState.PAUSED
            else:
                state = TimerState.RUNNING
        case Button.MIDDLE:
            read_input_command = os.getenv("read_input_command")
            if read_input_command:
                input = subprocess.check_output(
                    read_input_command, shell=True, encoding="utf-8"
                )
                start_time = time_format.text_to_seconds(input)
            state = TimerState.STOPPED
            elapsed_time = 0
        case Button.RIGHT:
            state = TimerState.STOPPED
            elapsed_time = 0
        case Button.SCROLL_UP:
            start_time = start_time + increments
        case Button.SCROLL_DOWN:
            start_time = max(start_time - increments, 0)

    alarm_command = os.getenv("alarm_command")

    elapsed_time = elapsed_time + 1 if state == TimerState.RUNNING else elapsed_time
    remaining = start_time - elapsed_time
    if start_time > 0 and remaining == 0 and alarm_command:
        subprocess.call(
            alarm_command.format(start_time=time_format.seconds_to_text(start_time)),
            shell=True,
        )

    text = time_format.seconds_to_text(remaining)
    match colorOption:
        case colorOption.COLORFUL:
            text = colorize(text)
        case colorOption.RED_ON_NEGATIVES:
            if remaining < 0:
                text = red(text)
        case colorOption.COLORFUL_ON_NEGATIVES:
            if remaining < 0:
                text = colorize(text)
        case colorOption.NEVER:
            pass

    if use_monospace:
        text = monospace(text)

    res = {
        "full_text": text,
        "label": get_label(state),
        "start_time": start_time,
        "elapsed_time": elapsed_time,
        "state": state.value,
        "interval": 1,
    }

    logging.debug(res)
    print(json.dumps(res))


if __name__ == "__main__":
    try:
        log_file = os.getenv("log_file")
        if log_file:
            logging.basicConfig(
                filename=log_file, 
                encoding="utf-8", 
                level=logging.DEBUG,
                format='{asctime} {name} {levelname:8s} {message}',
                style='{'
            )
        main()
    except Exception as e:
        logging.exception(e)
