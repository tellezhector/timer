import enum
import random
import math
from typing import Callable

import exceptions


class Color:
    def __init__(self, r: int, g: int, b: int, name: str = None) -> None:
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
        self.name = name

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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return False
        return self.rgb == other.rgb

    def dist(self, other) -> float:
        return math.sqrt(
            (self.r - other.r) ** 2 + (self.g - other.g) ** 2 + (self.b - other.b) ** 2
        )

    def whiteness(self) -> float:
        return self.dist(BLACK)

    def __str__(self) -> str:
        return f'<Color({self.r}, {self.g}, {self.b}) {self.hex}>'

    def __repr__(self) -> str:
        return f'<Color({self.r}, {self.g}, {self.b}) {self.hex}>'


def from_hex(hex: str, name: str = None) -> 'Color':
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
            name=name,
        )
    if len(standard_hex) == 6:
        return Color(
            int(standard_hex[0:2], 16),
            int(standard_hex[2:4], 16),
            int(standard_hex[4:6], 16),
            name=name,
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


WHITE = from_hex('#FFFFFF', 'WHITE')
BLACK = from_hex('#000000', 'BLACK')
NICE_RED = from_hex('#BB0A21', 'NICE RED')
XANTHOUS = from_hex('#FFBC42', 'XANTHOUS')
MOONSTONE = from_hex('#5EB1BF', 'MOONSTONE')
HOT_PINK = from_hex('#F564A9', 'HOT PINK')
SPRING_GREEN = from_hex('#04F06A', 'SPRING GREEN')

GREENS = [
    from_hex('#043927', 'SACRAMENTO'),
    from_hex('#4B5320', 'ARMY'),
    from_hex('#3F6A30', 'FERN GREEN'),
    from_hex('#3F704D', 'HUNTER'),
    from_hex('#4F7942', 'FERN'),
    from_hex('#01796F', 'PINE'),
    from_hex('#2E8B57', 'SEA'),
    from_hex('#708238', 'OLIVE'),
    from_hex('#00A86B', 'JADE'),
    from_hex('#4CBB17', 'KELLY'),
    from_hex('#29AB87', 'JUNGLE'),
    from_hex('#8A9A5B', 'MOSS'),
    from_hex('#8F9779', 'ARTICHOKE'),
    from_hex('#78BC61', 'MANTIS'),
    from_hex('#50C878', 'EMERALD'),
    from_hex('#9DC183', 'SAGE'),
    from_hex('#A9BA9D', 'LAUREL'),
    from_hex('#C7EA46', 'LIME'),
    from_hex('#98FB98', 'MINT'),
    from_hex('#D0F0C0', 'TEA'),
    from_hex('#FFFFFF', 'WHITE'),
]

PULSATING_GREEN = multi_color_linear_loop(
    100,
    # [-2:0:-1] means:
    # start at -2 (second to last)
    # stop at 0 (without including 0)
    # advance in steps of size -1
    GREENS + GREENS[-2:0:-1],
)

YELLOWS = [
    from_hex('#D2B55B', 'TROMBONE'),
    from_hex('#D5B85A', 'FLAXEN'),
    from_hex('#CEB180', 'ECRU'),
    from_hex('#C0C781', 'SAGE'),
    from_hex('#E4CD05', 'CORN'),
    from_hex('#E3B778', 'SEPIA'),
    from_hex('#FCD12A', 'TUSCANY YELLOW'),
    from_hex('#FFD300', 'CYBER YELLOW'),
    from_hex('#F5D547', 'NAPLES YELLOW'),
    from_hex('#FCE205', 'BUMBLEBEE'),
    from_hex('#FEE12B', 'PINEAPPLE YELLOW'),
    from_hex('#FADA5E', 'ROYAL YELLOW'),
    from_hex('#FEDC56', 'MUSTARD YELLOW'),
    from_hex('#EEDC82', 'FLAX'),
    from_hex('#FFF200', 'BRIGHT YELLOW'),
    from_hex('#F8DE7E', 'MELLOW YELLOW'),
    from_hex('#F8E473', 'LAGUNA YELLOW'),
    from_hex('#EFFD5F', 'LEMON YELLOW'),
    from_hex('#E2F89C', 'MINDARO'),
    from_hex('#F9E29C', 'EGG NOG'),
    from_hex('#FCF4A3', 'BANANA YELLOW'),
    from_hex('#FFE5B4', 'PEACH'),
    from_hex('#FFFDD0', 'CREAM'),
]

PULSATING_YELLOW = multi_color_linear_loop(
    100,
    # [-2:0:-1] means:
    # start at -2 (second to last)
    # stop at 0 (without including 0)
    # advance in steps of size -1
    YELLOWS + YELLOWS[-2:0:-1],
)

REDS = [
    from_hex('#590004', 'ROSEWOOD'),
    from_hex('#420D09', 'MAHOGANY'),
    from_hex('#5E1914', 'SANGRIA'),
    from_hex('#650D1B', 'CHOCOLATE COSMOS'),
    from_hex('#7C0A02', 'BARN RED'),
    from_hex('#800000', 'MAROON'),
    from_hex('#8D021F', 'BURGUNDY'),
    from_hex('#960019', 'CARMINE'),
    from_hex('#A50104', 'TURKEY RED'),
    from_hex('#B22222', 'FIRE BRICK'),
    from_hex('#B80F0A', 'CRIMSON RED'),
    from_hex('#BB0A21', 'NICE RED'),
    from_hex('#C21807', 'CHILI RED'),
    from_hex('#BF0A30', 'U.S. FLAG'),
    from_hex('#A45A52', 'REDWOOD'),
    from_hex('#D30000', 'RED'),
    from_hex('#CA3433', 'PERSIAN RED'),
    from_hex('#D21F3C', 'RASPBERRY'),
    from_hex('#ED1C24', 'CMYK'),
    from_hex('#CD5C5C', 'INDIAN RED'),
    from_hex('#ED2939', 'IMPERIAL RED'),
    from_hex('#FF0800', 'CANDY APPLE RED'),
    from_hex('#FF2400', 'SCARLET'),
    from_hex('#FF2800', 'FERRARI RED'),
    from_hex('#EE4266', 'CRAYOL'),
    from_hex('#FA8072', 'SALMON'),
    from_hex('#FF8A80', '¯\_(ツ)_/¯'),
    from_hex('#FFFFFF', 'WHITE'),
    from_hex('#FFFFFF', 'WHITE'),
    from_hex('#FFFFFF', 'WHITE'),
    from_hex('#FFFFFF', 'WHITE'),
]

PULSATING_RED = multi_color_linear_loop(
    5,
    # [-2:0:-1] means:
    # start at -2 (second to last)
    # stop at 0 (without including 0)
    # advance in steps of size -1
    REDS + REDS[-2:0:-1],
)

RAINBOW_ROAD_COLORS = [
    from_hex('#F32927'),
    from_hex('#F46D29'),
    from_hex('#F3BB26'),
    from_hex('#F2E22B'),
    from_hex('#76F228'),
    from_hex('#2DF298'),
    from_hex('#2BF3D9'),
    from_hex('#2BABF4'),
    from_hex('#2745F3'),
    from_hex('#6C29F3'),
    from_hex('#BD28F3'),
    from_hex('#F329E1'),
    from_hex('#F05129'),
    from_hex('#F3992B'),
    from_hex('#F3CE28'),
    from_hex('#BDE827'),
    from_hex('#4FF25B'),
    from_hex('#2AF3BD'),
    from_hex('#26C9E8'),
    from_hex('#2A6CF4'),
    from_hex('#4F36F4'),
    from_hex('#2F28F3'),
    from_hex('#E028E8'),
    from_hex('#F89192'),
    from_hex('#F7A87F'),
    from_hex('#F8D579'),
    from_hex('#F8EC7E'),
    from_hex('#ACF87E'),
    from_hex('#88F9C5'),
    from_hex('#89F8E8'),
]

RAINBOW_ROAD = multi_color_linear_loop(50, RAINBOW_ROAD_COLORS)

ALL_COLORS = (
    [
        NICE_RED,
        XANTHOUS,
        MOONSTONE,
        HOT_PINK,
        SPRING_GREEN,
    ]
    + GREENS
    + YELLOWS
    + REDS
    + RAINBOW_ROAD_COLORS
)


@enum.unique
class ColorOption(enum.Enum):
    # no colors
    NEVER = "never"
    # red when the timer has expired
    RED_ON_NEGATIVES = "red_on_negatives"
    # random colors
    COLORFUL = "colorful"
    # random colors but only when the timer has expired
    COLORFUL_ON_NEGATIVES = "colorful_on_negatives"
    # pulsating green when running and non-expired
    # pulsating yellow when approaching expiration time or when paused
    # pulsating red when the timer has expired
    PULSATING_TRAFFIC_LIGHT = "pulsating_traffic_light"
    # rainbow road colors when running
    # pulsating yellow when paused
    # pulsating red when the timer has expired
    RAINBOW_ROAD = "rainbow_road"
    # same as RAINBOW_ROAD, but in background colors instead of foreground colors.
    BACKGROUND_RAINBOW_ROAD = "background_rainbow_road"


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
            result += f"<span color='{random.choice(ALL_COLORS).hex}'>{c}</span>"
        else:
            result += c
    return result
