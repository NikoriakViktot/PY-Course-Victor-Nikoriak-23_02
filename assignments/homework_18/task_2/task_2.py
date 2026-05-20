class Boss:
    def __init__(self, id_: int, name: str, company: str):
        self.id = id_
        self.name = name
        self.company = company
        self._workers = []  # Приватный список

    @property
    def workers(self):
        return self._workers

    @workers.setter
    def workers(self, value):
        raise AttributeError("Нельзя изменять список рабочих напрямую. Используйте метод add_worker.")

    def add_worker(self, worker):
        if isinstance(worker, Worker):
            if worker not in self._workers:
                self._workers.append(worker)
                worker.boss = self
        else:
            raise ValueError("Добавить можно только экземпляр класса Worker")


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
            raise ValueError("Boss должен быть экземпляром класса Boss")


        if self._boss and self._boss != new_boss:
            if self in self._boss._workers:
                self._boss._workers.remove(self)

        self._boss = new_boss

        if self not in new_boss.workers:
            new_boss.add_worker(self)
