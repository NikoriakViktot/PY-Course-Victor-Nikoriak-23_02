FROM python:3.12-slim

WORKDIR /app

# Залежності — окремий шар (кешується)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY . .

# Не запускаємо як root
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# uvicorn: 4 worker процеси, 0.0.0.0 для Docker networking
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
