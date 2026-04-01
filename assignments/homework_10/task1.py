
# first part with list

def oops():
    test_list = [1, 2]
    print(test_list[10])

def call_oops():
    try:
        oops()
    except IndexError:
        print("An error with the list was caught!")

call_oops()

# second part with dict

# try:
#     def dict_oops():
#         my_dict = {1: 123, 2: 234, 3: 345}
#         print(my_dict[10])
# except IndexError as inst:
#     print(f"Oops! Something went wrong. Details: {inst.args}")

# dict_oops()

#через те, що ми вказали не той тип помилки, то except не спрацює.
# Виправити можна через Exception


try:
    def dict_oops():
        my_dict = {1: 123, 2: 234, 3: 345}
        print(my_dict[10])
    dict_oops()
except Exception as inst:
    print(f"Oops! Something went wrong. Details: {inst.args}")