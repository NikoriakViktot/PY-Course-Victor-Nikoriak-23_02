from threading import Lock, Thread


counter = 0
rounds = 100_000


class Counter(Thread):
    def run(self):
        global counter

        for _ in range(rounds):
            counter += 1


class SafeCounter(Thread):
    lock = Lock()

    def run(self):
        global counter

        for _ in range(rounds):
            with self.lock:
                counter += 1


def run_threads(thread_class):
    global counter

    counter = 0

    first_thread = thread_class()
    second_thread = thread_class()

    first_thread.start()
    second_thread.start()

    first_thread.join()
    second_thread.join()

    return counter


if __name__ == "__main__":
    unsafe_result = run_threads(Counter)
    safe_result = run_threads(SafeCounter)

    print(f"Unsafe counter result: {unsafe_result}")
    print(f"Safe counter result: {safe_result}")
    print(f"Expected result: {rounds * 2}")

    assert safe_result == rounds * 2
