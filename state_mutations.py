import dataclasses
import subprocess
from typing import Any, Callable
import logging

import exceptions
import input_parser
from monads import StateMonad
import state as state_lib


def handle_clicks(init_state: state_lib.State) -> state_lib.State:
    _, state = (
        StateMonad.get()
        .then(lambda _: handle_middle_click())
        .then(lambda _: handle_right_click())
        .then(lambda _: handle_left_click())
        .then(lambda _: handle_scroll_down())
        .then(lambda _: handle_scroll_up())
    ).run(init_state)

    return state.reset_transient_state()


def handle_increments(init_state: state_lib.State) -> state_lib.State:
    _, state = (
        StateMonad.get()
        .then(lambda _: increase_elapsed_time_if_running())
        .then(lambda _: consume_error_time())
        .run(init_state)
    )

    if state.execute_alert_command:
        subprocess.call(
            state.build_alarm_command(),
            shell=True,
        )

    return state.reset_transient_state()


def add_error(init_state: state_lib.State, e: Exception, now: float) -> state_lib.State:
    def _add_error(state: state_lib.State):
        full_text = str(e)
        short_text = str(e)[:40]
        # generic errors should be displayed for longer
        duration = 7
        if isinstance(e, exceptions.TimerException):
            full_text = getattr(e, "message")
            short_text = full_text[:40]
            # "known" errors can be displayed for shorter
            duration = 5
        return dataclasses.replace(
            state,
            error_message=full_text,
            short_error_message=short_text,
            error_duration=duration,
            new_timestamp=now,
        )

    _, state = (
        StateMonad.get()
        .then(lambda state: StateMonad(lambda _: (None, _add_error(state))))
        .run(init_state)
    )
    return state


def consume_error_time():
    def _consume_error_time(state: state_lib.State) -> tuple[Any, state_lib.State]:
        if state.error_duration is not None and state.old_timestamp is not None:
            delta = state.new_timestamp - state.old_timestamp
            new_error_time = state.error_duration - delta
            if new_error_time > 0:
                return dataclasses.replace(state, error_duration=new_error_time)
            return dataclasses.replace(
                state,
                error_message=None,
                short_error_message=None,
                error_duration=None,
            )

        return state

    return StateMonad.modify(_consume_error_time)


def increase_elapsed_time_if_running() -> (
    Callable[[state_lib.State], StateMonad[state_lib.State]]
):
    def _increase_elapsed_time(state: state_lib.State) -> state_lib.State:
        if state.timer_state == state_lib.TimerState.RUNNING and state.old_timestamp:
            # this delta should replace "increment", but at the moment
            # we can't until we move to "persistent" interval.
            delta = state.new_timestamp - state.old_timestamp
            new_elapsed_time = state.elapsed_time + delta
            execute_alert_command = (
                # before this step, elapsed time had still not
                # reached state.start_time.
                state.elapsed_time < state.start_time
                # by the end of this step, the new elapsed time
                # would have reached the start_time.
                and new_elapsed_time >= state.start_time
            )
            return dataclasses.replace(
                state,
                elapsed_time=new_elapsed_time,
                execute_alert_command=execute_alert_command,
            )

        return state

    return StateMonad.modify(_increase_elapsed_time)


def handle_left_click() -> StateMonad[state_lib.State]:
    def _handle_left_click(state: state_lib.State) -> tuple[Any, state_lib.State]:
        if state.button != state_lib.Button.LEFT:
            return state
        if state.timer_state == state_lib.TimerState.RUNNING:
            return dataclasses.replace(state, timer_state=state_lib.TimerState.PAUSED)

        return dataclasses.replace(state, timer_state=state_lib.TimerState.RUNNING)

    return StateMonad.modify(_handle_left_click)


def handle_right_click() -> StateMonad[state_lib.State]:
    def _handle_left_click(state: state_lib.State) -> tuple[Any, state_lib.State]:
        if state.button != state_lib.Button.RIGHT:
            return state
        return dataclasses.replace(
            state,
            timer_state=state_lib.TimerState.STOPPED,
            elapsed_time=0,
        )

    return StateMonad.modify(_handle_left_click)


def handle_scroll_up() -> StateMonad[state_lib.State]:
    def _handle_scroll_up(state: state_lib.State) -> tuple[Any, state_lib.State]:
        if state.button != state_lib.Button.SCROLL_UP:
            return state
        return (
            dataclasses.replace(state, start_time=state.start_time + state.increments),
        )

    return StateMonad.modify(_handle_scroll_up)


def handle_scroll_down() -> StateMonad[state_lib.State]:
    def _handle_scroll_down(state: state_lib.State) -> tuple[Any, state_lib.State]:
        if state.button != state_lib.Button.SCROLL_DOWN:
            return state
        return dataclasses.replace(
            state, start_time=max(state.start_time - state.increments, 0)
        )

    return StateMonad.modify(_handle_scroll_down)


def handle_middle_click() -> StateMonad[state_lib.State]:
    def _handle_middle_click(state: state_lib.State) -> tuple[Any, state_lib.State]:
        if state.button != state_lib.Button.MIDDLE or not state.read_input_command:
            return state
        input = subprocess.check_output(
            state.build_read_input_command(), shell=True, encoding="utf-8"
        )
        input_type, args = input_parser.parse_input(input)
        match input_type:
            case input_parser.InputType.SET_COLOR_OPTION:
                return dataclasses.replace(state, color_option=args[0])
            case input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY:
                key, value = args
                return dataclasses.replace(state, **{key: value})

            case input_parser.InputType.SET_TEXT_FORMAT:
                [new_text_format] = args
                try:
                    # try the new format before committing a bad format change.
                    state.formatted(new_text_format)
                except Exception as e:
                    logging.error(e)
                    raise e
                return dataclasses.replace(state, text_format=new_text_format)

            case input_parser.InputType.TIME_SET:
                return dataclasses.replace(state, start_time=args[0], elapsed_time=0)

            case input_parser.InputType.TIME_ADDITION:
                return dataclasses.replace(
                    state, start_time=max(state.start_time + args[0], 0)
                )

            case input_parser.InputType.TIME_REDUCTION:
                return dataclasses.replace(
                    state, start_time=max(state.start_time - args[0], 0)
                )
            case input_parser.InputType.RENAME_TIMER:
                return dataclasses.replace(state, timer_name=args[0])
            case input_parser.InputType.VOID:
                return state
        raise exceptions.BadValue(f"unrecognized input {input}")

    return StateMonad.modify(_handle_middle_click)
