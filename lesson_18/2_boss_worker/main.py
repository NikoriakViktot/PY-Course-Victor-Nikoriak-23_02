class Boss:
    def __init__(self, id_: int, name: str, company: str):
        self.id = id_
        self.name = name
        self.company = company
        self._workers = []

    @property
    def workers(self):
        return self._workers.copy()

    def add_worker(self, worker):
        if not isinstance(worker, Worker):
            raise ValueError("Worker must be an instance of Worker class")

        if worker not in self._workers:
            self._workers.append(worker)

        if worker.boss is not self:
            worker.boss = self

    def remove_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)


class Worker:
    def __init__(self, id_: int, name: str, company: str, boss: Boss):
        self.id = id_
        self.name = name
        self.company = company
        self._boss = None
        self.boss = boss

    @property
    def boss(self):
        return self._boss

    @boss.setter
    def boss(self, new_boss):
        if not isinstance(new_boss, Boss):
            raise ValueError("Boss must be an instance of Boss class")

        if self._boss is not None:
            self._boss.remove_worker(self)

        self._boss = new_boss

        if self not in new_boss._workers:
            new_boss._workers.append(self)


boss_1 = Boss(1, "John", "Google")
boss_2 = Boss(2, "Kate", "Microsoft")

worker = Worker(1, "Bob", "Google", boss_1)

assert worker.boss == boss_1
assert worker in boss_1.workers

worker.boss = boss_2

assert worker.boss == boss_2
assert worker not in boss_1.workers
assert worker in boss_2.workers

print("All assertions passed")
