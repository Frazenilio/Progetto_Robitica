from __future__ import annotations

from collections import deque

from Algorithm import Algorithm
from Direction import Direction


class FloodFill(Algorithm):
    def name(self) -> str:
        return "Flood Fill"

    def plan_path(self, start: tuple[int, int]) -> list[tuple[int, int]]:
        if start in self.goals:
            return [start]

        ## Riprende le distanze
        distances = self.maze.distances

        if start not in distances:
            return []

        path: list[tuple[int, int]] = [start]
        current = start
        visited_in_path: set[tuple[int, int]] = {start}

        while current not in self.goals:
            cx, cy = current
            neighbors = self.maze.get_open_neighbors(cx, cy)

            best = None
            best_dist = float("inf")

            ## Scelgo il vicino migliore raggiungibile e non ancora visitato
            for nx, ny, d in neighbors:
                if (nx, ny) in visited_in_path:
                    continue
                nd = distances.get((nx, ny), float("inf"))
                if nd < best_dist:
                    best_dist = nd
                    best = (nx, ny)

            if best is None:
                ## Tutti i vicini sono gia' stati visitati o irraggiungibili
                ## Questo significa che sono ad un vicolo cieco e devo tornare indietro
                ## quindi "rilasso" la condizione e prendo il path a ritroso
                for nx, ny, d in neighbors:
                    nd = distances.get((nx, ny), float("inf"))
                    if nd < best_dist:
                        best_dist = nd
                        best = (nx, ny)

            ## A questo punto (non dovrebbe succedere) il mouse è completamente bloccato
            if best is None:
                break

            ## A questo punto, procedo con lo spostamento verso il best
            path.append(best)
            visited_in_path.add(best)
            current = best

        return path
