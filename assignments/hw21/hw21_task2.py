import os
import pytest
from file_context_manager import FileContextManager


def test_file_write_and_read():
    filename = "test.txt"

    with FileContextManager(filename, "w") as f:
        f.write("hello")

    with FileContextManager(filename, "r") as f:
        content = f.read()

    assert content == "hello"

    os.remove(filename)


def test_counter():
    filename = "test_counter.txt"

    with FileContextManager(filename, "w") as f:
        f.write("1")

    assert FileContextManager.counter >= 1

    os.remove(filename)


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        with FileContextManager("no_file.txt", "r") as f:
            f.read()


def test_exception_inside_with():
    filename = "test_exception.txt"

    with pytest.raises(ValueError):
        with FileContextManager(filename, "w") as f:
            f.write("data")
            raise ValueError("error inside with")

    os.remove(filename)