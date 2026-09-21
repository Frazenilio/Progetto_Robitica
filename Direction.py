from enum import IntEnum


class Direction(IntEnum):
    NORTH = 0
    EAST  = 1
    SOUTH = 2
    WEST  = 3

    def turn_right(self) -> Direction:
        return Direction((self.value + 1) % 4)

    def turn_left(self) -> Direction:
        return Direction((self.value + 3) % 4)

    def opposite(self) -> Direction:
        return Direction((self.value + 2) % 4)

    def delta(self) -> tuple[int, int]:
        return _DELTAS[self.value]

    def api_char(self) -> str:
        return _API_CHARS[self.value]

_DELTAS: list[tuple[int, int]] = [
    ( 0,  1), ## NORD
    ( 1,  0), ## EST
    ( 0, -1), ## SUD
    (-1,  0), ## OVEST
]

_API_CHARS: list[str] = ["n", "e", "s", "w"]


def relative_to_absolute(heading: Direction, relative: str) -> Direction:
    offsets = {"front": 0, "right": 1, "back": 2, "left": 3}
    return Direction((heading.value + offsets[relative]) % 4)
