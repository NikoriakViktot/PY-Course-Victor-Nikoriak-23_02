# Task 2
# Розширити сервер Echo, який повертає клієнту дані, зашифровані за допомогою алгоритму
# шифрування Цезаря з використанням певного ключа, отриманого від клієнта.
def caesar_cipher(text, key):
    """Шифрує текст шифром Цезаря з вказаним ключем зсуву (для англійського алфавіту)."""
    result = []
    for char in text:
        if char.isalpha():
            # Визначаємо початкову точку в залежності від регістру (A або a)
            start = ord('A') if char.isupper() else ord('a')
            # Формула зсуву в межах 26 літер алфавіту
            new_char = chr(start + (ord(char) - start + key) % 26)
            result.append(new_char)
        else:
            result.append(char)
    return "".join(result)