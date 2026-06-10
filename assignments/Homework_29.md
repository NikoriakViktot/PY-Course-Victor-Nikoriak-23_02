## Task 1: Пошук сильно зв'язаних компонент (Алгоритм Косараджу)

Щоб знайти сильно зв'язані компоненти (Strongly Connected Components — SCC) за допомогою пошуку в глибину (DFS), класичним рішенням є **Алгоритм Косараджу**. Він використовує властивість: якщо розгорнути всі ребра графа назад, топологічний порядок сильно зв'язаних компонент залишиться незмінним, але ми не зможемо "вийти" за межі компоненти під час обходу.

### Логіка алгоритму:

1. Запустити стандартний DFS на початковому графі, щоб зафіксувати час виходу з кожної вершини (додати вершини у стек по мірі завершення їх обробки).
    
2. Створити **інвертований граф** (транспонований), де всі ребра змінюють свій напрямок на протилежний.
    
3. Вилучати вершини зі стеку. Якщо вершина ще не відвідана, запустити на ній DFS, але вже **по інвертованому графу**. Кожен такий запуск виділить рівно одну сильно зв'язану компоненту.
    

### Реалізація (Python)

Python

```
from collections import defaultdict

class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = defaultdict(list)

    def add_edge(self, u, v):
        self.graph[u].append(v)

    # Перший DFS: заповнює стек у порядку завершення обробки вершин
    def _fill_order(self, v, visited, stack):
        visited[v] = True
        for neighbor in self.graph[v]:
            if not visited[neighbor]:
                self._fill_order(neighbor, visited, stack)
        stack.append(v)

    # Другий DFS: обходить інвертований граф та збирає компоненту
    def _dfs_transpose(self, v, visited, component):
        visited[v] = True
        component.append(v)
        for neighbor in self.transpose_graph[v]:
            if not visited[neighbor]:
                self._dfs_transpose(neighbor, visited, component)

    # Функція транспонування (інверсії) графа
    def _get_transpose(self):
        g_rev = defaultdict(list)
        for node in self.graph:
            for neighbor in self.graph[node]:
                g_rev[neighbor].append(node)
        return g_rev

    # Головний метод пошуку SCC
    def find_sccs(self):
        stack = []
        visited = [False] * self.V

        # 1. Заповнюємо стек за часом виходу
        for i in range(self.V):
            if not visited[i]:
                self._fill_order(i, visited, stack)

        # 2. Інвертуємо граф
        self.transpose_graph = self._get_transpose()

        # 3. Скидаємо масив відвіданих вершин для другого проходу
        visited = [False] * self.V
        sccs = []

        # Обробляємо вершини у порядку, заданому стеком
        while stack:
            i = stack.pop()
            if not visited[i]:
                component = []
                self._dfs_transpose(i, visited, component)
                sccs.append(component)
        
        return sccs

# Приклад використання:
g = Graph(5)
g.add_edge(1, 0)
g.add_edge(0, 2)
g.add_edge(2, 1)
g.add_edge(0, 3)
g.add_edge(3, 4)

print("Strongly Connected Components:")
print(g.find_sccs())
```

## Task 2: All-Pairs Shortest Path за допомогою BFS

Пошук у ширину (BFS) знаходить найкоротший шлях від однієї вершини до всіх інших за умови, що граф **незважений** (тобто всі ребра мають однакову вагу/довжину, наприклад 1).

Щоб вирішити задачу _All-Pairs Shortest Path_ (найкоротші шляхи для всіх пар вершин), нам потрібно просто запустити BFS **для кожної вершини графа як для стартової**.

### Реалізація (Python)

Python

```
from collections import deque

def all_pairs_shortest_path_bfs(graph_dict, num_vertices):
    # Матриця суміжності для збереження відстаней. 
    # Спочатку заповнюємо її нескінченністю (float('inf')), а відстань від вершини до самої себе — 0.
    distance_matrix = {u: {v: float('inf') for v in graph_dict} for u in graph_dict}
    
    # Функція BFS для конкретної стартової вершини
    def bfs(start_vertex):
        queue = deque([start_vertex])
        distance_matrix[start_vertex][start_vertex] = 0
        
        while queue:
            current = queue.popleft()
            current_dist = distance_matrix[start_vertex][current]
            
            for neighbor in graph_dict[current]:
                # Якщо сусіда ще не відвідували (відстань нескінченна)
                if distance_matrix[start_vertex][neighbor] == float('inf'):
                    distance_matrix[start_vertex][neighbor] = current_dist + 1
                    queue.append(neighbor)

    # Запускаємо BFS з кожної вершини
    for vertex in graph_dict:
        bfs(vertex)
        
    return distance_matrix

# Приклад графа (представлений списком суміжності)
# Ключ — вершина, значення — список її сусідів
graph = {
    0: [1, 2],
    1: [0, 3],
    2: [0, 3, 4],
    3: [1, 2, 4],
    4: [2, 3]
}

matrix = all_pairs_shortest_path_bfs(graph, len(graph))

# Красиве виведення матриці відстаней
print("Матриця найкоротших відстаней між усіма парами:")
for start in sorted(matrix.keys()):
    row = [f"{matrix[start][end]}" if matrix[start][end] != float('inf') else "∞" for end in sorted(matrix[start].keys())]
    print(f"Від вершини {start}: {row}")
```