def oops():
    raise IndexError("This is an IndexError")


def call_oops():
    try:
        oops()
    except IndexError as e:
        print("Caught:", e)


call_oops()