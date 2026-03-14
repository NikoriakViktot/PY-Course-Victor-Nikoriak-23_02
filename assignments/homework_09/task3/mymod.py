def count_lines(name):
    with open(name, 'r', encoding='utf-8') as file:
        return len(file.readlines())

def count_chars(name):
    with open(name, 'r', encoding='utf-8') as file:
        return len(file.read())

def test(name):
    lines = count_lines(name)
    chars = count_chars(name)
    print(f"Файл: {name} | Рядків: {lines} | Символів: {chars}")

if __name__ == "__main__":
    test("mymod.py")