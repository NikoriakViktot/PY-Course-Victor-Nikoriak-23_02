class CustomException(Exception):
    def __init__(self, msg):
        super().__init__(msg)  # виклик конструктора базового класу Exception
        # запис повідомлення у файл logs.txt
        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
def divide(a, b):
    if b == 0:
        raise CustomException("Ділення на нуль неможливе!")
    return a / b


try:
    result = divide(10, 0)
except CustomException as e:
    print("Помилка:", e)
