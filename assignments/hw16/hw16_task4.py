class CustomException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

        # запис у файл
        with open("logs.txt", "a") as file:
            file.write(msg + "\n")


# Example usage
try:
    raise CustomException("Something went wrong!")
except CustomException as e:
    print(e)