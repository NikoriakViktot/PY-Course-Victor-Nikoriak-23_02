import pytest

try:
    from file_context_manager import FileContextManager
    from text_utils import count_words
except ImportError:
    from lesson_21.file_context_manager import FileContextManager
    from lesson_21.text_utils import count_words


@pytest.fixture
def file_obj(tmp_path):
    file_path = tmp_path / "text.txt"
    file_path.write_text("Python context manager test", encoding="utf-8")

    with FileContextManager(file_path, "r") as file:
        yield file


def test_count_words(file_obj):
    assert count_words(file_obj) == 4
