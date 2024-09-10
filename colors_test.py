import unittest

import exceptions
import colors



class ColorsTest(unittest.TestCase):
    def test_bad_color_length(self):
        with self.assertRaisesRegex(exceptions.BadColor, 'must have 3 or 6 hex digits.'):
            colors.from_hex('#1234')

    def test_bad_color_digits(self):
        with self.assertRaisesRegex(exceptions.BadColor, 'invalid hex chars'):
            colors.from_hex('#DEFXYZ')

    def test_from_hex(self):
        self.assertEqual((255, 255, 255), colors.from_hex('#FFFFFF').rgb)
        self.assertEqual((255, 255, 255), colors.from_hex('#FFF').rgb)
        self.assertEqual((0,0,0), colors.from_hex('#000000').rgb)
        self.assertEqual((0,0,0), colors.from_hex('#000').rgb)
        self.assertEqual((127, 127, 127), colors.from_hex('#7F7F7F').rgb)

    def test_add_colors(self):
        red = colors.Color(255, 0, 0)
        green = colors.Color(0, 255, 0)
        yellow = colors.Color(255, 255, 0)
        self.assertEqual(yellow, red + green)

    def test_adding_colors_does_not_overflow(self):
        red = colors.Color(255, 0, 0)
        # red+red does not result in Color(510, 0, 0)
        # each primary maxes out at 255.
        self.assertEqual(red, red + red)

    def test_substract_colors(self):
        red = colors.Color(255, 0, 0)
        green = colors.Color(0, 255, 0)
        yellow = colors.Color(255, 255, 0)
        self.assertEqual(red, yellow - green)

    def test_substractig_colors_does_not_overflow(self):
        red = colors.Color(255, 0, 0)
        black = colors.Color(0, 0, 0)
        # black-red does not result in Color(-255, 0, 0)
        # each primary reaches minimum at 0.
        self.assertEqual(black, black - red)

    def test_linear_trajectory_black_to_white(self):
        black = colors.from_hex("#000000")
        gray = colors.from_hex('#7F7F7F')
        white = colors.from_hex("#FFFFFF")
        trajectory = colors.linear_trajectory(2, black, white)

        self.assertEqual(black, trajectory(0))
        self.assertEqual(gray, trajectory(1))
        self.assertEqual(white, trajectory(2))   

    def test_linear_trajectory_white_to_black(self):
        black = colors.from_hex("#000000")
        gray = colors.from_hex('#7F7F7F')
        white = colors.from_hex("#FFFFFF")
        trajectory = colors.linear_trajectory(2, white, black)

        self.assertEqual(white, trajectory(0))
        self.assertEqual(gray, trajectory(1))
        self.assertEqual(black, trajectory(2))    
    
    def test_multi_color_linear_loop_1(self):
        red = colors.from_hex("#FF0000")
        green = colors.from_hex("#00FF00")
        blue = colors.from_hex("#0000FF")
        trajectory = colors.multi_color_linear_loop(2, [red, green, blue])

        self.assertEqual(red, trajectory(0))
        self.assertEqual(colors.from_hex('#7F7F00'), trajectory(1))
        self.assertEqual(green, trajectory(2))
        self.assertEqual(colors.from_hex('#007F7F'), trajectory(3))
        self.assertEqual(blue, trajectory(4))
        self.assertEqual(colors.from_hex('#7F007F'), trajectory(5))
        self.assertEqual(red, trajectory(6))
    
    def test_multi_color_linear_loop_2(self):
        black = colors.from_hex("#000000")
        gray = colors.from_hex('#7F7F7F')
        white = colors.from_hex("#FFFFFF")

        trajectory = colors.multi_color_linear_loop(2, [black, white])

        self.assertEqual(black, trajectory(0))
        self.assertEqual(gray, trajectory(1))
        self.assertEqual(white, trajectory(2))
        self.assertEqual(gray, trajectory(3))
        self.assertEqual(black, trajectory(4))
        self.assertEqual(gray, trajectory(5))
        self.assertEqual(white, trajectory(6))

if __name__ == '__main__':
    unittest.main()
