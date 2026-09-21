from __future__ import annotations

import sys

import API
from Direction import Direction


def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


class Mouse:
    def __init__(self, x: int = 0, y: int = 0, heading: Direction = Direction.NORTH) -> None:
        self.x = x
        self.y = y
        self.heading = heading
        self.total_steps = 0
        self.total_turns = 0

    @property
    def position(self) -> tuple[int, int]:
        return (self.x, self.y)

    def face(self, target: Direction) -> None:
        if target == self.heading:
            return

        if target == self.heading.turn_right():
            API.turnRight()
            self.total_turns += 1
        elif target == self.heading.turn_left():
            API.turnLeft()
            self.total_turns += 1
        else:
            API.turnRight()
            API.turnRight()
            self.total_turns += 2

        self.heading = target

    def move_forward(self) -> None:
        API.moveForward()
        self.total_steps += 1
        dx, dy = self.heading.delta()
        self.x += dx
        self.y += dy

    def go(self, direction: Direction) -> None:
        self.face(direction)
        self.move_forward()
