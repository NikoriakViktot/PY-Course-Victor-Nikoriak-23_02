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

    def _dfs(self, vertex, visited, result):
        visited.add(vertex)

        for neighbour in self.vertices[vertex]:
            if neighbour not in visited:
                self._dfs(neighbour, visited, result)

        result.append(vertex)

    def _dfs_component(self, vertex, visited, component):
        visited.add(vertex)
        component.append(vertex)

        for neighbour in self.vertices[vertex]:
            if neighbour not in visited:
                self._dfs_component(neighbour, visited, component)

    def transpose(self):
        transposed_graph = Graph()

        for vertex in self.vertices:
            transposed_graph.add_vertex(vertex)

        for vertex in self.vertices:
            for neighbour in self.vertices[vertex]:
                transposed_graph.add_edge(neighbour, vertex)

        return transposed_graph

    def strongly_connected_components(self):
        visited = set()
        finish_order = []

        for vertex in self.vertices:
            if vertex not in visited:
                self._dfs(vertex, visited, finish_order)

        transposed_graph = self.transpose()
        visited = set()
        components = []

        for vertex in reversed(finish_order):
            if vertex not in visited:
                component = []
                transposed_graph._dfs_component(vertex, visited, component)
                components.append(component)

        return components


def normalize_components(components):
    return sorted([sorted(component) for component in components])


graph = Graph()
graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "A")
graph.add_edge("B", "D")
graph.add_edge("D", "E")
graph.add_edge("E", "F")
graph.add_edge("F", "D")
graph.add_edge("G", "F")
graph.add_edge("G", "H")
graph.add_edge("H", "G")

components = graph.strongly_connected_components()

assert normalize_components(components) == [
    ["A", "B", "C"],
    ["D", "E", "F"],
    ["G", "H"],
]

print(components)
print("All assertions passed")
