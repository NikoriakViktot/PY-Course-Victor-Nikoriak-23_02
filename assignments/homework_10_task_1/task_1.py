import mod_oops

def catch_error():
    try:
        mod_oops.oops()
    except IndexError:
        print("Index Error to catch")
    except KeyError:
        print("KeyError to catch")

catch_error()
