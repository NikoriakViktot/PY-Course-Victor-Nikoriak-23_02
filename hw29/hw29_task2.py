from collections import deque, defaultdict

class GraphBFS:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = defaultdict(list)

    def add_edge(self, u, v):
        self.graph[u].append(v)

    # BFS для одного стартового вузла
    def bfs(self, start):
        distances = [-1] * self.V
        queue = deque()

        queue.append(start)
        distances[start] = 0

        while queue:
            node = queue.popleft()

            for neighbor in self.graph[node]:
                if distances[neighbor] == -1:
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)

        return distances

    # All-pairs shortest path через BFS
    def all_pairs_shortest_path(self):
        result = []

        for i in range(self.V):
            distances = self.bfs(i)
            result.append(distances)

        return result


# ===== TEST =====
g = GraphBFS(4)
g.add_edge(0, 1)
g.add_edge(0, 2)
g.add_edge(1, 2)
g.add_edge(2, 3)
g.add_edge(3, 3)

paths = g.all_pairs_shortest_path()

print("All-Pairs Shortest Path (BFS):")
for row in paths:
    print(row)