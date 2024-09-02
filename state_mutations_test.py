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


if __name__ == '__main__':
    unittest.main()
