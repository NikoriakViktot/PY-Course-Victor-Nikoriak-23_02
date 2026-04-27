def find_sccs(n, edges):
    adj = [[] for _ in range(n)]
    adj_rev = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj_rev[v].append(u)

    stack = []
    visited = [False] * n

    def fill_order(u):
        visited[u] = True
        for v in adj[u]:
            if not visited[v]: fill_order(v)
        stack.append(u)

    def collect_scc(u, component):
        visited[u] = True
        component.append(u)
        for v in adj_rev[u]:
            if not visited[v]: collect_scc(v, component)

    for i in range(n):
        if not visited[i]: fill_order(i)

    visited = [False] * n
    sccs = []
    while stack:
        u = stack.pop()
        if not visited[u]:
            component = []
            collect_scc(u, component)
            sccs.append(component)

    return sccs


# Приклад
graph_edges = [(0, 1), (1, 2), (2, 0), (3, 4)]
print(find_sccs(5, graph_edges))