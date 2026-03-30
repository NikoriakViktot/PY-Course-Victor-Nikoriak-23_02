# read_file.py

def read_from_file():
    try:
        with open("myfile.txt", "r", encoding="utf-8") as file:
            content = file.read()
            print("File content:")
            print(content)
    except FileNotFoundError:
        print("File not found. Please run write_file.py first.")


if __name__ == "__main__":
    read_from_file()