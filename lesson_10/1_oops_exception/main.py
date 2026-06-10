def oops():
    raise IndexError("Index error was raised")


def catch_oops():
    try:
        oops()
    except IndexError as error:
        print(f"Caught an IndexError: {error}")


catch_oops()
