import enum
import re

import exceptions


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


def pretty_time_to_seconds(text: str) -> int:
    text = text.strip()
    if text.isnumeric():
        return int(text)
    regex = re.compile(r"(\d+h)?(\d+m)?(\d+s)?")
    if not regex.fullmatch(text):
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
    regex = re.compile(r"(\d+:)?\d+:\d+")
    if not regex.fullmatch(text):
        raise exceptions.BadClockTime(f'bad clock time "{text}"')
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
