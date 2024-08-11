from collections.abc import Mapping
import dataclasses
import enum
import subprocess
import logging
from typing import Any, Callable

import colors
import exceptions
import state_monad
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


@dataclasses.dataclass(frozen=True)
class State:
    start_time: int
    increments: int
    button: Button
    color_option: colors.ColorOption
    time_format: time_format.TimeFormat
    font: str | None
    alarm_command: str | None
    read_input_command: str | None
    running_label: str
    stopped_label: str
    paused_label: str

    # internal control - not modifiable through configuration
    elapsed_time: float
    timer_state: TimerState
    execute_read_input_command: bool = False
    execute_alert_command: bool = False

    def reset_transient_state(self) -> "State":
        return dataclasses.replace(
            self,
            button=Button.NONE,
            execute_read_input_command=False,
            execute_alert_command=False,
        )

    @property
    def label(self) -> str:
        match self.timer_state:
            case TimerState.RUNNING:
                return self.running_label
            case TimerState.PAUSED:
                return self.paused_label
            case TimerState.STOPPED:
                return self.stopped_label

    def build_alarm_command(self) -> str:
        return self.alarm_command.format(
            start_time=self.time_format.seconds_to_text(self.start_time)
        )

    @property
    def full_text(self) -> str:
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

    def serializable(self) -> dict[str, Any]:
        return {
            "full_text": self.full_text,
            "label": self.label,
            "start_time": self.start_time,
            "elapsed_time": self.elapsed_time,
            "timer_state": self.timer_state.value,
        }


def load_state(map_: Mapping) -> State:
    return State(
        start_time=get_int(map_, "start_time", 300),
        elapsed_time=get_int(map_, "elapsed_time", 0),
        increments=get_int(map_, "increments", 60),
        timer_state=get_enum(map_, "timer_state", TimerState.STOPPED),
        button=get_enum(map_, "button", Button.NONE),
        color_option=get_enum(map_, "colorize", colors.ColorOption.NEVER),
        time_format=get_enum(map_, "time_format", time_format.TimeFormat.PRETTY),
        font=map_.get("font"),
        alarm_command=map_.get("alarm_command"),
        read_input_command=map_.get("read_input_command"),
        running_label=map_.get("running_label", "running:"),
        stopped_label=map_.get("stopped_label", "timer:"),
        paused_label=map_.get("paused_label", "paused:"),
    )


def increase_elapsed_time_if_running(increment: float):
    def _increase_elapsed_time(state: State):
        if state.timer_state == TimerState.RUNNING:
            new_elapsed_time = state.elapsed_time + increment
            execute_alert_command = (
                state.elapsed_time < state.start_time
                and new_elapsed_time >= state.start_time
            )
            return (
                None,
                dataclasses.replace(
                    state,
                    elapsed_time=new_elapsed_time,
                    execute_alert_command=execute_alert_command,
                ),
            )
        return (None, state)

    return _increase_elapsed_time


def update_start_time(new_start_time: int) -> Callable[[State], tuple[Any, State]]:
    def _update_start_time(state: State) -> tuple[Any, State]:
        return (None, dataclasses.replace(state, start_time=new_start_time))

    return _update_start_time


def apply_click(state: State) -> tuple[Any, State]:
    match state.button:
        case Button.NONE:
            return (None, state)
        case Button.LEFT:
            if state.timer_state == TimerState.RUNNING:
                return (
                    None,
                    dataclasses.replace(state, timer_state=TimerState.PAUSED),
                )
            else:
                return (
                    None,
                    dataclasses.replace(state, timer_state=TimerState.RUNNING),
                )
        case Button.MIDDLE:
            new_state = dataclasses.replace(state)
            if state.read_input_command:
                input = subprocess.check_output(
                    state.read_input_command, shell=True, encoding="utf-8"
                )
                new_start_time = state.time_format.text_to_seconds(input)
                _, new_state = update_start_time(new_start_time)(new_state)
            logging.debug(type(new_state))
            return (
                None,
                dataclasses.replace(
                    new_state,
                    timer_state=TimerState.STOPPED,
                    elapsed_time=0,
                    execute_read_input_command=True,
                ),
            )
        case Button.RIGHT:
            return (
                None,
                dataclasses.replace(
                    state,
                    timer_state=TimerState.STOPPED,
                    elapsed_time=0,
                ),
            )
        case Button.SCROLL_UP:
            return (
                None,
                dataclasses.replace(
                    state, start_time=state.start_time + state.increments
                ),
            )
        case Button.SCROLL_DOWN:
            return (
                None,
                dataclasses.replace(
                    state, start_time=max(state.start_time - state.increments, 0)
                ),
            )
