import unittest
import enum

import exceptions
import state


@enum.unique
class TestEnum(enum.Enum):
    NADA = 'nada'
    UNO = 'uno'
    DOS = 'dos'


class StateTest(unittest.TestCase):
    def test_get_float(self):
        self.assertEqual(1.1, state.get_float({'key': '1.1'}, 'key', 42.0))
        self.assertEqual(1.1, state.get_float({'key': 1.1}, 'key', 42.0))

    def test_get_default_float(self):
        self.assertEqual(42.0, state.get_float({}, 'key', 42.0))

    def test_get_bad_float(self):
        with self.assertRaises(exceptions.BadFloat):
            state.get_float({'key': 'not_a_float'}, 'key', 42.0)

    def test_get_float_or_none_with_existing_value(self):
        self.assertEqual(1.1, state.get_float_or_none({'key': '1.1'}, 'key'))
        self.assertEqual(1.1, state.get_float_or_none({'key': 1.1}, 'key'))

    def test_get_float_or_none_with_non_existing_value(self):
        self.assertIsNone(state.get_float_or_none({}, 'key'))

    def test_get_float_or_none_bad_float(self):
        with self.assertRaises(exceptions.BadFloat):
            state.get_float_or_none({'key': 'not_a_float'}, 'key')

    def test_get_int(self):
        self.assertEqual(1, state.get_int({'key': '1'}, 'key', 42))
        self.assertEqual(1, state.get_int({'key': 1}, 'key', 42))

    def test_get_default_int(self):
        self.assertEqual(42, state.get_int({}, 'key', 42))

    def test_get_bad_int(self):
        with self.assertRaises(exceptions.BadInteger):
            state.get_int({'key': 'not_an_int'}, 'key', 42.0)

    def test_get_enum(self):
        self.assertEqual(
            TestEnum.UNO, state.get_enum({'key': 'uno'}, 'key', TestEnum.NADA)
        )
        self.assertEqual(
            TestEnum.UNO, state.get_enum({'key': TestEnum.UNO}, 'key', TestEnum.NADA)
        )

    def test_get_default_enum(self):
        self.assertEqual(TestEnum.NADA, state.get_enum({}, 'key', TestEnum.NADA))

    def test_get_bad_enum(self):
        with self.assertRaises(exceptions.BadEnum):
            state.get_enum({'key': 'not_an_enum'}, 'key', TestEnum.NADA)

    def test_new_timestamp_becomes_old_timestamp_on_serialization(self):
        init = state.load_state(mapping={'old_timestamp': 1}, now=3)

        serializable = init.serializable()

        self.assertEqual('3', serializable['old_timestamp'])


if __name__ == '__main__':
    unittest.main()
