import threading

counter = 0
rounds = 100000


class Counter(threading.Thread):

    def run(self):
        global counter
        for _ in range(rounds):
            counter += 1


for i in range(1, 4):
    counter = 0

    thread1 = Counter()
    thread2 = Counter()
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    print(f"Запуск №{i}: Фінальне значення counter = {counter}")
