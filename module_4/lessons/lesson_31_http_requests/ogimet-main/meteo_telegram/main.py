"""
Meteo Telegram API — FastAPI backend для навчального demo

Endpoints:
    POST /download_telegrams     — завантажити телеграми з ogimet.com
    POST /filter_telegrams/      — фільтрувати за критеріями
    GET  /telegram/{col}/{id}    — отримати одну телеграму
    PUT  /telegram/{col}/{id}    — оновити поле телеграми
    DELETE /telegram/{col}/{id}  — видалити телеграму

Запуск:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    Swagger UI: http://localhost:8000/docs
"""
import os
import math
import logging
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel, Field
from pymongo import MongoClient

from mongo_db.mongo_tools import MongoDb
from telegram_decode.telegram_factory import TelegramFactory

logging.basicConfig(
    level=logging.ERROR,
    filename="app.log",
    filemode="a",
    format="%(name)s - %(levelname)s - %(message)s",
)

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# MONGO_URL:
#   В Docker:  задається через env var у docker-compose.yaml
#   Локально:  mongodb://localhost:27017/
# ─────────────────────────────────────────────────────────────────────────────
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL)
db = client["telegram"]


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY: очищення значень несумісних з JSON (NaN, Inf)
# ─────────────────────────────────────────────────────────────────────────────
def clean_data(data):
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, float) and (
        data == float("inf") or data == float("-inf") or data != data
    ):
        return None
    return data


