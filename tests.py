#!/usr/bin/env python3

import unittest

if __name__ == '__main__':
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=1, warnings='always')
    runner.run(
        loader.discover(
            start_dir='.',
            pattern='*test.py',
        )
    )
