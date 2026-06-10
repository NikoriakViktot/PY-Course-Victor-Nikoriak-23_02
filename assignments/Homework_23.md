### `question1`

Python

```
def question1(first_list: List[int], second_list: List[int]) -> List[int]:
    res: List[int] = []
    for el_first_list in first_list:  # Обертається N разів
        if el_first_list in second_list:  # Оператор 'in' для списку в найгіршому випадку шукає за O(N)
            res.append(el_first_list)
    return res
```

- **Аналіз:** Зовнішній цикл `for` виконується $N$ разів. Всередині нього використовується перевірка `if ... in second_list`. Оскільки `second_list` — це звичайний список (`List`), Python змушений перебирати його елементи один за одним від початку до кінця (лінійний пошук). Тобто сама перевірка займає $O(N)$.
    
- **Складність:** $N \times O(N) =$ **$O(N^2)$**
    

### `question2`

Python

```
def question2(n: int) -> int:
	for _ in range(10):  # Завжди виконується рівно 10 разів
		n **= 3
	return n
```

- **Аналіз:** Цикл виконується рівно 10 разів. Кількість ітерацій абсолютно не залежить від значення змінної `n` (вона може бути 5, а може бути 5 000 000 — цикл все одно зробить 10 кроків). Будь-яка фіксована кількість кроків у Big O констатується як константа.
    
- **Складність:** **$O(1)$** (константна складність)
    

### `question3`

Python

```
def question3(first_list: List[int], second_list: List[int])-> List[int]:
   temp: List[int] = first_list[:]  # Копіювання списку довжиною N займає O(N)
   for el_second_list in second_list:  # Обертається N разів
      flag = False
      for check in temp:  # Внутрішній цикл по списку temp (спочатку довжина N, потім трохи росте) -> O(N)
         if el_second_list == check:
            flag = True
            break
      if not flag:
         temp.append(second_list)
   return temp
```

- **Аналіз:** Тут ми маємо вкладені цикли. Зовнішній цикл іде по `second_list` ($N$ ітерацій). Внутрішній цикл `for check in temp` перебирає елементи копії першого списку. Навіть якщо довжина списку `temp` збільшується, вона залишається пропорційною $N$. Вкладений перебір дає нам квадратичну залежність.
    
- **Складність:** **$O(N^2)$**
    

### `question4`

Python

```
def question4(input_list: List[int]) -> int:
  res: int = 0
  for el in input_list:  # Обертається рівно N разів
    if el > res:
      res = el
  return res
```

- **Аналіз:** Це класичний алгоритм пошуку максимуму в списку. Ми просто один раз проходимо по всьому списку `input_list` довжиною $N$. Всередині циклу виконуються лише базові операції порівняння та присвоєння, які займають $O(1)$.
    
- **Складність:** **$O(N)$** (лінійна складність)
    

### `question5`

Python

```
def question5(n: int) -> List[Tuple[int, int]]:
    res: List[Tuple[int, int]] = []
    for i in range(n):  # Зовнішній цикл виконується n разів
        for j in range(n):  # Внутрішній цикл виконується n разів на кожну ітерацію зовнішнього
            res.append((i, j))
    return res
```

- **Аналіз:** Перед нами класична матриця або таблиця множення. На кожну з $n$ ітерацій зовнішнього циклу припадає $n$ ітерацій внутрішнього. Загальна кількість операцій додавання до списку дорівнює $n \times n = n^2$.
    
- **Складність:** **$O(n^2)$**
    

### `question6`

Python

```
def question6(n: int) -> int:
    while n > 1:
        n /= 2  # На кожному кроці n зменшується вдвічі
    return n
```