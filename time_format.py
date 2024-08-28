import string
import logging


class Formatter(string.Formatter):

    def format_field(self, value, format_spec):
        match format_spec:
            case "pretty":
                value = int(float(value))
                return seconds_to_pretty_time(value)
            case "clock":
                value = int(float(value))
                return seconds_to_clock_format(value)
        return super().format_field(value, format_spec)


FORMATTER = Formatter()


def seconds_to_clock_format(secs: int) -> str:
    res = ""
    if secs < 0:
        res += "-"
        secs = secs * -1

    if secs == 0:
        return res + "00:00"

    hrs, secs = divmod(secs, 3600)
    mins, secs = divmod(secs, 60)
    if hrs:
        res += f"{hrs}:"
    res += f"{mins:02d}:{secs:02d}"
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
