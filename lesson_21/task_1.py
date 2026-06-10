from file_context_manager import FileContextManager


with FileContextManager("example.txt", "w") as file:
    file.write("Hello context manager!\n")

with FileContextManager("example.txt", "r") as file:
    print(file.read())

print(f"Opened files: {FileContextManager.open_counter}")
print(f"Closed files: {FileContextManager.close_counter}")
