from collections.abc import Mapping
import dataclasses
import enum
import exceptions

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

def get_int(mapping: Mapping[str, str], key: str, default: int) -> int:
    res = mapping.get(key)
    if res is None:
        return default
    if res.isdigit():
        return int(res)
    raise exceptions.BadInteger(f'{key}="{res}" not an int')


def get_enum(
    mapping: Mapping[str, str], key: str, default: enum.Enum | None) -> enum.Enum:
    if default is None:
        raise exceptions.BadEnum(f'default for key {key} is None')
    raw = mapping.get(key)
    if raw is None:
        return default
    enum_type = type(default)
    try:
        return enum_type(raw)
    except ValueError:
        raise exceptions.BadEnum(f'"{raw}" is not a {enum_type.__name__}')

# TODO: Make this (frozen=True)
@dataclasses.dataclass
class State:
    start_time: int
    elapsed_time: float
    increments: int
    timer_state: TimerState
    button: Button
    color_option: ColorOption
    time_format: TimeFormat
    font: str | None
    alarm_command: str | None
    read_input_command: str | None

def load_state(mapping: Mapping) -> State:
    return State(
        start_time = get_int(mapping, "start_time", 300),
        elapsed_time = get_int(mapping, "elapsed_time", 0),
        increments = get_int(mapping, "increments", 60),
        timer_state = get_enum(mapping, "state", TimerState.STOPPED),
        button = get_enum(mapping, "button", Button.NONE),
        color_option = get_enum(mapping, "colorize", ColorOption.NEVER),
        time_format = get_enum(mapping, "time_format", TimeFormat.PRETTY),
        font = mapping.get("font"),
        alarm_command = mapping.get("alarm_command"),
        read_input_command = mapping.get("read_input_command")
    )