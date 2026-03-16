def get_string_edges(text):
    # Перевіряємо довжину рядка за допомогою len()
    if len(text) < 2:
        return ""  # Повертаємо порожній рядок, якщо символів замало

    # Використовуємо зрізи:
    # text[:2] — перші два символи (індекси 0 та 1)
    # text[-2:] — останні два символи (від другого з кінця до кінця)
    return text[:2] + text[-2:]

# Тестування
test_samples = ['helloworld', 'my', 'x']

for sample in test_samples:
    result = get_string_edges(sample)
    print(f"Sample String: '{sample}' -> Result: '{result}'")



phone_number = input("Введіть номер телефону (10 цифр): ")

# Перевірка: довжина має бути рівно 10 ТА всі символи мають бути цифрами
if len(phone_number) == 10 and phone_number.isdigit():
    print("Номер правильний! Дякуємо.")
else:
    print("Помилка: номер має містити рівно 10 цифр без зайвих символів.")


# Задаємо приклад
question = "Скільки буде 7 помножити на 8?"
correct_answer = 56

print(question)
user_input = input("Ваша відповідь: ")

# Перетворюємо введення в число для порівняння
if int(user_input) == correct_answer:
    print("Правильно! Ви чудовий математик.")
else:
    print(f"На жаль, ні. Правильна відповідь: {correct_answer}.")


stored_name = "yan" # ваше ім'я в нижньому регістрі
user_name = input("Як вас звати? ")

# Перетворюємо введене ім'я в нижній регістр перед порівнянням
if user_name.lower() == stored_name:
    print(True)
    print(f"Привіт, {user_name}! Радий тебе бачити.")
else:
    print(False)
    print("Вибачте, ім'я не збігається.")
