from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from collections import deque
from typing import Optional

from Direction import Direction


def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


def get_deep_size(obj: object, seen: Optional[set[int]] = None) -> int:
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(get_deep_size(k, seen) + get_deep_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, deque)):
        size += sum(get_deep_size(item, seen) for item in obj)
    return size



class Map(ABC):
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    @abstractmethod
    def set_wall(self, x: int, y: int, direction: Direction) -> None:
        ...

    @abstractmethod
    def clear_wall(self, x: int, y: int, direction: Direction) -> None:
        ...

    @abstractmethod
    def has_wall(self, x: int, y: int, direction: Direction) -> Optional[bool]:
        ...

    @abstractmethod
    def wall_blocks(self, x: int, y: int, direction: Direction) -> bool:
        ...

    @abstractmethod
    def is_visited(self, x: int, y: int) -> bool:
        ...

    @abstractmethod
    def mark_visited(self, x: int, y: int) -> None:
        ...
        
    @abstractmethod
    def get_open_neighbors(self, x: int, y: int) -> list[tuple[int, int, Direction]]:
        ...


    @abstractmethod
    def scan_and_update(self, x: int, y: int, heading: Direction) -> None:
        ...

    @abstractmethod
    def compute_distances(self, goals: set[tuple[int, int]]) -> dict[tuple[int, int], int]:
        ...

    @property
    @abstractmethod
    def distances(self) -> dict[tuple[int, int], int]:
        ...

    @abstractmethod
    def path_still_valid(self, path: list[tuple[int, int]]) -> bool:
        ...

    @abstractmethod
    def visualize(self) -> None:
        ...

    @abstractmethod
    def visualize_path(self, path: list[tuple[int, int]]) -> None:
        ...

    def total_cells(self) -> int:
        return self.width * self.height

    @abstractmethod
    def cells_visited(self) -> int:
        ...

    @abstractmethod
    def walls_discovered(self) -> int:
        ...

    @abstractmethod
    def walls_present(self) -> int:
        ...

    def exploration_ratio(self) -> float:
        total = self.total_cells()
        return self.cells_visited() / total if total > 0 else 0.0

    def total_edges(self) -> int:
        return self.width * (self.height + 1) + (self.width + 1) * self.height

    def discovery_ratio(self) -> float:
        total = self.total_edges()
        return self.walls_discovered() / total if total > 0 else 0.0

    @abstractmethod
    def python_memory_bytes(self) -> int:
        ...

    def get_stats(self) -> dict[str, object]:
        return {
            "map_type": type(self).__name__,
            "dimensions": f"{self.width}x{self.height}",
            "total_cells": self.total_cells(),
            "cells_visited": self.cells_visited(),
            "exploration_ratio": f"{self.exploration_ratio():.1%}",
            "total_edges": self.total_edges(),
            "walls_discovered": self.walls_discovered(),
            "walls_present": self.walls_present(),
            "discovery_ratio": f"{self.discovery_ratio():.1%}",
            "python_memory_bytes": f"{self.python_memory_bytes()} B",
        }

    def print_stats(self) -> None:
        stats = self.get_stats()
        log(f"Map Stats ({stats['map_type']})")
        for key, val in stats.items():
            if key != "map_type":
                log(f"  {key}: {val}")
