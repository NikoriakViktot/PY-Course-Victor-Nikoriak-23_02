# Homework 13
# Task 2
# Access a function inside a function

def outer_function():
    # Inner function
    def inner_function():
        return "Hello from inner function!"

    # Return the inner function (not calling it yet)
    return inner_function


# Get the inner function
result_function = outer_function()

# Call the returned function
print(result_function())