def clean_nan_values(data):
    if isinstance(data, dict):
        return {k: clean_nan_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_nan_values(i) for i in data]
    elif isinstance(data, float) and math.isnan(data):
        return None
    return data


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS LOGIC: завантаження та збереження телеграм
# Ця функція викликається вручну через endpoint /download_telegrams
# (замість автоматичного APScheduler — для навчального demo)
# ─────────────────────────────────────────────────────────────────────────────
def download_and_process_telegrams(country_code: str):
    processor = TelegramFactory.create_processor(country_code=country_code)
    df_result = processor.process_telegrams()

    documents = df_result.to_dict("records")
    db_manager = MongoDb().db_manager

    for document in documents:
        id_telegram = document["id_telegram"]
        data_for_mongo = {"id_telegram": id_telegram, "data": document}
        data_for_mongo["data"].pop("id_telegram", None)
        collection = db_manager.get_or_create_collection(country_code)
        db_manager.insert_or_update_document(collection, data_for_mongo)

    print(f"Processed {len(documents)} telegrams for '{country_code}'")


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODEL: фільтр для POST /filter_telegrams/
# ─────────────────────────────────────────────────────────────────────────────
class TelegramFilter(BaseModel):
    """
    Параметри фільтрації телеграм.
    Всі поля опціональні — вкажи тільки те, що потрібно.
    """
    country_code: Optional[str] = Field(None, description="'ua', 'bel', 'rus'")
    station_id: Optional[str] = Field(None, description="WMO код станції")
    date: Optional[str] = Field(None, description="Дата YYYYMMDD")
    date_start: Optional[str] = Field(None, description="Початкова дата YYYYMMDD")
    date_end: Optional[str] = Field(None, description="Кінцева дата YYYYMMDD")
    hour: Optional[int] = Field(None, description="Година 0-23")
    temperature: Optional[float] = Field(None, description="Температура °C")
    dew_point_temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    wind_dir: Optional[float] = None
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None
    sea_level_pressure: Optional[float] = None
    maximum_temperature: Optional[float] = None
    minimum_temperature: Optional[float] = None
    precipitation_s1: Optional[float] = None
    precipitation_s3: Optional[float] = None
    pressure_tendency: Optional[float] = None
    present_weather: Optional[str] = None
    past_weather_1: Optional[str] = None
    past_weather_2: Optional[str] = None
    sunshine: Optional[float] = None
    ground_state_snow: Optional[str] = None
    ground_state: Optional[str] = None
    fields_to_return: Optional[List[str]] = Field(
        None, description="Які поля повернути (порожньо = всі)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Meteo Telegram API",
    description="Навчальний REST API — Урок 31: HTTP & requests",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── POST /download_telegrams ──────────────────────────────────────────────
@app.post("/download_telegrams", summary="Завантажити телеграми з ogimet.com")
def download_telegrams(country_code: str):
    """
    Запускає синхронне завантаження метеорологічних телеграм.

    **Увага для студентів:** цей endpoint є blocking — Python чекає поки всі
    35+ станцій завантажаться. Це може зайняти 1-5 хвилин.

    Приклад:
    ```bash
    curl -X POST "http://localhost:8000/download_telegrams?country_code=ua"
    ```
    """
    try:
        download_and_process_telegrams(country_code)
        return {"message": f"Successfully downloaded telegrams for '{country_code}'"}
    except Exception as e:
        logging.error(f"download_telegrams error: {e}")
        return {"error": str(e)}


# ─── GET /telegram/{collection}/{id} ─────────────────────────────────────
@app.get(
    "/telegram/{collection_name}/{id_teleg}",
    summary="Отримати телеграму по ID",
)
def get_data_from_collection(collection_name: str, id_teleg: str):
    """
    Повертає одну телеграму за її унікальним ID.

    ID формат: `{station_id}{year}{month}{day}{hour}`
    Приклад: `3450420249218` = станція 34504, 2024-09-02 18:00

    ```bash
    curl http://localhost:8000/telegram/ua/3450420249218
    ```
    """
    collection = db[collection_name]
    data = collection.find_one({"id_telegram": id_teleg}, {"_id": False})
    if data is None:
        return {"message": "Дані за цим ID не знайдено"}
    return JSONResponse(content=clean_data(data))


# ─── DELETE /telegram/{collection}/{id} ──────────────────────────────────
@app.delete(
    "/telegram/{collection_name}/{id_teleg}",
    summary="Видалити телеграму",
)
def delete_data_from_collection(collection_name: str, id_teleg: str):
    """
    Видаляє телеграму з MongoDB.

    ```bash
    curl -X DELETE http://localhost:8000/telegram/ua/3450420249218
    ```
    """
    collection = db[collection_name]
    result = collection.delete_one({"id_telegram": id_teleg})
    if result.deleted_count == 1:
        return {"message": "Запис успішно видалено"}
    return {"message": "Запис з таким ID не знайдено"}


# ─── PUT /telegram/{collection}/{id} ─────────────────────────────────────
@app.put(
    "/telegram/{collection_name}/{id_teleg}",
    summary="Оновити поля телеграми",
)
def update_data_in_collection(
    collection_name: str, id_teleg: str, dynamic_updates: dict
):
    """
    Оновлює довільні поля документу.

    Передай JSON об'єкт з полями для оновлення:
    ```bash
    curl -X PUT http://localhost:8000/telegram/ua/3450420249218 \\
         -H "Content-Type: application/json" \\
         -d '{"temperature": 25.5}'
    ```
    """
    collection = db[collection_name]
    update_fields = {f"data.{k}": v for k, v in dynamic_updates.items()}
    result = collection.update_one(
        {"id_telegram": id_teleg},
        {"$set": update_fields},
    )
    if result.modified_count == 1:
        return {"message": "Запис успішно оновлено"}
    return {"message": "Запис не знайдено або значення не змінилось"}


# ─── POST /filter_telegrams/ ─────────────────────────────────────────────
@app.post("/filter_telegrams/", summary="Фільтрувати телеграми")
def filter_telegrams(filter: TelegramFilter):
    """
    Повертає телеграми що відповідають фільтру.

    Якщо `country_code` не вказано — шукає у всіх колекціях.
    Якщо `fields_to_return` не вказано — повертає всі поля.

    ```bash
    curl -X POST http://localhost:8000/filter_telegrams/ \\
         -H "Content-Type: application/json" \\
         -d '{"country_code": "ua", "station_id": "33345"}'
    ```
    """
    collections_to_query = (
        [filter.country_code] if filter.country_code else db.list_collection_names()
    )
    results = []

    for collection_name in collections_to_query:
        collection = db[collection_name]
        query = {}

        if filter.station_id:
            query["data.station_id"] = filter.station_id

        if filter.date and len(filter.date) >= 8:
            try:
                query["data.year"] = int(filter.date[:4])
                query["data.month"] = int(filter.date[4:6])
                query["data.day"] = int(filter.date[6:8])
            except ValueError:
                continue

        if filter.hour is not None:
            query["data.hour"] = filter.hour

        projection = {"_id": False}
        if filter.fields_to_return:
            for field in filter.fields_to_return:
                projection[f"data.{field}"] = True

        collection_results = list(collection.find(query, projection))
        results.extend(collection_results)

    cleaned = clean_data(results)

    if not cleaned:
        return {"message": "Даних за заданими фільтрами не знайдено", "results": []}

    return {"results": cleaned}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
