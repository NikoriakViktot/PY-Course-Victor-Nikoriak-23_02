from collections import defaultdict


class Graph:
    def __init__(self, vertices_count: int):
        self.V = vertices_count
        # Граф представлений списком суміжності
        self.graph = defaultdict(list)

    def add_edge(self, u: int, v: int):
        """Додавання орієнтованого ребра з u в v."""
        self.graph[u].append(v)

    def _fill_order(self, v: int, visited: list, stack: list):
        """Перший DFS: заповнює стек вузлами в порядку завершення їх обробки."""
        visited[v] = True
        for neighbor in self.graph[v]:
            if not visited[neighbor]:
                self._fill_order(neighbor, visited, stack)
        # Вузол додається в стек, коли всі його нащадки повністю оброблені
        stack.append(v)

    def _get_transpose(self) -> 'Graph':
        """Створення транспонованого (інвертованого) графа: ребра міняють напрямок."""
        g_rev = Graph(self.V)
        for node in self.graph:
            for neighbor in self.graph[node]:
                g_rev.add_edge(neighbor, node)
        return g_rev

    def _dfs_scc(self, v: int, visited: list, current_scc: list):
        """Другий DFS: збирає всі досяжні вузли в одну компоненту зв'язності."""
        visited[v] = True
        current_scc.append(v)
        for neighbor in self.graph[v]:
            if not visited[neighbor]:
                self._dfs_scc(neighbor, visited, current_scc)

    def find_sccs(self) -> list[list[int]]:
        """Головна функція для пошуку всіх сильно зв'язаних компонентів (SCC)."""
        stack = []
        visited = [False] * self.V

        # Крок 1: Запускаємо перший DFS для визначення порядку виходу (топологічний сорт)
        for i in range(self.V):
            if not visited[i]:
                self._fill_order(i, visited, stack)

        # Крок 2: Транспонуємо граф
        g_rev = self._get_transpose()

        # Крок 3: Скидаємо масив відвіданих вузлів для другого DFS
        visited = [False] * self.V
        all_sccs = []

        # Крок 4: Обробимо всі вузли у порядку, заданому першим DFS (із кінця стека)
        while stack:
            v = stack.pop()
            if not visited[v]:
                current_scc = []
                # Запускаємо другий DFS на інвертованому графі
                g_rev._dfs_scc(v, visited, current_scc)
                all_sccs.append(current_scc)

        return all_sccs


# ── Тести ────────────────────────────────────────────────────────────────────
def run_scc_tests():
    print("=== Задача 1: Сильно зв'язані компоненти (SCC) ===")

    # Створюємо граф з 5 вершинами (0, 1, 2, 3, 4)
    # Схема графа:
    # 1 ──> 0 ──> 2 ──> 3
    # ^     │     ^     │
    # │     v     │     v
    # └───  4     └────
    g = Graph(5)
    g.add_edge(1, 0)
    g.add_edge(0, 2)
    g.add_edge(2, 1)
    g.add_edge(0, 3)
    g.add_edge(3, 4)

    sccs = g.find_sccs()

    print("Знайдені компоненти SCC:")
    for idx, scc in enumerate(sccs, 1):
        print(f" Компонента {idx}: {scc}")

    # Очікуваний результат:
    # [3, 4] утворюють окремі циклічні або тупикові зони, а [0, 1, 2] утворюють один великий цикл.
    # Відповідно, ми маємо отримати 3 окремі компоненти.


run_scc_tests()
