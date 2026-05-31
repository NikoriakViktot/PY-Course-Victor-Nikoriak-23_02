import pytest


def process_file(file_obj):
    return file_obj.read().upper()


@pytest.fixture
def file_fixture():
    filename = "fixture_test.txt"

    with open(filename, "w") as f:
        f.write("hello fixture")

    f = open(filename, "r")
    yield f
    f.close()


def test_process_file(file_fixture):
    result = process_file(file_fixture)
    assert result == "HELLO FIXTURE"