class TimerException(Exception):
    """Base class for this timer's errors.

    Procure to keep error messages short as they will
    be displayed in the i3blocket.
    """

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*[message, args])
        self.message = message


class BadValue(TimerException): ...


class BadPrettyTime(BadValue): ...


class BadClockTime(BadValue): ...


class BadInteger(BadValue): ...


class BadEnum(BadValue): ...
