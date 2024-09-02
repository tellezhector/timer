import unittest

import input_parser
import colors
import exceptions

class InputParserTest(unittest.TestCase):
    def test_time_addition_pretty_format(self):
        input_type, [seconds] = input_parser.parse_input('+3m')

        self.assertEqual(input_parser.InputType.TIME_ADDITION, input_type)
        self.assertEqual(180, seconds)

    def test_time_addition_clock_format(self):
        input_type, [seconds] = input_parser.parse_input('+3:00')

        self.assertEqual(input_parser.InputType.TIME_ADDITION, input_type)
        self.assertEqual(180, seconds)

    def test_time_addition_naked_format(self):
        input_type, [seconds] = input_parser.parse_input('+180')

        self.assertEqual(input_parser.InputType.TIME_ADDITION, input_type)
        self.assertEqual(180, seconds)

    def test_time_reduction_pretty_format(self):
        input_type, [seconds] = input_parser.parse_input('-3m')

        self.assertEqual(input_parser.InputType.TIME_REDUCTION, input_type)
        self.assertEqual(180, seconds)

    def test_time_reduction_clock_format(self):
        input_type, [seconds] = input_parser.parse_input('-3:00')

        self.assertEqual(input_parser.InputType.TIME_REDUCTION, input_type)
        self.assertEqual(180, seconds)

    def test_time_reduction_naked_format(self):
        input_type, [seconds] = input_parser.parse_input('-180')

        self.assertEqual(input_parser.InputType.TIME_REDUCTION, input_type)
        self.assertEqual(180, seconds)

    def test_set_time_pretty_format(self):
        input_type, [seconds] = input_parser.parse_input('5m')

        self.assertEqual(input_parser.InputType.TIME_SET, input_type)
        self.assertEqual(300, seconds)

    def test_set_time_clock_format(self):
        input_type, [seconds] = input_parser.parse_input('5:00')

        self.assertEqual(input_parser.InputType.TIME_SET, input_type)
        self.assertEqual(300, seconds)

    def test_set_time_naked_format(self):
        input_type, [seconds] = input_parser.parse_input('300')

        self.assertEqual(input_parser.InputType.TIME_SET, input_type)
        self.assertEqual(300, seconds)

    def test_set_color_option(self):
        input_type, [color] = input_parser.parse_input('color_option=red_on_negatives')

        self.assertEqual(input_parser.InputType.SET_COLOR_OPTION, input_type)
        self.assertEqual(colors.ColorOption.RED_ON_NEGATIVES, color)

    def test_set_timer_name(self):
        input_type, [key, value] = input_parser.parse_input('timer_name=whatever')

        self.assertEqual(input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY, input_type)
        self.assertEqual('timer_name', key)
        self.assertEqual('whatever', value)

    def test_set_font(self):
        input_type, [key, value] = input_parser.parse_input('font=whatever')

        self.assertEqual(input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY, input_type)
        self.assertEqual('font', key)
        self.assertEqual('whatever', value)

    def test_set_alarm_command(self):
        input_type, [key, value] = input_parser.parse_input('alarm_command=whatever')

        self.assertEqual(input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY, input_type)
        self.assertEqual('alarm_command', key)
        self.assertEqual('whatever', value)

    def test_set_read_input_command(self):
        input_type, [key, value] = input_parser.parse_input('read_input_command=whatever')

        self.assertEqual(input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY, input_type)
        self.assertEqual('read_input_command', key)
        self.assertEqual('whatever', value)

    def test_set_running_label(self):
        input_type, [key, value] = input_parser.parse_input('running_label=whatever')

        self.assertEqual(input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY, input_type)
        self.assertEqual('running_label', key)
        self.assertEqual('whatever', value)

    def test_set_stopped_label(self):
        input_type, [key, value] = input_parser.parse_input('stopped_label=whatever')

        self.assertEqual(input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY, input_type)
        self.assertEqual('stopped_label', key)
        self.assertEqual('whatever', value)

    def test_set_paused_label(self):
        input_type, [key, value] = input_parser.parse_input('paused_label=whatever')

        self.assertEqual(input_parser.InputType.SET_GENERIC_FREE_TEXT_PROPERTY, input_type)
        self.assertEqual('paused_label', key)
        self.assertEqual('whatever', value)

    def test_set_text_format(self):
        input_type, [value] = input_parser.parse_input('text_format={elapsed_time}')

        self.assertEqual(input_parser.InputType.SET_TEXT_FORMAT, input_type)
        self.assertEqual('{elapsed_time}', value)

    def test_unknown_property(self):
        with self.assertRaisesRegex(exceptions.BadPropertyPattern, 'unknown property'): 
            input_parser.parse_input('something_non_existent=¯\_(ツ)_/¯')
    
    def test_bad_input(self):
        with self.assertRaisesRegex(exceptions.BadValue, 'invalid input'): 
            input_parser.parse_input('¯\_(ツ)_/¯')

    



if __name__ == '__main__':
    unittest.main()