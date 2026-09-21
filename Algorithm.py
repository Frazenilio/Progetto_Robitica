from __future__ import annotations

import sys
from abc import ABC, abstractmethod

import API
from Direction import Direction
from Map import Map
from Mouse import Mouse


def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


class Algorithm(ABC):
    def __init__(self, maze: Map, mouse: Mouse, goals: set[tuple[int, int]]) -> None:
        self.maze = maze
        self.mouse = mouse
        self.goals = goals

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def plan_path(self, start: tuple[int, int]) -> list[tuple[int, int]]:
        ...

    def _direction_between(self, frm: tuple[int, int], to: tuple[int, int]) -> Direction:
        dx = to[0] - frm[0]
        dy = to[1] - frm[1]
        for d in Direction:
            if d.delta() == (dx, dy):
                return d
        raise ValueError(f"Cells {frm} and {to} are not adjacent")

    def is_goal_reached(self) -> bool:
        return self.mouse.position in self.goals

    def _direction_between(self, frm: tuple[int, int], to: tuple[int, int]) -> Direction:
        dx = to[0] - frm[0]
        dy = to[1] - frm[1]
        for d in Direction:
            if d.delta() == (dx, dy):
                return d
        raise ValueError(f"Cells {frm} and {to} are not adjacent")

    def run(self) -> None:
        log(f"[{self.name()}] Starting exploration...")

        while True:
            ## Scan dei muri
            self.maze.scan_and_update(self.mouse.x, self.mouse.y, self.mouse.heading)
            self.maze.mark_visited(self.mouse.x, self.mouse.y)
            self.maze.compute_distances(self.goals)
            self.maze.visualize()

            ## Se siamo al goal, non serve continuare
            if self.is_goal_reached():
                log(f"[{self.name()}] Goal reached at {self.mouse.position}!")
                return

            ## Ora si cerca un path
            path = self.plan_path(self.mouse.position)

            if not path or len(path) < 2:
                log(f"[{self.name()}] No path found — maze may be unsolvable.")
                return

            ## Ora seguiamo il path
            step_index = 1
            while step_index < len(path):
                next_cell = path[step_index]
                direction = self._direction_between(self.mouse.position, next_cell)

                ## Move
                self.mouse.go(direction)

                ## Scan dei muri nella nuova posizione
                self.maze.scan_and_update(self.mouse.x, self.mouse.y, self.mouse.heading)
                self.maze.mark_visited(self.mouse.x, self.mouse.y)
                self.maze.compute_distances(self.goals)
                self.maze.visualize()

                ## Check goal
                if self.is_goal_reached():
                    log(f"[{self.name()}] Goal reached at {self.mouse.position}!")
                    return

                ## Verifichiamo che il path sia ancora valido
                remaining = path[step_index:]
                if not self.maze.path_still_valid(remaining):
                    log(f"[{self.name()}] Wall discovered — replanning from {self.mouse.position}")
                    ## Se non facciamo break, il mouse continua a camminare verso il punto successivo anche se ha trovato un muro di fronte a sé
                    break 

                step_index += 1
