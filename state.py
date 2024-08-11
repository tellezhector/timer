from collections.abc import Mapping
import dataclasses
import enum
import exceptions
import colors
import time_format


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


def set_font(text: str, font: str) -> str:
    return f"<span font_family='{font}'>{text}</span>"


def get_int(mapping: Mapping[str, str], key: str, default: int) -> int:
    res = mapping.get(key)
    if res is None:
        return default
    if res.isdigit():
        return int(res)
    raise exceptions.BadInteger(f'{key}="{res}" not an int')


def get_enum(
    mapping: Mapping[str, str], key: str, default: enum.Enum | None
) -> enum.Enum:
    if default is None:
        raise exceptions.BadEnum(f"default for key {key} is None")
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
    color_option: colors.ColorOption
    time_format: time_format.TimeFormat
    font: str | None
    alarm_command: str | None
    read_input_command: str | None

    def full_text(self):
        remaining = self.start_time - self.elapsed_time
        text = self.time_format.seconds_to_text(remaining)
        match self.color_option:
            case colors.ColorOption.COLORFUL:
                text = colors.colorize(text)
            case colors.ColorOption.RED_ON_NEGATIVES:
                if remaining < 0:
                    text = colors.red(text)
            case colors.ColorOption.COLORFUL_ON_NEGATIVES:
                if remaining < 0:
                    text = colors.colorize(text)
            case colors.ColorOption.NEVER:
                pass
        if self.font is not None:
            text = set_font(text, self.font)
        return text


def load_state(map_: Mapping) -> State:
    return State(
        start_time=get_int(map_, "start_time", 300),
        elapsed_time=get_int(map_, "elapsed_time", 0),
        increments=get_int(map_, "increments", 60),
        timer_state=get_enum(map_, "state", TimerState.STOPPED),
        button=get_enum(map_, "button", Button.NONE),
        color_option=get_enum(map_, "colorize", colors.ColorOption.NEVER),
        time_format=get_enum(map_, "time_format", time_format.TimeFormat.PRETTY),
        font=map_.get("font"),
        alarm_command=map_.get("alarm_command"),
        read_input_command=map_.get("read_input_command"),
    )
