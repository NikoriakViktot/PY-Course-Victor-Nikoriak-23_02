def count_words(file_obj):
    text = file_obj.read()
    return len(text.split())
