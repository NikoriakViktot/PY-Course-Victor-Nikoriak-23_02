# write_file.py

def write_to_file():
    with open("myfile.txt", "w", encoding="utf-8") as file:
        file.write("Hello file world!\n")


if __name__ == "__main__":
    write_to_file()
    print("File written successfully.")