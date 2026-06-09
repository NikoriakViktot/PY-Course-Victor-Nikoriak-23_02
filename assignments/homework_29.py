# Task 1
# Modify the 'depth-first search' to produce strongly connected components (Strongly Connected Components ).
# Модифікуйте алгоритм «пошуку в глибину» таким чином, щоб отримати сильно зв’язані компоненти (Strongly Connected Components).
from collections import defaultdict
class Graph:
    def __init__(self, vertices):
        self.V = vertices  # Кількість вершин
        self.graph = defaultdict(list)  # Словник для збереження списку суміжності
    def add_edge(self, u, v):
        """Додавання орієнтованого ребра з u в v."""
        self.graph[u].append(v)
    def _fill_order(self, v, visited, stack):
        """Перший DFS: заповнює стек вершинами в порядку завершення їх обробки."""
        visited[v] = True
        for neighbor in self.graph[v]:
            if not visited[neighbor]:
                self._fill_order(neighbor, visited, stack)
        # Додаємо вершину в стек після обробки всіх її сусідів
        stack.append(v)
    def _get_transpose(self):
        """Створює інвертований (транспонований) граф."""
        g_rev = Graph(self.V)
        for node in self.graph:
            for neighbor in self.graph[node]:
                g_rev.add_edge(neighbor, node)
        return g_rev
    def _dfs_scc(self, v, visited, current_scc):
        """Другий DFS: обходить інвертований граф та збирає елементи однієї SCC."""
        visited[v] = True
        current_scc.append(v)
        for neighbor in self.graph[v]:
            if not visited[neighbor]:
                self._dfs_scc(neighbor, visited, current_scc)
    def find_sccs(self):
        """Основна функція для пошуку всіх сильно зв'язаних компонент."""
        stack = []
        visited = [False] * self.V
        # 1. Запускаємо перший DFS для всіх невідвіданих вершин
        for i in range(self.V):
            if not visited[i]:
                self._fill_order(i, visited, stack)
        # 2. Отримуємо транспонований граф
        g_rev = self._get_transpose()
        # 3. Скидаємо масив відвіданих вершин для другого DFS
        visited = [False] * self.V
        all_sccs = []
        # Обробляємо вершини у порядку, заданому стеком (з кінця)
        while stack:
            v = stack.pop()
            if not visited[v]:
                current_scc = []
                # Запускаємо DFS на інвертованому графі
                g_rev._dfs_scc(v, visited, current_scc)
                all_sccs.append(current_scc)
        return all_sccs
# Приклад використання:
if __name__ == "__main__":
    # Створюємо граф з 5 вершинами (0, 1, 2, 3, 4)
    g = Graph(5)
    g.add_edge(1, 0)
    g.add_edge(0, 2)
    g.add_edge(2, 1)
    g.add_edge(0, 3)
    g.add_edge(3, 4)
    sccs = g.find_sccs()
    print("Знайдені сильно зв'язані компоненти (SCC):")
    for idx, component in enumerate(sccs, 1):
        print(f"Компонента {idx}: {component}")

# Task 2
# Використовуючи обхід в ширину, напишіть алгоритм, який зможе визначити найкоротший шлях від
# кожної вершини до кожної іншої вершини. Це завдання називається задачею про найкоротші шляхи
# між усіма парами вершин.
from collections import deque
def all_pairs_shortest_paths_bfs(graph_dict):
    """
    Знаходить найкоротші шляхи між усіма парами вершин за допомогою BFS.
    graph_dict: словник суміжності, де ключі — вершини, а значення — списки сусідів.
    """
    # Отримуємо відсортований список усіх унікальних вершин графа
    vertices = sorted(list(graph_dict.keys()))
    num_vertices = len(vertices)
    # Створюємо словник для швидкого мапінгу назви/id вершини в індекс матриці
    v_to_idx = {v: i for i, v in enumerate(vertices)}
    # Ініціалізуємо матрицю відстаней значеннями нескінченності
    # Відстань від вершини до самої себе дорівнює 0
    distance_matrix = [[float('inf')] * num_vertices for _ in range(num_vertices)]
    for i in range(num_vertices):
        distance_matrix[i][i] = 0
    # Запускаємо окремий BFS для кожної вершини графа
    for start_vertex in vertices:
        start_idx = v_to_idx[start_vertex]
        # Черга зберігає кортежі: (поточна_вершина, поточна_відстань)
        queue = deque([(start_vertex, 0)])
        # Набір для відстеження відвіданих вершин у поточному запуску BFS
        visited = {start_vertex}
        while queue:
            current_vertex, current_dist = queue.popleft()
            # Оновлюємо відстань у підсумковій матриці
            curr_idx = v_to_idx[current_vertex]
            distance_matrix[start_idx][curr_idx] = current_dist
            # Перебираємо сусідів поточної вершини
            for neighbor in graph_dict.get(current_vertex, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, current_dist + 1))
    return vertices, distance_matrix
# Приклад використання:
if __name__ == "__main__":
    # Задаємо орієнтований граф у вигляді списку суміжності
    # Граф містить 4 вершини: 0, 1, 2, 3
    custom_graph = {
        0: [1, 2],
        1: [3],
        2: [1, 3],
        3: [0]
    }
    labels, matrix = all_pairs_shortest_paths_bfs(custom_graph)
    # Красиве виведення результатів
    print("Матриця найкоротших шляхів між усіма парами вершин:")
    # Виводимо заголовок стовпців
    print("    " + "  ".join(f"[{v}]" for v in labels))
    for i, row in enumerate(matrix):
        row_str = "  ".join(f"{str(val):>3}" for val in row)
        print(f"[{labels[i]}]  {row_str}")