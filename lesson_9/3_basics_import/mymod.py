import os


def count_lines(name):
    with open(name, "r", encoding="utf-8") as file:
        lines = file.readlines()
        return len(lines)


def count_chars(name):
    with open(name, "r", encoding="utf-8") as file:
        text = file.read()
        return len(text)


def test(name):
    if not os.path.exists(name):
        print(f"File '{name}' does not exist")
        return

    lines = count_lines(name)
    chars = count_chars(name)

    print(f"File: {name}")
    print(f"Lines: {lines}")
    print(f"Characters: {chars}")