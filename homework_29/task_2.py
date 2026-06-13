from collections import deque


def bfs(graph, start):
    distances = {v: float("inf") for v in graph}
    distances[start] = 0

    queue = deque([start])

    while queue:
        current = queue.popleft()

        for neigh in graph[current]:
            if distances[neigh] == float("inf"):
                distances[neigh] = distances[current] + 1
                queue.append(neigh)

    return distances


def all_pairs_shortest_path(graph):
    result = {}

    for v in graph:
        result[v] = bfs(graph, v)

    return result