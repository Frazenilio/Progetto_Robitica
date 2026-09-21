from __future__ import annotations

import sys

import API
from Map import Map
from WallsMap import WallsMap
from BitmaskMap import BitmaskMap
from Mouse import Mouse
from Direction import Direction
from BFSAlgorithm import BFSAlgorithm
from FloodFill import FloodFill
from AStarAlgorithm import AStarAlgorithm

## Usato da micromouse
def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


## Ritorna i goal del classico micromouse: la subarea 2x2 
def default_goals(width: int, height: int) -> set[tuple[int, int]]:
    mid_x = width // 2
    mid_y = height // 2
    return {
        (mid_x - 1, mid_y - 1),
        (mid_x - 1, mid_y),
        (mid_x,     mid_y - 1),
        (mid_x,     mid_y),
    }


ALGORITHMS = {
    "bfs": BFSAlgorithm,
    "floodfill": FloodFill,
    "astar": AStarAlgorithm,
}

MAP_TYPES: dict[str, type[Map]] = {
    "wallsmap": WallsMap,
    "bitmask": BitmaskMap,
}


def main() -> None:
    log("START")

    algo_name = "astar"
    if len(sys.argv) > 1:
        algo_name = sys.argv[1].lower()
    
    map_name = "wallsmap"
    if len(sys.argv) > 2:
        map_name = sys.argv[2].lower()
    
    if algo_name not in ALGORITHMS:
        log(f"Unknown algorithm '{algo_name}'. Available: {', '.join(ALGORITHMS.keys())}")
        log("Falling back to 'bfs'.")
        algo_name = "bfs"

    if map_name not in MAP_TYPES:
        log(f"Unknown map type '{map_name}'. Available: {', '.join(MAP_TYPES.keys())}")
        log("Falling back to 'wallsmap'.")
        map_name = "wallsmap"

    width = API.mazeWidth()
    height = API.mazeHeight()
    log(f"Maze size: {width}x{height}")

    map_cls = MAP_TYPES[map_name]
    maze = map_cls(width, height)
    mouse = Mouse(x=0, y=0, heading=Direction.NORTH)
    goals = default_goals(width, height)

    log(f"Goal cells: {goals}")
    log(f"Algorithm:  {algo_name}")
    log(f"Map type:   {map_name} ({map_cls.__name__})")

    algorithm_cls = ALGORITHMS[algo_name]
    algorithm = algorithm_cls(maze, mouse, goals)
    
    algorithm.run()
    
    maze.print_stats()

    log("Robot Stats")
    log(f"total_steps:  {mouse.total_steps}")
    log(f"total_turns:  {mouse.total_turns}")

    log("Done")


if __name__ == "__main__":
    main()
