FROM python:3.11-slim

WORKDIR /opt/code/meteo_telegram

RUN pip install --upgrade pip setuptools

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/opt/code/meteo_telegram"

EXPOSE 8000 8501

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
