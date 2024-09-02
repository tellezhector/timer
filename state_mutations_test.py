import unittest


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

        _, later = state_mutations.increase_elapsed_time_if_running().run(init)
        self.assertEqual(1.0, later.elapsed_time)

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

        _, later = state_mutations.increase_elapsed_time_if_running().run(init)
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

        _, later = state_mutations.increase_elapsed_time_if_running().run(init)
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

        _, later = state_mutations.consume_error_time().run(init)
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

        _, later = state_mutations.consume_error_time().run(init)
        self.assertEqual(None, later.error_duration)

    def test_pause_timer_on_left_click_if_running(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
                'button': state.Button.LEFT,
            },
            now=0,
        )

        _, later = state_mutations.handle_left_click().run(init)
        self.assertEqual(state.TimerState.PAUSED, later.timer_state)

    def test_start_timer_on_left_click_if_stopped(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.STOPPED,
                'button': state.Button.LEFT,
            },
            now=0,
        )

        _, later = state_mutations.handle_left_click().run(init)
        self.assertEqual(state.TimerState.RUNNING, later.timer_state)

    def test_start_timer_on_left_click_if_paused(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.STOPPED,
                'button': state.Button.LEFT,
            },
            now=0,
        )

        _, later = state_mutations.handle_left_click().run(init)
        self.assertEqual(state.TimerState.RUNNING, later.timer_state)

    def test_reset_and_stop_timer_on_right_click(self):
        init = state.load_state(
            {
                'timer_state': state.TimerState.RUNNING,
                'start_time': '300',
                'elapsed_time': '240',
                'button': state.Button.RIGHT,
            },
            now=0,
        )
        self.assertEqual(240, init.elapsed_time)

        _, later = state_mutations.handle_right_click().run(init)
        self.assertEqual(state.TimerState.STOPPED, later.timer_state)
        self.assertEqual(300, later.start_time)
        self.assertEqual(0, later.elapsed_time)


if __name__ == '__main__':
    unittest.main()
