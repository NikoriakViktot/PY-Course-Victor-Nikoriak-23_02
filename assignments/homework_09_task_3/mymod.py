def count_lines(filename):
    with open(filename, 'r') as f:
        print(f"Кількість рядків у файлі: {len(f.readlines())}")

def count_chars(filename):
    with open(filename, 'r') as f:
        print(f"Кількість символів у файлі: {len(f.read())}")

def test(name_file):
    count_lines(name_file)
    count_chars(name_file)
