def with_index(iterable, start = 0):
    ind = start
    for item in iterable:
        yield ind, item
        ind += 1



