def outer_function():
    def inner_function():
        return "Hello from inner function"

    return inner_function


function = outer_function()
print(function())
