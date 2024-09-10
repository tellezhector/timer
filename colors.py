import enum
import random
from typing import Callable

import exceptions


class Color:
    def __init__(self, r: int, g: int, b: int) -> None:
        self.hex = f'#{r:02x}{g:02x}{b:02x}'.upper()
        if r < 0 or r > 255:
            raise exceptions.BadColor(f'{r=} is out of range [0, 255]')
        self.r = r
        if g < 0 or g > 255:
            raise exceptions.BadColor(f'{g=} is out of range [0, 255]')
        self.g = g
        if b < 0 or b > 255:
            raise exceptions.BadColor(f'{b=} is out of range [0, 255]')
        self.b = b
        self.rgb = (r, g, b)

    def __add__(self, other: 'Color') -> 'Color':
        return Color(
            min(self.r + other.r, 255),
            min(self.g + other.g, 255),
            min(self.b + other.b, 255),
        )

    def __sub__(self, other: 'Color') -> 'Color':
        return Color(
            max(self.r - other.r, 0),
            max(self.g - other.g, 0),
            max(self.b - other.b, 0),
        )

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Color):
            return False
        return self.rgb == value.rgb

    def __str__(self) -> str:
        return f'<Color({self.r}, {self.g}, {self.b}) {self.hex}>'

    def __repr__(self) -> str:
        return f'<Color({self.r}, {self.g}, {self.b}) {self.hex}>'


def from_hex(hex: str) -> 'Color':
    if not hex.startswith('#'):
        raise exceptions.BadColor(f'{hex} should start with #')
    standard_hex = hex[1:].upper()
    bad_chars = []
    for h in standard_hex:
        if h not in '0123456789ABCDEF':
            bad_chars.append(h)
    if bad_chars:
        raise exceptions.BadColor(f'invalid hex chars {"".join(bad_chars)}')
    if len(standard_hex) == 3:
        return Color(
            int(standard_hex[0] * 2, 16),
            int(standard_hex[1] * 2, 16),
            int(standard_hex[2] * 2, 16),
        )
    if len(standard_hex) == 6:
        return Color(
            int(standard_hex[0:2], 16),
            int(standard_hex[2:4], 16),
            int(standard_hex[4:6], 16),
        )
    raise exceptions.BadColor(f'{hex} must have 3 or 6 hex digits.')


def to_color_range(f: float) -> int:
    x = int(f)
    x = x % (510)
    if x <= 255:
        return x
    return 510 - x


def linear_trajectory(steps: int, start: Color, end: Color) -> Callable[[int], Color]:
    """A trajectory passing through different colors and looping back.

    Args:
      steps: The number of steps to go from one color to the next.
      start: The first color in the trajectory (trajectory(0))
      end:   The last color in the trajectory  (trajectory(steps))

    trajectory = linear_trajectory(2, color_1, color_2):

    trajectory(0) == color_1
    trajectory(1) == average of color_1 and color 2
    trajectory(2) == color_2
    """
    r = lambda i: to_color_range((i * (end.r - start.r) / (steps)) + start.r)
    g = lambda i: to_color_range((i * (end.g - start.g) / (steps)) + start.g)
    b = lambda i: to_color_range((i * (end.b - start.b) / (steps)) + start.b)
    return lambda i: Color(r(i), g(i), b(i))


def multi_color_linear_loop(steps, colors: list[Color]) -> Callable[[int], Color]:
    """A trajectory passing through different colors and looping back.

    trajectory = multi_color_linear_loop(2, [color_1, color_2, color_3]):

    trajectory(0) == color_1
    trajectory(1) == average of color_1 and color 2
    trajectory(2) == color_2
    trajectory(3) == average of color 2 and color 3
    trajectory(4) == color_3
    trajectory(5) == average of color 3 and color_1
    trajectory(6) == color_1
    """
    total_colors = len(colors)
    pairs = [(colors[i], colors[(i + 1) % total_colors]) for i in range(total_colors)]
    trajectories = [linear_trajectory(steps, start, end) for start, end in pairs]
    total_steps = steps * total_colors

    def _trajectory(i):
        normalized_i = i % total_steps
        bucket = normalized_i // steps
        new_i = normalized_i % steps
        return trajectories[bucket](new_i)

    return _trajectory


WHITE = from_hex('#FFFFFF')
NICE_RED = from_hex('#BB0A21')
XANTHOUS = from_hex('#FFBC42')
MOONSTONE = from_hex('#5EB1BF')
HOT_PINK = from_hex('#F564A9')
SPRING_GREEN = from_hex('#04F06A')

COLORS = [
    NICE_RED,
    XANTHOUS,  # Xanthous (yellow)
    MOONSTONE,  # Moonstone (light blue)
    HOT_PINK,  # Hot pink
    SPRING_GREEN,  # Spring green
]

PULSATING_GREEN = multi_color_linear_loop(
    100,
    [
        from_hex('#78BC61'),  # mantis
        from_hex('#78BC61'),  # mantis
        from_hex('#FFFFFF'),  # white
        from_hex('#3F6A30'),  # fern green
        from_hex('#3F6A30'),  # fern green
    ],
)

PULSATING_YELLOW = multi_color_linear_loop(
    100,
    [
        from_hex('#F5D547'),  # naples yellow
        from_hex('#C0C781'),  # sage
        from_hex('#E2F89C'),  # mindaro
    ],
)

PULSATING_RED = multi_color_linear_loop(
    100,
    [
        from_hex('#EE4266'),  # crayol
        from_hex('#ED1C24'),  # cmyk
        from_hex('#A50104'),  # white
        from_hex('#BB0A21'),  # nice red
        from_hex('#650D1B'),  # chocolate cosmos
    ],
)


@enum.unique
class ColorOption(enum.Enum):
    NEVER = "never"
    COLORFUL = "colorful"
    COLORFUL_ON_NEGATIVES = "colorful_on_negatives"
    PULSATING_TRAFFIC_LIGHT = "pulsating_traffic_light"
    RED_ON_NEGATIVES = "red_on_negatives"


def red(text: str) -> str:
    return f"<span color='{NICE_RED.hex}'>{text}</span>"


def colorize(text: str) -> str:
    result = ""
    pango_stack = 0
    for c in text:
        if c == "<":
            pango_stack += 1
            result += c
            continue
        if c == ">":
            pango_stack -= 1
            result += c
            continue
        if pango_stack == 0:
            result += f"<span color='{random.choice(COLORS).hex}'>{c}</span>"
        else:
            result += c
    return result
