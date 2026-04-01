class CustomException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

        with open('logs.txt', 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
