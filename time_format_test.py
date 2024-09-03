import unittest

import time_format


class FormatterTest(unittest.TestCase):

    def test_seconds_to_pretty_format(self):
        cases = [
            (300, '5m'),
            (301, '5m1s'),
            (299, '4m59s'),
            (3600, '1h'),
            (3600 * 24, '24h'),
            (3661, '1h1m1s'),
            (3601, '1h1s'),
        ]
        for secs, expected in cases:
            with self.subTest(expected, secs=secs, expected=expected):
                self.assertEqual(expected, time_format.seconds_to_pretty_time(secs))

    def test_seconds_to_clock_format(self):
        cases = [
            (300, '05:00'),
            (301, '05:01'),
            (299, '04:59'),
            (3600, '1:00:00'),
            (3600 * 24, '24:00:00'),
            (3661, '1:01:01'),
            (3601, '1:00:01'),
        ]
        for secs, expected in cases:
            with self.subTest(expected, secs=secs, expected=expected):
                self.assertEqual(expected, time_format.seconds_to_clock_format(secs))
        self.assertEqual('05:00', time_format.seconds_to_clock_format(300))
        self.assertEqual('05:01', time_format.seconds_to_clock_format(301))
        self.assertEqual('04:59', time_format.seconds_to_clock_format(299))
        self.assertEqual('1:00:00', time_format.seconds_to_clock_format(3600))
        self.assertEqual('24:00:00', time_format.seconds_to_clock_format(24 * 3600))
        self.assertEqual('1:00:01', time_format.seconds_to_clock_format(3601))
        self.assertEqual('1:01:01', time_format.seconds_to_clock_format(3661))

    def test_format_pretty(self):
        format = time_format.FORMATTER.format
        cases = [
            (300, '5m'),
            (301, '5m1s'),
            (299, '4m59s'),
            (3600, '1h'),
            (3600 * 24, '24h'),
            (3661, '1h1m1s'),
            (3601, '1h1s'),
        ]
        for secs, expected in cases:
            with self.subTest(expected, secs=secs, expected=expected):
                self.assertEqual(expected, format('{time:pretty}', time=secs))

    def test_format_pretty(self):
        format = time_format.FORMATTER.format
        cases = [
            (300, '05:00'),
            (301, '05:01'),
            (299, '04:59'),
            (3600, '1:00:00'),
            (3600 * 24, '24:00:00'),
            (3661, '1:01:01'),
            (3601, '1:00:01'),
        ]
        for secs, expected in cases:
            with self.subTest(expected, secs=secs, expected=expected):
                self.assertEqual(expected, format('{time:clock}', time=secs))


if __name__ == '__main__':
    unittest.main()
