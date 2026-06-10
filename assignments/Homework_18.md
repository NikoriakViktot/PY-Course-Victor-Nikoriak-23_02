## Task 1: Email Validation за допомогою Class Method


Python

```
import re

class User:
    def __init__(self, email: str):
        # Викликаємо classmethod для валідації перед збереженням
        self.email = self.validate(email)

    @classmethod
    def validate(cls, email: str) -> str:
        """Метод класу для перевірки коректності email."""
        if not isinstance(email, str):
            raise TypeError("Email має бути рядком (str).")
            
        # Простий регулярний вираз для базової перевірки email
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        if not re.match(email_regex, email):
            raise ValueError(f"Некоректний формат email: '{email}'")
            
        return email

# Перевірка роботи Task 1
if __name__ == "__main__":
    try:
        user1 = User("valid.email@example.com")
        print(f"Користувача створено успішно з email: {user1.email}")
        
        # Це викличе помилку
        user2 = User("invalid-email.com")
    except ValueError as e:
        print(f"Помилка валідації: {e}")
```

## Task 2: Взаємозв'язок Boss & Worker (Getters / Setters)

Щоб керувати доступом до атрибутів і не дозволяти додавати що попало напряму, ми використаємо вбудований у Python декоратор `@property` (це найкращий спосіб реалізації геттерів та сеттерів у Python). Також реалізуємо метод автоматичного двостороннього зв'язку: коли робітнику призначають боса, робітник автоматично додається до списку цього боса.

Python

```
class Boss:
    def __init__(self, id_: int, name: str, company: str):
        self.id = id_
        self.name = name
        self.company = company
        self._workers = []  # Захищений атрибут

    @property
    def workers(self) -> list:
        """Геттер для списку робітників."""
        return self._workers

    def add_worker(self, worker) -> None:
        """Метод для безпечного додавання робітника до боса."""
        if not isinstance(worker, Worker):
            raise TypeError("Додати можна лише об'єкт класу Worker!")
        if worker not in self._workers:
            self._workers.append(worker)
            # Якщо у робітника ще не встановлено цього боса, оновлюємо його
            if worker.boss != self:
                worker.boss = self

    def __repr__(self):
        return f"Boss(id={self.id}, name='{self.name}', workers_count={len(self._workers)})"


class Worker:
    def __init__(self, id_: int, name: str, company: str, boss: Boss):
        self.id = id_
        self.name = name
        self.company = company
        self._boss = None  # Захищений атрибут
        self.boss = boss   # Викличе сеттер для перевірки та встановлення

    @property
    def boss(self) -> Boss:
        """Геттер для отримання боса."""
        return self._boss

    @boss.setter
    def boss(self, new_boss: Boss) -> None:
        """Сеттер з валідацією типу даних."""
        if not isinstance(new_boss, Boss):
            raise TypeError("Значення boss має бути екземпляром класу Boss!")
        
        # Якщо бос змінюється, прибираємо робітника у старого боса
        if self._boss and self._boss != new_boss:
            if self in self._boss._workers:
                self._boss._workers.remove(self)
                
        self._boss = new_boss
        # Автоматично додаємо цього робітника до списку нового боса
        if self not in new_boss.workers:
            new_boss.add_worker(self)

    def __repr__(self):
        return f"Worker(id={self.id}, name='{self.name}', boss='{self._boss.name}')"


# Перевірка роботи Task 2
if __name__ == "__main__":
    boss_1 = Boss(1, "Ілон Маск", "SpaceX")
    boss_2 = Boss(2, "Марк Цукерберг", "Meta")
    
    # Створюємо робітника і прив'язуємо до першого боса
    worker_1 = Worker(101, "Олексій", "SpaceX", boss_1)
    
    print("Список робітників Ілона:", boss_1.workers)  # Має містити Олексія
    print("Бос Олексія:", worker_1.boss.name)
    
    # Змінюємо боса через сеттер
    worker_1.boss = boss_2
    
    print("\n--- Після зміни боса ---")
    print("Список робітників Ілона:", boss_1.workers)  # Тепер порожній
    print("Список робітників Марка:", boss_2.workers)  # Тепер містить Олексія
    
    # Спроба підсунути неправильний тип у сеттер
    try:
        worker_1.boss = "Просто якийсь рядок"
    except TypeError as e:
        print(f"\nПеревірка типу спрацювала успішно: {e}")
```

## Task 3: Декоратори типів (`TypeDecorators`)

Для того, щоб методи класу можна було використовувати як декоратори без створення екземпляра класу, ми оголосимо їх як `@staticmethod`. Також використовуємо функцію `functools.wraps`, щоб зберегти оригінальні метадані функцій (назви, докстрінги тощо).

> **Особливість `to_bool`:** Пряме приведення рядка `"False"` до булевого типу через `bool("False")` в Python повертає `True` (бо рядок не порожній). Тому для методу `to_bool` додано логічну перевірку текстового значення рядка.

Python

```
from functools import wraps

class TypeDecorators:
    
    @staticmethod
    def to_int(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return int(result)
        return wrapper

    @staticmethod
    def to_str(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return str(result)
        return wrapper

    @staticmethod
    def to_bool(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Якщо результат є рядком, обробляємо специфічні текстові значення
            if isinstance(result, str):
                return result.strip().lower() in ("true", "1", "yes")
            return bool(result)
        return wrapper

    @staticmethod
    def to_float(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return float(result)
        return wrapper


# Тестування за допомогою твоїх оригінальних функцій:

@TypeDecorators.to_int
def do_nothing(string: str):
    return string

@TypeDecorators.to_bool
def do_something(string: str):
    return string

@TypeDecorators.to_float
def return_number_str(string: str):
    return string


# Перевірка роботи Task 3 через assert
if __name__ == "__main__":
    # Твої оригінальні перевірки (якщо assert мовчить — значить все True)
    assert do_nothing('25') == 25
    assert do_something('True') is True
    assert do_something('False') is False
    
    # Додатковий тест для float
    assert return_number_str('3.14') == 3.14
    
    print("Усі assert-перевірки для декораторів типів пройшли успішно! 🎉")
```