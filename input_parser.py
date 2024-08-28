import enum
import re
from typing import Any
import logging

import exceptions

CLOCK_TIME_REGEX = re.compile(r"(\d+:)?\d+:\d+", flags=re.VERBOSE)
PRETTY_TIME_REGEX = re.compile(r"(\d+h)?(\d+m)?(\d+s)?")


@enum.unique
class InputType(enum.Enum):
    TIME_SET = "time_set"
    TIME_ADDITION = "time_addition"
    TIME_REDUCTION = "time_reduction"
    SET_PROPERTY = "set_property"
    SET_COLOR_OPTION = "set_color_option"
    VOID = "void"


def pretty_time_to_seconds(text: str) -> int:
    text = text.strip()
    if text.isnumeric():
        return int(text)
    if not PRETTY_TIME_REGEX.fullmatch(text):
        raise exceptions.BadPrettyTime(f'bad pretty time "{text}"')
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
    if not CLOCK_TIME_REGEX.fullmatch(text):
        raise exceptions.BadClockTime(f'bad clock time "{text}"')
    parts = text.split(":")
    secs = 0
    for part in parts:
        part = int(part)
        secs = (secs * 60) + part
    return secs


def parse_input(input: str) -> tuple[InputType, list[Any]]:
    input = input.strip()
    if not input:
        return (InputType.VOID, [])
    if "=" in input:
        property, value = input.split("=", 1)
        if property in (
            "timer_name",
            "text_format",
            "font",
            "alarm_command",
            "read_input_command",
            "running_label",
            "stopped_label",
            "paused_label",
        ):
            return (InputType.SET_PROPERTY, [property, value])
        elif property == "color_option":
            return (InputType.SET_COLOR_OPTION, [value])
        raise exceptions.BadPropertyPattern(f"unknown property: {property}")
    if input.startswith("+"):
        reduced = input[1:]
        time_type, time_in_secs = parse_input(reduced)
        if time_type != InputType.TIME_SET:
            raise exceptions.BadTimePattern(f"{reduced} is not a time pattern")
        return (InputType.TIME_ADDITION, time_in_secs)
    if input.startswith("-"):
        reduced = input[1:]
        time_type, time_in_secs = parse_input(reduced)
        if time_type != InputType.TIME_SET:
            raise exceptions.BadTimePattern(f"{reduced} is not a time pattern")
        return (InputType.TIME_REDUCTION, time_in_secs)
    if CLOCK_TIME_REGEX.fullmatch(input):
        return (InputType.TIME_SET, [clock_format_to_seconds(input)])
    if PRETTY_TIME_REGEX.fullmatch(input):
        return (InputType.TIME_SET, [pretty_time_to_seconds(input)])
    if input.isnumeric():
        return (InputType.TIME_SET, [int(input)])
    raise exceptions.BadValue(f"invalid input: {input}")
