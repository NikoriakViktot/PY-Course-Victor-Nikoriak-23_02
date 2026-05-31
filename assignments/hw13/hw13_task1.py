# Homework 13
# Task 1
# Count number of local variables in a function

def count_local_variables():
    # Create some local variables
    a = 10
    b = 20
    c = a + b
    d = "hello"

    # locals() returns a dictionary of local variables
    # len() counts how many variables are inside
    return len(locals())


# Function call
print("Number of local variables:", count_local_variables())