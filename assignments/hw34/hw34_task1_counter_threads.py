import threading

counter = 0
rounds = 100000

class Counter(threading.Thread):
    def run(self):
        global counter
        for _ in range(rounds):
            counter += 1


if __name__ == "__main__":
    t1 = Counter()
    t2 = Counter()

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("Final counter value:", counter)