from __future__ import annotations

from collections import deque

from Algorithm import Algorithm


class BFSAlgorithm(Algorithm):
    def name(self) -> str:
        return "BFS"

    def plan_path(self, start: tuple[int, int]) -> list[tuple[int, int]]:
        ## Se il nodo di partenza e' un goal, il percorso e' solo il nodo di partenza
        if start in self.goals:
            return [start]

        ## Insieme dei nodi visitati, per evitare di visitare due volte lo stesso nodo (evita cicli)
        visited: set[tuple[int, int]] = {start}
        ## Dizionario che memorizza il percorso, mappando ogni nodo al suo predecessore
        parent: dict[tuple[int, int], tuple[int, int]] = {}
        ## Coda di nodi da esplorare (FIFO - First In First Out)
        queue: deque[tuple[int, int]] = deque([start])

        while queue:
            ## Essendo una ricerca in ampiezza, si parte da sinistra
            cx, cy = queue.popleft()

            ## Aggiungiamo i vicini alla lista (i vicini sono, di fatto, usati per i nuovi stati
            ## nel nostro albero di ricerca)
            for nx, ny, _ in self.maze.get_open_neighbors(cx, cy):
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                parent[(nx, ny)] = (cx, cy)

                ## Se il vicino e' un goal, ricostruiamo il percorso (all'indietro)
                if (nx, ny) in self.goals:
                    path: list[tuple[int, int]] = []
                    node: tuple[int, int] = (nx, ny)
                    while node != start:
                        path.append(node)
                        node = parent[node]
                    path.append(start)
                    path.reverse()
                    return path

                queue.append((nx, ny))

        ## Se la coda e' vuota e non abbiamo trovato un goal, non esiste un percorso
        return []
