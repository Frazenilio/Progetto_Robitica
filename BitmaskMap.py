from __future__ import annotations

import sys
from collections import deque
from typing import Optional

import API
from Direction import Direction, relative_to_absolute
from Map import Map, get_deep_size


_DIR_BIT: dict[Direction, int] = {
    Direction.NORTH: 0x1,
    Direction.EAST:  0x2,
    Direction.SOUTH: 0x4,
    Direction.WEST:  0x8,
}


def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


class BitmaskMap(Map):
    ## Inizializziamo la griglia con i muri esterni
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)

        ## walls[x][y]: bitmask dei muri confermati
        self._walls: list[list[int]] = [[0] * height for _ in range(width)]

        ## known[x][y]: bitmask delle direzioni conosciute (che si sanno a priorio avendo la mappa)
        self._known: list[list[int]] = [[0] * height for _ in range(width)]

        ## Celle visitate
        self._visited: set[tuple[int, int]] = set()

        ## Distanze per il flood-fill
        self._distances: dict[tuple[int, int], int] = {}

        ## Inizializziamo i muri esterni
        self._init_boundary_walls()

    def _init_boundary_walls(self) -> None:
        for x in range(self.width):
            self._set_wall_bit(x, 0, Direction.SOUTH)
            self._set_wall_bit(x, self.height - 1, Direction.NORTH)
        for y in range(self.height):
            self._set_wall_bit(0, y, Direction.WEST)
            self._set_wall_bit(self.width - 1, y, Direction.EAST)

    ## Imposta un muro in una cella (non invalida le celle vicine)
    def _set_wall_bit(self, x: int, y: int, d: Direction) -> None:
        bit = _DIR_BIT[d]
        self._walls[x][y] |= bit
        self._known[x][y] |= bit

    ## Rimuove un muro da una cella (non invalida le celle vicine)
    def _clear_wall_bit(self, x: int, y: int, d: Direction) -> None:
        bit = _DIR_BIT[d]
        self._walls[x][y] &= ~bit
        self._known[x][y] |= bit

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def _neighbor(self, x: int, y: int, d: Direction) -> tuple[int, int]:
        dx, dy = d.delta()
        return x + dx, y + dy

    ## Imposta un muro in una cella (invalida anche la cella vicina)
    def set_wall(self, x: int, y: int, direction: Direction) -> None:
        bit = _DIR_BIT[direction]
        self._walls[x][y] |= bit
        self._known[x][y] |= bit
        ## Ora prende la cella vicina: essendo che un muro e' tra due celle
        ## ma la nostra struttura contiene le direzioni per le singole celle,
        ## ci serve modificare anche l'altra cella adiacente
        nx, ny = self._neighbor(x, y, direction)
        if self._in_bounds(nx, ny):
            opp_bit = _DIR_BIT[direction.opposite()]
            self._walls[nx][ny] |= opp_bit
            self._known[nx][ny] |= opp_bit

    ## Come il set ma invece lo rimuove (non dovrebbe servire)
    def clear_wall(self, x: int, y: int, direction: Direction) -> None:
        bit = _DIR_BIT[direction]
        self._walls[x][y] &= ~bit
        self._known[x][y] |= bit
        nx, ny = self._neighbor(x, y, direction)
        if self._in_bounds(nx, ny):
            opp_bit = _DIR_BIT[direction.opposite()]
            self._walls[nx][ny] &= ~opp_bit
            self._known[nx][ny] |= opp_bit

    ## Ritorna True se c'e' muro, False altrimenti. Se non e' noto (cella non ancora esplorata)
    ## allora ritorna None
    def has_wall(self, x: int, y: int, direction: Direction) -> Optional[bool]:
        bit = _DIR_BIT[direction]
        if not (self._known[x][y] & bit):
            return None
        return bool(self._walls[x][y] & bit)

    ## Come has_wall ma ritorna True anche se la cella non e' stata esplorata (visione ottimistica)
    def wall_blocks(self, x: int, y: int, direction: Direction) -> bool:
        bit = _DIR_BIT[direction]
        return bool((self._known[x][y] & bit) and (self._walls[x][y] & bit))

    def is_visited(self, x: int, y: int) -> bool:
        return (x, y) in self._visited

    def mark_visited(self, x: int, y: int) -> None:
        self._visited.add((x, y))

    def get_open_neighbors(self, x: int, y: int) -> list[tuple[int, int, Direction]]:
        result: list[tuple[int, int, Direction]] = []
        for d in Direction:
            if self.wall_blocks(x, y, d):
                continue
            nx, ny = self._neighbor(x, y, d)
            if self._in_bounds(nx, ny):
                result.append((nx, ny, d))
        return result

    ## Scan peculiare: aggiorna la mappa leggendo i sensori del robot
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

    ## Flood fill per calcolare le distanze dalle celle goals 
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

    ## Un path non e' piu' valido se uno dei due adjacent cells ha un muro in mezzo
    def path_still_valid(self, path: list[tuple[int, int]]) -> bool:
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            dx, dy = x2 - x1, y2 - y1
            d = _delta_to_direction(dx, dy)
            if d is None or self.wall_blocks(x1, y1, d):
                return False
        return True

    def visualize(self) -> None:
        for x in range(self.width):
            for y in range(self.height):
                for d in Direction:
                    if self.has_wall(x, y, d) is True:
                        API.setWall(x, y, d.api_char())
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
        for x in range(self.width):
            for y in range(self.height):
                if self._known[x][y] == 0:
                    continue
                for d in Direction:
                    if self._known[x][y] & _DIR_BIT[d]:
                        nx, ny = self._neighbor(x, y, d)
                        edge = (*min((x, y), (nx, ny)), *max((x, y), (nx, ny)))
                        seen.add(edge)
        return len(seen)

    def walls_present(self) -> int:
        seen: set[tuple[int, int, int, int]] = set()
        for x in range(self.width):
            for y in range(self.height):
                if self._walls[x][y] == 0:
                    continue
                for d in Direction:
                    if self._walls[x][y] & _DIR_BIT[d]:
                        nx, ny = self._neighbor(x, y, d)
                        edge = (*min((x, y), (nx, ny)), *max((x, y), (nx, ny)))
                        seen.add(edge)
        return len(seen)

    def python_memory_bytes(self) -> int:
        seen: set[int] = set()
        total = get_deep_size(self._walls, seen)
        total += get_deep_size(self._known, seen)
        total += get_deep_size(self._visited, seen)
        total += get_deep_size(self._distances, seen)
        return total

    def get_stats(self) -> dict[str, object]:
        return super().get_stats()


_DELTA_MAP: dict[tuple[int, int], Direction] = {
    (0, 1): Direction.NORTH, (1, 0): Direction.EAST,
    (0, -1): Direction.SOUTH, (-1, 0): Direction.WEST,
}

def _delta_to_direction(dx: int, dy: int) -> Optional[Direction]:
    return _DELTA_MAP.get((dx, dy))
