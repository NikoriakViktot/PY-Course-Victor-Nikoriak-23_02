# create_file.py
with open("myfile.txt", "w") as f:
    f.write("Hello file world!\n")
    f.write("This is a new file created by Python.\n")

    # read_file.py
with open("myfile.txt", "r") as f:
    content = f.read()
    print(content)