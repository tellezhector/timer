from collections.abc import Mapping
import dataclasses
import enum
import subprocess
from typing import Any, Callable

import colors
import exceptions
from monads import StateMonad
import time_format
import input_parser


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

def get_float(mapping: Mapping[str, str], key: str, default: float) -> float:
    res = mapping.get(key)
    if res is None:
        return default
    try:
        return float(res)
    except TypeError:
      raise exceptions.BadFloat(f'{key}="{res}" not an int')

def get_float_or_none(mapping: Mapping[str, str], key: str) -> float | None:
    if key in mapping:
        return float(mapping.get(key))
    return None


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
    timer: str
    start_time: int
    increments: int
    old_timestamp: float | None
    new_timestamp: float
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
    execute_alert_command: bool = False

    def reset_transient_state(self) -> "State":
        return dataclasses.replace(
            self,
            button=Button.NONE,
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
            start_time=self.time_format.seconds_to_text(self.start_time),
            timer=self.timer,
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
            "elapsed_time": str(self.elapsed_time),
            # This is on purpse, the new timestamp will become
            # the new old.
            "old_timestamp": str(self.new_timestamp),
            "timer_state": self.timer_state.value,
            "timer": self.timer,
        }


def load_state(map_: Mapping, now: float) -> State:
    return State(
        timer=map_.get("timer", "timer"),
        start_time=get_int(map_, "start_time", 300),
        elapsed_time=get_float(map_, "elapsed_time", 0.0),
        old_timestamp=get_float_or_none(map_, "old_timestamp"),
        new_timestamp=now,
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


def increase_elapsed_time_if_running(
    increment: float,
) -> Callable[[State], StateMonad[State]]:
    def _increase_elapsed_time(state: State) -> tuple[Any, State]:
        if state.timer_state == TimerState.RUNNING and state.old_timestamp:
            # this delta should replace "increment", but at the moment
            # we can't until we move to "persistent" interval.
            # delta = state.new_timestamp - state.old_timestamp
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

    return StateMonad(_increase_elapsed_time)


def update_start_time(new_start_time: int) -> Callable[[State], tuple[Any, State]]:
    def _update_start_time(state: State) -> tuple[Any, State]:
        return (None, dataclasses.replace(state, start_time=new_start_time))

    return _update_start_time


def handle_left_click() -> StateMonad[State]:
    def _handle_left_click(state: State) -> tuple[Any, State]:
        if state.button != Button.LEFT:
            return (None, state)
        if state.timer_state == TimerState.RUNNING:
            return (
                None,
                dataclasses.replace(state, timer_state=TimerState.PAUSED),
            )
        return (
            None,
            dataclasses.replace(state, timer_state=TimerState.RUNNING),
        )

    return StateMonad.get().then(lambda _: StateMonad(_handle_left_click))


def handle_right_click() -> StateMonad[State]:
    def _handle_left_click(state: State) -> tuple[Any, State]:
        if state.button != Button.RIGHT:
            return (None, state)
        return (
            None,
            dataclasses.replace(
                state,
                timer_state=TimerState.STOPPED,
                elapsed_time=0,
            ),
        )

    return StateMonad.get().then(lambda _: StateMonad(_handle_left_click))


def handle_scroll_up() -> StateMonad[State]:
    def _handle_scroll_up(state: State) -> tuple[Any, State]:
        if state.button != Button.SCROLL_UP:
            return (None, state)
        return (
            None,
            dataclasses.replace(state, start_time=state.start_time + state.increments),
        )

    return StateMonad.get().then(lambda _: StateMonad(_handle_scroll_up))


def handle_scroll_down() -> StateMonad[State]:
    def _handle_scroll_down(state: State) -> tuple[Any, State]:
        if state.button != Button.SCROLL_DOWN:
            return (None, state)
        return (
            None,
            dataclasses.replace(
                state, start_time=max(state.start_time - state.increments, 0)
            ),
        )

    return StateMonad.get().then(lambda _: StateMonad(_handle_scroll_down))


def handle_middle_click() -> StateMonad[State]:
    def _handle_middle_click(state: State) -> tuple[Any, State]:
        if state.button != Button.MIDDLE or not state.read_input_command:
            return (None, state)
        input = subprocess.check_output(
            state.read_input_command, shell=True, encoding="utf-8"
        )
        input_type, args = input_parser.parse_input(input)
        match input_type:
            case input_parser.InputType.TIME_SET:
                return (
                    None,
                    dataclasses.replace(state, start_time=args[0], elapsed_time=0),
                )
            case input_parser.InputType.TIME_ADDITION:
                return (
                    None,
                    dataclasses.replace(state, start_time=max(state.start_time + args[0], 0)),
                )
            case input_parser.InputType.TIME_REDUCTION:
                return (
                    None,
                    dataclasses.replace(state, start_time=max(state.start_time - args[0], 0)),
                )
            case input_parser.InputType.RENAME_TIMER:
                return (None, dataclasses.replace(state, timer=args[0]))
            case input_parser.InputType.VOID:
                return (None, state)
        raise exceptions.BadValue(f"unrecognized input {input}")

    return StateMonad.get().then(lambda _: StateMonad(_handle_middle_click))
