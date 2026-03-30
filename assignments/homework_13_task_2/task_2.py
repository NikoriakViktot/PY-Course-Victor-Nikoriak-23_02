def greeting():
    your_name = input("Enter your name: ")

    def hello(name):
        print("Hello, " + your_name + "!")

    return hello(your_name)


greeting()
