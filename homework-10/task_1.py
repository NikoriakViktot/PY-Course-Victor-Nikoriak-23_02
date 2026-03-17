def oops():
    raise IndexError('Index error')

try:
    oops()
except IndexError:
    print('Зловили Index error')
    pass


def oops():
    raise KeyError('KeyError')

try:
    oops()
except IndexError:
    print('Зловили Index error')
# не зловить KeyError так як він не прописан у except