FROM python:3.12-slim

WORKDIR /app

# Встановлюємо залежності окремим шаром (кешується якщо requirements не змінився)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код
COPY . .

CMD ["python", "main.py"]
