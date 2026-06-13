def dfs_fill(graph, v, visited, stack):
    visited.add(v)

    for neigh in graph[v]:
        if neigh not in visited:
            dfs_fill(graph, neigh, visited, stack)
    stack.append(v)


def reverse_graph(graph):
    rev = {v: [] for v in graph}

    for v in graph:
        for neigh in graph[v]:
            rev[neigh].append(v)
    return rev


def dfs_collect(graph, v, visited, component):
    visited.add(v)
    component.append(v)

    for neigh in graph[v]:
        if neigh not in visited:
            dfs_collect(graph, neigh, visited, component)


def kosaraju(graph):
    stack = []
    visited = set()

    for v in graph:
        if v not in visited:
            dfs_fill(graph, v, visited, stack)

    rev = reverse_graph(graph)
    visited.clear()
    scc = []

    while stack:
        v = stack.pop()

        if v not in visited:
            component = []
            dfs_collect(rev, v, visited, component)
            scc.append(component)

    return scc