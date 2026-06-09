from collections import deque


class GraphAllPairsBFS:
    def __init__(self, vertices_count: int):
        self.V = vertices_count
        # Представлення графа у вигляді списку суміжності
        self.adj = {i: [] for i in range(vertices_count)}

    def add_edge(self, u: int, v: int, bidirectional: bool = True):
        """Додавання ребра. За замовчуванням — неорієнтоване."""
        self.adj[u].append(v)
        if bidirectional:
            self.adj[v].append(u)

    def _bfs_from_source(self, source: int) -> list[int]:
        """Запуск BFS з однієї конкретної вершини."""
        # Ініціалізуємо відстані нескінченністю (float('inf'))
        distances = [float('inf')] * self.V
        distances[source] = 0

        queue = deque([source])

        while queue:
            current = queue.popleft()

            for neighbor in self.adj[current]:
                # Якщо сусіда ще не відвідували
                if distances[neighbor] == float('inf'):
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)

        return distances

    def find_all_pairs_shortest_paths(self) -> list[list[int]]:
        """
        Головна функція. Запускає BFS для кожної вершини
        та будує підсумкову матрицю відстаней.
        """
        matrix = []
        for i in range(self.V):
            # Отримуємо масив найкоротших відстаней від вершини 'i' до всіх інших
            distances_from_i = self._bfs_from_source(i)
            matrix.append(distances_from_i)
        return matrix


# ── Тести ────────────────────────────────────────────────────────────────────
def run_all_pairs_tests():
    print("=== Задача 2: Найкоротші шляхи між усіма парами (BFS) ===")

    # Створюємо простий граф з 4 вершинами (0, 1, 2, 3)
    # Зв'язки: 0 - 1 - 2
    #            \   /
    #              3
    g = GraphAllPairsBFS(4)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(0, 3)

    matrix = g.find_all_pairs_shortest_paths()

    # Виводимо матрицю у красивому табличному вигляді
    print("\nМатриця найкоротших відстаней між вершинами:")
    print("     " + " ".join(f"[{j}]" for j in range(g.V)))
    print("-" * (g.V * 5 + 5))
    for i in range(g.V):
        row_str = " ".join(f"{dist:3}" if dist != float('inf') else " ∞ " for dist in matrix[i])
        print(f"[{i}] | {row_str}")


run_all_pairs_tests()


'''
=== Задача 2: Найкоротші шляхи між усіма парами (BFS) ===

Матриця найкоротших відстаней між вершинами:
       [0] [1] [2] [3]
-------------------------
[0] |   0   1   2   1
[1] |   1   0   1   2
[2] |   2   1   0   1
[3] |   1   2   1   0

'''