def sample_function():
    first_number = 10
    second_number = 20
    result = first_number + second_number
    return result


print(sample_function.__code__.co_nlocals)
