class Boss:
    def __init__(self, id_: int, name: str, company: str):
        self.id = id_
        self.name = name
        self.company = company
        self._workers = []

    @property
    def workers(self):
        return self._workers

    def add_worker(self, worker):
        if isinstance(worker, Worker):
            worker.boss = self
            self._workers.append(worker)
        else:
            raise TypeError("Only Worker instances can be added")


class Worker:
    def __init__(self, id_: int, name: str, company: str, boss):
        self.id = id_
        self.name = name
        self.company = company
        self._boss = None
        self.boss = boss

    @property
    def boss(self):
        return self._boss

    @boss.setter
    def boss(self, value):
        if isinstance(value, Boss):
            self._boss = value
            if self not in value.workers:
                value._workers.append(self)
        else:
            raise TypeError("Boss must be an instance of Boss class")


# Приклад використання
b = Boss(1, "Alice", "TechCorp")
w1 = Worker(101, "Bob", "TechCorp", b)
w2 = Worker(102, "Charlie", "TechCorp", b)

print([w.name for w in b.workers])  # ['Bob', 'Charlie']