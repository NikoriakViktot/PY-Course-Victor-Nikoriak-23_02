# Task 1
movie = input('What is your favorite movie? ')
def favorite_movie(movie):
    print (f'My favorite movie is named {movie}')

favorite_movie(movie)

# Task 2
def make_country (country, capital):
    country_dict = {
        'name': country,
        'capital': capital,
    }
    return country_dict

result = make_country('Ukraine', 'Kyiv')
print(result)

# Task 3
def make_operation (operator, *args):
    if operator == '+':
        return sum(args)
    elif operator == '-':
        num_oper = args[0]
        for num in args[1:]:
            num_oper -= num
        return num_oper
    elif operator == '*':
        num_oper = args[0]
        for num in args[1:]:
            num_oper *= num
        return num_oper
    else:
        return('Error')

result = make_operation('+', 7, 7, 2)
# result = make_operation('-', 5, 5, -10, -20)
# result = make_operation('*', 7, 6)
print(result)