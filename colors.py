import enum
import random

RED = "#BB0A21"  # red

COLORS = [
    RED,
    "#FFBC42",  # Xanthous (yellow)
    "#5EB1BF",  # Moonstone (light blue)
    "#F564A9",  # Hot pink
    "#04F06A",  # Spring green
]


@enum.unique
class ColorOption(enum.Enum):
    NEVER = "never"
    COLORFUL = "colorful"
    COLORFUL_ON_NEGATIVES = "colorful_on_negatives"
    RED_ON_NEGATIVES = "red_on_negatives"


def red(text: str) -> str:
    return f"<span color='{RED}'>{text}</span>"


def colorize(text: str) -> str:
    result = ""
    for c in text:
        result += f"<span color='{random.choice(COLORS)}'>{c}</span>"
    return result
