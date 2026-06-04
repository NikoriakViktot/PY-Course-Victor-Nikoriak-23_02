from collections import deque

def find_all_distances(graph):
    all_results = {}

    for start_node in graph:
        distances = {node: "inf" for node in graph}
        distances[start_node] = 0

        queue = deque([start_node])

        while queue:
            current = queue.popleft()

            for neighbor in graph[current]:
                if distances[neighbor] == "inf":
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)

        all_results[start_node] = distances

    return all_results


#Приклад графа (словник суміжності)
my_graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'D'],
    'D': ['B', 'C', 'E'],
    'E': ['D']
}

#Виконання
results = find_all_distances(my_graph)

#Гарний вивід
for start, targets in results.items():
    print(f"Від {start}: {targets}")