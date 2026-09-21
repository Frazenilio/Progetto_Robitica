from __future__ import annotations

import sys
from collections import deque
from typing import Optional

import API
from Direction import Direction, relative_to_absolute
from Map import Map, get_deep_size

WALL_UNKNOWN = None
WALL_PRESENT = True
WALL_ABSENT  = False


def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


class WallsMap(Map):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)

        ## Contiene i muri per ogni cella e direzione 
        ## (della mappa intera, aggiornato con l'esplorazione)
        self._walls: dict[tuple[int, int, Direction], Optional[bool]] = {}

        self._visited: set[tuple[int, int]] = set()

        ## Distanze di ogni cella dal centro (Flood fill)
        self._distances: dict[tuple[int, int], int] = {}

        ## Inizializza i muri esterni (questi sono sempre presenti)
        self._init_boundary_walls()

    def _init_boundary_walls(self) -> None:
        for x in range(self.width):
            self.set_wall(x, 0, Direction.SOUTH)
            self.set_wall(x, self.height - 1, Direction.NORTH)
        for y in range(self.height):
            self.set_wall(0, y, Direction.WEST)
            self.set_wall(self.width - 1, y, Direction.EAST)

    def set_wall(self, x: int, y: int, direction: Direction) -> None:
        ## Si imposta il valore direttamente
        self._walls[(x, y, direction)] = WALL_PRESENT
        ## Ma la stessa cosa deve essere fatta con la cella adiacente (per coerenza)
        nx, ny = self._neighbor(x, y, direction)
        if self._in_bounds(nx, ny):
            self._walls[(nx, ny, direction.opposite())] = WALL_PRESENT

    def clear_wall(self, x: int, y: int, direction: Direction) -> None:
        self._walls[(x, y, direction)] = WALL_ABSENT
        nx, ny = self._neighbor(x, y, direction)
        if self._in_bounds(nx, ny):
            self._walls[(nx, ny, direction.opposite())] = WALL_ABSENT

    ## Controlla che un muro non sia Unkown
    def has_wall(self, x: int, y: int, direction: Direction) -> Optional[bool]:
        return self._walls.get((x, y, direction), WALL_UNKNOWN)

    ## Controlla che un muro sia PRESENTE (non Unknown o Absent)
    def wall_blocks(self, x: int, y: int, direction: Direction) -> bool:
        return self.has_wall(x, y, direction) is WALL_PRESENT
        
    def is_visited(self, x: int, y: int) -> bool:
        return (x, y) in self._visited

    def mark_visited(self, x: int, y: int) -> None:
        self._visited.add((x, y))

    def _neighbor(self, x: int, y: int, direction: Direction) -> tuple[int, int]:
        dx, dy = direction.delta()
        return x + dx, y + dy

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_open_neighbors(self, x: int, y: int) -> list[tuple[int, int, Direction]]:
        result: list[tuple[int, int, Direction]] = []
        for d in Direction:
            if self.wall_blocks(x, y, d):
                continue
            nx, ny = self._neighbor(x, y, d)
            if self._in_bounds(nx, ny):
                result.append((nx, ny, d))
        return result

    ## Scan chiamato ad ogni iterazione
    def scan_and_update(self, x: int, y: int, heading: Direction) -> None:
        sensor_calls = {
            "front": API.wallFront,
            "right": API.wallRight,
            "left":  API.wallLeft,
            "back":  API.wallBack,
        }

        for relative_name, sensor_fn in sensor_calls.items():
            abs_dir = relative_to_absolute(heading, relative_name)
            if sensor_fn():
                self.set_wall(x, y, abs_dir)
            else:
                self.clear_wall(x, y, abs_dir)

    ## Flood fill
    def compute_distances(self, goals: set[tuple[int, int]]) -> dict[tuple[int, int], int]:
        dist: dict[tuple[int, int], int] = {}
        queue: deque[tuple[int, int]] = deque()

        for gx, gy in goals:
            dist[(gx, gy)] = 0
            queue.append((gx, gy))

        while queue:
            cx, cy = queue.popleft()
            for nx, ny, _ in self.get_open_neighbors(cx, cy):
                if (nx, ny) not in dist:
                    dist[(nx, ny)] = dist[(cx, cy)] + 1
                    queue.append((nx, ny))

        self._distances = dist
        return dist

    @property
    def distances(self) -> dict[tuple[int, int], int]:
        return self._distances

    ## Path validation: un path e' valido se non ci sono muri nel percorso
    def path_still_valid(self, path: list[tuple[int, int]]) -> bool:
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            dx, dy = x2 - x1, y2 - y1
            direction = _delta_to_direction(dx, dy)
            if direction is None:
                return False
            if self.wall_blocks(x1, y1, direction):
                return False
        return True

    def visualize(self) -> None:
        for (x, y, d), state in self._walls.items():
            if state is WALL_PRESENT:
                API.setWall(x, y, d.api_char())

        for x in range(self.width):
            for y in range(self.height):
                if (x, y) in self._visited:
                    API.setColor(x, y, "G")
                if (x, y) in self._distances:
                    API.setText(x, y, str(self._distances[(x, y)]))

    def visualize_path(self, path: list[tuple[int, int]]) -> None:
        for x, y in path:
            API.setColor(x, y, "B")

    def cells_visited(self) -> int:
        return len(self._visited)

    def walls_discovered(self) -> int:
        seen: set[tuple[int, int, int, int]] = set()
        for (x, y, d), state in self._walls.items():
            if state is not WALL_UNKNOWN:
                nx, ny = self._neighbor(x, y, d)
                edge = (*min((x, y), (nx, ny)), *max((x, y), (nx, ny)))
                seen.add(edge)
        return len(seen)

    def walls_present(self) -> int:
        seen: set[tuple[int, int, int, int]] = set()
        for (x, y, d), state in self._walls.items():
            if state is WALL_PRESENT:
                nx, ny = self._neighbor(x, y, d)
                edge = (*min((x, y), (nx, ny)), *max((x, y), (nx, ny)))
                seen.add(edge)
        return len(seen)

    def python_memory_bytes(self) -> int:
        seen: set[int] = set()
        total = get_deep_size(self._walls, seen)
        total += get_deep_size(self._visited, seen)
        total += get_deep_size(self._distances, seen)
        return total

    def get_stats(self) -> dict[str, object]:
        stats = super().get_stats()
        stats["storage_entries"] = len(self._walls)
        return stats


_DELTA_MAP: dict[tuple[int, int], Direction] = {
    ( 0,  1): Direction.NORTH,
    ( 1,  0): Direction.EAST,
    ( 0, -1): Direction.SOUTH,
    (-1,  0): Direction.WEST,
}

def _delta_to_direction(dx: int, dy: int) -> Optional[Direction]:
    return _DELTA_MAP.get((dx, dy))
