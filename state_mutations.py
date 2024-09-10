import dataclasses
import subprocess
from typing import Any, Callable
import logging

import exceptions
import input_parser
from monads import StateMonad
import state as state_lib


_ALARM_CALLER = lambda cmd: subprocess.Popen(cmd, shell=True)
_INPUT_READ_CALLER = lambda cmd: subprocess.check_output(
    cmd, shell=True, encoding='utf-8'
)


def add_new_timestamp(state: state_lib.State, now: float) -> state_lib.State:
    return dataclasses.replace(state, new_timestamp=now)


def handle_increments(init_state: state_lib.State) -> state_lib.State:
    _, state = (
        StateMonad.get()
        .then(lambda _: StateMonad.modify(_increase_elapsed_time_if_running))
        .then(lambda _: StateMonad.modify(_consume_error_time))
        .then(lambda _: StateMonad.modify(_update_old_timestamp))
        .run(init_state)
    )
    if state.execute_alert_command:
        state = _reset_execute_alert_command(state)
        _ALARM_CALLER(state.build_alarm_command())

    if state.execute_read_input_command:
        state = _reset_execute_read_input_command(state)
        try:
            input = _INPUT_READ_CALLER(state.build_read_input_command())
            input_type, args = input_parser.parse_input(input)
            _mutation = _input_intake_mutation(input_type, args)
            state = _mutation(state)
        except Exception as e:
            state = add_error(state, e, state_lib.now())

    return state


def _reset_execute_alert_command(state: state_lib.State) -> state_lib.State:
    return dataclasses.replace(state, execute_alert_command=False)


def _reset_execute_read_input_command(state: state_lib.State) -> state_lib.State:
    return dataclasses.replace(state, execute_read_input_command=False)


def add_error(init_state: state_lib.State, e: Exception, now: float) -> state_lib.State:
    # Since some I/O errors take longer to be generated,
    # refreshing the timestamp is necessary to avoid time-skips or
    # error messages shown for too little.
    def _add_error(state: state_lib.State) -> state_lib.State:
        full_text = str(e)
        short_text = str(e)[:40]
        # generic errors should be displayed for longer
        duration = 7
        if isinstance(e, exceptions.TimerException):
            full_text = getattr(e, 'message')
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

    _, state = StateMonad.modify(_add_error).run(init_state)
    return state


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


def _increase_elapsed_time_if_running(state: state_lib.State) -> state_lib.State:
    if (
        state.timer_state == state_lib.TimerState.RUNNING
        and state.old_timestamp is not None
    ):
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


def _update_old_timestamp(state: state_lib.State) -> state_lib.State:
    if state.new_timestamp is not None:
        return dataclasses.replace(state, old_timestamp=state.new_timestamp)
    return state


def handle_clicks(
    init_state: state_lib.State, button: state_lib.Button
) -> state_lib.State:
    def _on_click(
        expected_button: state_lib.Button,
        mutation: Callable[[state_lib.State], state_lib.State],
    ) -> StateMonad[state_lib.State]:
        def _action(arg):
            if button == expected_button:
                return StateMonad.modify(mutation)
            return StateMonad.get()

        return _action

    _, state = (
        StateMonad.get()
        .then(_on_click(state_lib.Button.MIDDLE, _on_middle_click))
        .then(_on_click(state_lib.Button.RIGHT, _on_right_click))
        .then(_on_click(state_lib.Button.LEFT, _on_left_click))
        .then(_on_click(state_lib.Button.SCROLL_UP, _on_scroll_up))
        .then(_on_click(state_lib.Button.SCROLL_DOWN, _on_scroll_down))
    ).run(init_state)

    return state


def _on_left_click(state: state_lib.State) -> state_lib.State:
    if state.timer_state == state_lib.TimerState.RUNNING:
        return dataclasses.replace(state, timer_state=state_lib.TimerState.PAUSED)
    return dataclasses.replace(state, timer_state=state_lib.TimerState.RUNNING)


def _on_right_click(state: state_lib.State) -> state_lib.State:
    return dataclasses.replace(
        state,
        timer_state=state_lib.TimerState.STOPPED,
        elapsed_time=0,
    )


def _on_scroll_up(state: state_lib.State) -> state_lib.State:
    return dataclasses.replace(state, start_time=state.start_time + state.increments)


def _on_scroll_down(state: state_lib.State) -> state_lib.State:
    return dataclasses.replace(
        state, start_time=max(state.start_time - state.increments, 0)
    )


def _input_intake_mutation(
    input_type: input_parser.InputType, args: list[Any]
) -> Callable[[state_lib.State], state_lib.State]:
    def _mutation(state: state_lib.State) -> state_lib.State:
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
                return dataclasses.replace(state, start_time=args[0])

            case input_parser.InputType.TIME_ADDITION:
                return dataclasses.replace(
                    state, start_time=max(state.start_time + args[0], 0)
                )

            case input_parser.InputType.TIME_REDUCTION:
                return dataclasses.replace(
                    state, start_time=max(state.start_time - args[0], 0)
                )
            case input_parser.InputType.VOID:
                return state
        raise exceptions.BadValue(f'unrecognized input {input}')

    return _mutation


def _on_middle_click(state: state_lib.State) -> state_lib.State:
    if not state.read_input_command:
        return state
    return dataclasses.replace(state, execute_read_input_command=True)
