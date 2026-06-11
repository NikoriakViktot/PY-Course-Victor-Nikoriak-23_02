from collections import deque


class Graph:
    def __init__(self):
        self.vertices = {}

    def add_vertex(self, vertex):
        if vertex not in self.vertices:
            self.vertices[vertex] = []

    def add_edge(self, from_vertex, to_vertex):
        self.add_vertex(from_vertex)
        self.add_vertex(to_vertex)
        self.vertices[from_vertex].append(to_vertex)
        self.vertices[to_vertex].append(from_vertex)

    def bfs_shortest_paths(self, start_vertex):
        distances = {vertex: None for vertex in self.vertices}
        distances[start_vertex] = 0

        queue = deque([start_vertex])

        while queue:
            current_vertex = queue.popleft()

            for neighbour in self.vertices[current_vertex]:
                if distances[neighbour] is None:
                    distances[neighbour] = distances[current_vertex] + 1
                    queue.append(neighbour)

        return distances

    def all_pairs_shortest_paths(self):
        result = {}

        for vertex in self.vertices:
            result[vertex] = self.bfs_shortest_paths(vertex)

        return result


graph = Graph()
graph.add_edge("A", "B")
graph.add_edge("A", "C")
graph.add_edge("B", "D")
graph.add_edge("C", "D")
graph.add_edge("D", "E")

shortest_paths = graph.all_pairs_shortest_paths()

assert shortest_paths["A"] == {
    "A": 0,
    "B": 1,
    "C": 1,
    "D": 2,
    "E": 3,
}

assert shortest_paths["E"] == {
    "A": 3,
    "B": 2,
    "C": 2,
    "D": 1,
    "E": 0,
}

print(shortest_paths)
print("All assertions passed")
