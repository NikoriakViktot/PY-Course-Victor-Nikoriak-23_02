from collections import defaultdict

class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = defaultdict(list)

    # додати ребро
    def add_edge(self, u, v):
        self.graph[u].append(v)

    # DFS для першого проходу (запис порядку завершення)
    def dfs_fill_order(self, v, visited, stack):
        visited[v] = True

        for neighbor in self.graph[v]:
            if not visited[neighbor]:
                self.dfs_fill_order(neighbor, visited, stack)

        stack.append(v)

    # транспонування графа
    def transpose(self):
        g = Graph(self.V)

        for v in self.graph:
            for neighbor in self.graph[v]:
                g.add_edge(neighbor, v)

        return g

    # DFS для SCC
    def dfs_util(self, v, visited, component):
        visited[v] = True
        component.append(v)

        for neighbor in self.graph[v]:
            if not visited[neighbor]:
                self.dfs_util(neighbor, visited, component)

    # основна функція SCC
    def strongly_connected_components(self):
        stack = []
        visited = [False] * self.V

        # 1. заповнюємо стек
        for i in range(self.V):
            if not visited[i]:
                self.dfs_fill_order(i, visited, stack)

        # 2. транспонуємо граф
        gr = self.transpose()

        # 3. DFS у порядку стеку
        visited = [False] * self.V

        print("Strongly Connected Components:")

        while stack:
            i = stack.pop()

            if not visited[i]:
                component = []
                gr.dfs_util(i, visited, component)
                print(component)


# ===== TEST =====
g = Graph(5)
g.add_edge(0, 2)
g.add_edge(2, 1)
g.add_edge(1, 0)
g.add_edge(0, 3)
g.add_edge(3, 4)

g.strongly_connected_components()