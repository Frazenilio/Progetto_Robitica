from __future__ import annotations

import heapq
from Algorithm import Algorithm


class AStarAlgorithm(Algorithm):
    def name(self) -> str:
        return "A*"

    def _heuristic(self, cell: tuple[int, int]) -> int:
        cx, cy = cell
        return min(abs(cx - gx) + abs(cy - gy) for gx, gy in self.goals)

    def plan_path(self, start: tuple[int, int]) -> list[tuple[int, int]]:
        ## Caso: siamo gia' al goal
        if start in self.goals:
            return [start]

        ## Inizializziamo la priority queue con il nodo di partenza
        pq: list[tuple[int, int, tuple[int, int]]] = []
        ## Uso di un HEAP: Aiuta a sortare gli elementi gia' in base alla loro f(x)
        heapq.heappush(pq, (self._heuristic(start), 0, start))

        ## Questi invece servono per ricostruire il percorso: parent[figlio] = genitore
        parent: dict[tuple[int, int], tuple[int, int]] = {}
        ## Costo del percorso dal nodo di partenza al nodo corrente
        g_score: dict[tuple[int, int], int] = {start: 0}
        ## Insieme dei nodi gia' visitati
        closed_set: set[tuple[int, int]] = set()

        while pq:
            ## Estraiamo il nodo con la minore f(x). Il primo elemento e' f(x), il secondo e' g(x) e il terzo e' il nodo
            ## Prendiamo pero' g perche', a parità di f, scegliamo la g minore
            _, g, current = heapq.heappop(pq)

            ## Se il nodo corrente e' un goal, ricostruiamo il percorso
            if current in self.goals:
                path: list[tuple[int, int]] = []
                node = current
                while node != start:
                    path.append(node)
                    node = parent[node]
                path.append(start)
                path.reverse()
                return path

            ## A* controlla i nodi che sono nella open list. Nella closed ci vanno quelli
            ## gia' visitati
            ## E puo' capitare che ci siano due cammini per raggiungere lo stesso nodo,
            ## quindi controlliamo se quello corrente ha un percorso peggiore del precedente
            if current in closed_set:
                continue
            closed_set.add(current)

            ## Esploriamo i vicini del nodo corrente
            cx, cy = current
            for nx, ny, _ in self.maze.get_open_neighbors(cx, cy):
                neighbor = (nx, ny)
                ## Se il vicino e' gia' stato visitato, lo saltiamo
                if neighbor in closed_set:
                    continue

                ## Calcoliamo il costo del percorso dal nodo di partenza al nodo corrente
                ## +1 perche' noi ci muoviamo di una casella da quella corrente
                tentative_g = g + 1
                ## Se il costo del percorso dal nodo di partenza al nodo vicino considerato
                ## e' minore del percorso gia' trovato per il nodo vicino considerato
                ## Traduzione: se non abbiamo mai visto il neighbor, sicuramente aggiorniamo il suo g
                ## infatti non ci sara' il suo g_score e il get ritornera' inf.
                ## Ma se lo abbiamo gia' visto, confrontiamo il costo e aggiorniamo solo se e' minore
                ## (con un'euristica ammissibile A* garantisce che non ci siano percorsi migliori)
                if tentative_g < g_score.get(neighbor, float('inf')):
                    ## Aggiorniamo il costo del percorso dal nodo di partenza al nodo vicino considerato
                    g_score[neighbor] = tentative_g
                    ## Aggiorniamo il genitore del nodo vicino considerato
                    parent[neighbor] = current
                    ## Calcoliamo la f del nodo vicino considerato
                    f = tentative_g + self._heuristic(neighbor)
                    ## Aggiungiamo il nodo vicino alla priority queue
                    heapq.heappush(pq, (f, tentative_g, neighbor))

        ## Se la priority queue e' vuota e non abbiamo trovato un goal, non c'è un percorso
        return []
