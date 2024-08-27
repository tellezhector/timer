import enum
import re

import exceptions


@enum.unique
class TimeFormat(enum.Enum):
    PRETTY = "pretty"
    CLOCK = "clock"

    def seconds_to_text(self, seconds: float) -> str:
        if self == TimeFormat.PRETTY:
            return seconds_to_pretty_time(int(seconds))
        if self == TimeFormat.CLOCK:
            return seconds_to_clock_format(int(seconds))


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
