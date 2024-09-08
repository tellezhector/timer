import unittest

import exceptions
import state
import state_mutations


class StateMutationsTest(unittest.TestCase):
    def test_increase_elapsed_time_if_running(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
                'old_timestamp': 0,
            },
            now=1,
        )
        self.assertEqual(1.0, init.new_timestamp)
        self.assertEqual(0.0, init.old_timestamp)

        later = state_mutations._increase_elapsed_time_if_running(init)
        self.assertEqual(1.0, later.elapsed_time)

    def test_trigger_alarm_cmd_when_start_time_is_crossed_over(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
                'start_time': 300,
                'elapsed_time': 299,
                'old_timestamp': 0,
            },
            now=2,
        )

        later = state_mutations._increase_elapsed_time_if_running(init)
        self.assertTrue(later.execute_alert_command)

    def test_trigger_alarm_cmd_when_start_time_is_just_reached(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
                'start_time': 300,
                'elapsed_time': 299,
                'old_timestamp': 0,
            },
            now=1,
        )

        later = state_mutations._increase_elapsed_time_if_running(init)
        self.assertTrue(later.execute_alert_command)

    def test_do_not_trigger_alarm_cmd_when_start_time_was_already_reached(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
                'start_time': 300,
                'elapsed_time': 300,
                'old_timestamp': 0,
            },
            now=1,
        )

        later = state_mutations._increase_elapsed_time_if_running(init)
        self.assertFalse(later.execute_alert_command)

    def test_do_not_increase_elapsed_time_if_stopped(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.STOPPED,
                'old_timestamp': 0,
            },
            now=1,
        )
        self.assertEqual(1.0, init.new_timestamp)
        self.assertEqual(0.0, init.old_timestamp)

        later = state_mutations._increase_elapsed_time_if_running(init)
        self.assertEqual(0.0, later.elapsed_time)

    def test_do_not_increase_elapsed_time_if_paused(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.PAUSED,
                'old_timestamp': 0,
            },
            now=1,
        )
        self.assertEqual(1.0, init.new_timestamp)
        self.assertEqual(0.0, init.old_timestamp)

        later = state_mutations._increase_elapsed_time_if_running(init)
        self.assertEqual(0.0, later.elapsed_time)

    def test_consume_error_time_if_there_is_error_duration(self):
        init = state.load_state(
            {
                'old_timestamp': 0,
                'error_duration': 4,
            },
            now=1,
        )
        self.assertEqual(1.0, init.new_timestamp)
        self.assertEqual(0.0, init.old_timestamp)
        self.assertEqual(4.0, init.error_duration)

        later = state_mutations._consume_error_time(init)
        self.assertEqual(3.0, later.error_duration)

    def test_do_not_consume_error_time_if_there_is_no_error_duration(self):
        init = state.load_state(
            {
                'old_timestamp': 0,
            },
            now=1,
        )
        self.assertEqual(1.0, init.new_timestamp)
        self.assertEqual(0.0, init.old_timestamp)

        later = state_mutations._consume_error_time(init)
        self.assertEqual(None, later.error_duration)

    def test_pause_timer_on_left_click_if_running(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
            },
            now=0,
        )

        later = state_mutations._on_left_click(init)
        self.assertEqual(state.TimerState.PAUSED, later.timer_state)

    def test_start_timer_on_left_click_if_stopped(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.STOPPED,
            },
            now=0,
        )

        later = state_mutations._on_left_click(init)
        self.assertEqual(state.TimerState.RUNNING, later.timer_state)

    def test_start_timer_on_left_click_if_paused(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.STOPPED,
            },
            now=0,
        )

        later = state_mutations._on_left_click(init)
        self.assertEqual(state.TimerState.RUNNING, later.timer_state)

    def test_reset_and_stop_timer_on_right_click(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
                'start_time': '300',
                'elapsed_time': '240',
            },
            now=0,
        )
        self.assertEqual(240, init.elapsed_time)

        later = state_mutations._on_right_click(init)
        self.assertEqual(state.TimerState.STOPPED, later.timer_state)
        self.assertEqual(300, later.start_time)
        self.assertEqual(0, later.elapsed_time)

    def test_add_generic_error(self):
        init = state.load_state(mapping={}, now=0)
        some_error = ValueError('some value error')

        later = state_mutations.add_error(init, some_error, 2)

        self.assertEqual('some value error', later.error_message)
        self.assertEqual(7, later.error_duration)
        self.assertEqual(2, later.new_timestamp)

    def test_add_timer_error(self):
        init = state.load_state(mapping={}, now=0)
        some_error = exceptions.TimerException('some timer error')

        later = state_mutations.add_error(init, some_error, 2)

        self.assertEqual('some timer error', later.error_message)
        self.assertEqual(5, later.error_duration)
        self.assertEqual(2, later.new_timestamp)

    def test_new_timestamp_becomes_old_timestamp_on_serialization(self):
        init = state.load_state(mapping={'old_timestamp': 1}, now=3)

        later = state_mutations._move_new_timestamp_to_old_timestamp(init)

        self.assertEqual(3, later.old_timestamp)

    def test_middle_click_input_intake(self):
        user_input = None  # to be defined during test

        def _inputs(unused_arg):
            return user_input

        state_mutations._INPUT_READ_CALLER = _inputs
        init = state.load_state(
            mapping={
                'read_input_command': 'whatever',
                'timer_state': state.TimerState.RUNNING,
            },
            now=0,
        )

        # press middle_click and set name
        user_input = 'timer_name=new_name'
        later = state_mutations._on_middle_click(init)
        self.assertEqual('new_name', later.timer_name)

        # press middle click again
        user_input = '1h'
        later = state_mutations._on_middle_click(later)
        self.assertEqual('new_name', later.timer_name)
        self.assertEqual(3600, later.start_time)

        # press middle click again
        user_input = '-10m'
        later = state_mutations._on_middle_click(later)
        self.assertEqual('new_name', later.timer_name)
        self.assertEqual(3000, later.start_time)

        # assert time doesn't pass during click events
        self.assertEqual(0, later.elapsed_time)


if __name__ == '__main__':
    unittest.main()
