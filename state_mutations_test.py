import unittest


import state
import state_mutations


class StateMutationsTest(unittest.TestCase):
    def test_increase_elapsed_time_if_running(self):
        init = state.load_state(
            {'timer_state': state.TimerState.RUNNING, 'old_timestamp': 0}, 
            now=1
        )
        self.assertEqual(1.0, init.new_timestamp)
        self.assertEqual(0.0, init.old_timestamp)

        _, later = state_mutations.increase_elapsed_time_if_running().run(init)
        self.assertEqual(state.TimerState.RUNNING, later.timer_state)
        self.assertEqual(1.0, later.elapsed_time)


if __name__ == '__main__':
    unittest.main()
