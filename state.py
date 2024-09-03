from collections.abc import Mapping
import dataclasses
import enum
from typing import Any
import datetime
import logging

import colors
import exceptions
import time_format


@enum.unique
class Button(enum.Enum):
    NONE = None
    LEFT = '1'
    MIDDLE = '2'
    RIGHT = '3'
    SCROLL_UP = '4'
    SCROLL_DOWN = '5'


@enum.unique
class TimerState(enum.Enum):
    STOPPED = 'stopped'
    RUNNING = 'running'
    PAUSED = 'paused'


def now():
    return datetime.datetime.now(tz=datetime.timezone.utc).timestamp()


def get_int(mapping: Mapping[str, Any], key: str, default: int) -> int:
    res = mapping.get(key)
    if res is None:
        return default
    try:
        return int(res)
    except (TypeError, ValueError):
      raise exceptions.BadInteger(f"{key}='{res}' not an int")


def get_float(mapping: Mapping[str, Any], key: str, default: float) -> float:
    res = mapping.get(key)
    if res is None:
        return default
    try:
        return float(res)
    except (TypeError, ValueError):
        raise exceptions.BadFloat(f"{key}='{res}' not a float")


def get_float_or_none(mapping: Mapping[str, Any], key: str) -> float | None:
    return get_float(mapping, key, None)


def get_enum(
    mapping: Mapping[str, Any], key: str, default: enum.Enum | None
) -> enum.Enum:
    if default is None:
        raise exceptions.BadEnum(f'default for key {key} is None')
    raw = mapping.get(key)
    if raw is None:
        return default
    enum_type = type(default)
    try:
        return enum_type(raw)
    except ValueError:
        raise exceptions.BadEnum(f"'{raw}' is not a {enum_type.__name__}")


@dataclasses.dataclass(frozen=True)
class State:
    text_format: str
    timer_name: str
    start_time: int
    increments: int
    button: Button
    color_option: colors.ColorOption
    alarm_command: str | None
    read_input_command: str | None
    running_label: str
    stopped_label: str
    paused_label: str

    # internal control - not modifiable through configuration
    elapsed_time: float
    timer_state: TimerState
    old_timestamp: float | None
    new_timestamp: float | None = None
    execute_alert_command: bool = False
    error_message: str | None = None
    short_error_message: str | None = None
    error_duration: float | None = None

    def reset_transient_state(self) -> 'State':
        res = dataclasses.replace(
            self,
            button=Button.NONE,
            execute_alert_command=False,
        )
        return res

    def label(self) -> str:
        match self.timer_state:
            case TimerState.RUNNING:
                return self.running_label
            case TimerState.PAUSED:
                return self.paused_label
            case TimerState.STOPPED:
                return self.stopped_label

    def build_alarm_command(self) -> str:
        return self.formatted(self.alarm_command)

    def build_read_input_command(self) -> str:
        return self.formatted(self.read_input_command)

    def formatted(self, text) -> str:
        remaining_time = self.start_time - self.elapsed_time
        try:
            return time_format.FORMATTER.format(
                text,
                timer_name=self.timer_name,
                start_time=self.start_time,
                elapsed_time=self.elapsed_time,
                remaining_time=remaining_time,
            )
        except KeyError as e:
            raise exceptions.BadFormat(f'Bad key {e}')
        except SyntaxError as e:
            raise exceptions.BadFormat(f'Bad syntax in {text}')

    def full_text(self) -> str:
        remaining_time = self.start_time - self.elapsed_time
        text = self.formatted(self.text_format)

        match self.color_option:
            case colors.ColorOption.COLORFUL:
                text = colors.colorize(text)
            case colors.ColorOption.RED_ON_NEGATIVES:
                if remaining_time < 0:
                    text = colors.red(text)
            case colors.ColorOption.COLORFUL_ON_NEGATIVES:
                if remaining_time < 0:
                    text = colors.colorize(text)
            case colors.ColorOption.NEVER:
                pass
        return text

    def serializable(self) -> dict[str, Any]:
        res = {
            'label': self.label(),
            'start_time': self.start_time,
            'elapsed_time': str(self.elapsed_time),
            'timer_state': self.timer_state.value,
            'timer_name': self.timer_name,
            'text_format': self.text_format,
            'alarm_command': self.alarm_command,
            'read_input_command': self.read_input_command,
            'running_label': self.running_label,
            'stopped_label': self.stopped_label,
            'paused_label': self.paused_label,
        }

        if self.new_timestamp is not None:
            res.update(
                {
                    # This is on purpse, the new timestamp will become
                    # the new old timestamp
                    'old_timestamp': str(self.new_timestamp),
                }
            )

        if self.error_duration is None:
            full_text = self.full_text()
            res.update(
                {
                    'full_text': full_text,
                    'short_text': full_text,
                }
            )
        else:
            res.update(
                {
                    'full_text': f'{self.error_message}({self.error_duration:.1f})',
                    'short_text': self.short_error_message,
                    'color': '#ffffff',
                    'background': '#ff0000',
                    'error_message': self.error_message,
                    'short_error_message': self.short_error_message,
                    'error_duration': str(self.error_duration),
                }
            )

        return res


def load_state(mapping: Mapping, now: float) -> State:
    state = State(
        text_format=mapping.get('text_format', '{remaining_time:pretty}'),
        timer_name=mapping.get('timer_name', 'timer'),
        start_time=get_int(mapping, 'start_time', 300),
        elapsed_time=get_float(mapping, 'elapsed_time', 0.0),
        old_timestamp=get_float_or_none(mapping, 'old_timestamp'),
        new_timestamp=now,
        increments=get_int(mapping, 'increments', 60),
        timer_state=get_enum(mapping, 'timer_state', TimerState.STOPPED),
        button=get_enum(mapping, 'button', Button.NONE),
        color_option=get_enum(mapping, 'colorize', colors.ColorOption.NEVER),
        alarm_command=mapping.get('alarm_command'),
        read_input_command=mapping.get('read_input_command'),
        running_label=mapping.get('running_label', 'running:'),
        stopped_label=mapping.get('stopped_label', 'timer:'),
        paused_label=mapping.get('paused_label', 'paused:'),
        error_message=mapping.get('error_message'),
        short_error_message=mapping.get('short_error_message'),
        error_duration=get_float_or_none(mapping, 'error_duration'),
    )
    return state
