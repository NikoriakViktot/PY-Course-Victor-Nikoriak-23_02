import os
import math as mt
import numpy as np
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt


class TelegramDataLoader:
    """
    Клас для завантаження та агрегації даних телеграм.

    Цей клас дозволяє завантажувати дані (наприклад, температури, вологість, тиск тощо)
    з API або CSV, а також агрегувати їх до середньодобових значень. При цьому створюється колонка
    datetime, яка перетворюється на об’єкти типу date, а непотрібні стовпці видаляються з агрегованих даних.

    Параметри, які можна задавати при створенні екземпляру:
      - country_code (str): Код країни ('ua', 'bel', 'rus').
      - station_id (str): Ідентифікатор станції.
      - date (str): Дата у форматі YYYYMMDD.
      - date_start (str): Початкова дата для діапазону (YYYYMMDD).
      - date_end (str): Кінцева дата для діапазону (YYYYMMDD).
      - hour (int): Година дня (0-23).
      - temperature (float): Температура.
      - dew_point_temperature (float): Точка роси.
      - relative_humidity (float): Відносна вологість.
      - wind_dir (float): Напрямок вітру.
      - wind_speed (float): Швидкість вітру.
      - pressure (float): Тиск.
      - sea_level_pressure (float): Тиск на рівні моря.
      - maximum_temperature (float): Максимальна температура.
      - minimum_temperature (float): Мінімальна температура.
      - precipitation_s1 (float): Опади (перший тип).
      - precipitation_s3 (float): Опади (третій тип).
      - pressure_tendency (float): Тенденція тиску.
      - present_weather (str): Поточна погода.
      - past_weather_1 (str): Минуле погодне явище 1.
      - past_weather_2 (str): Минуле погодне явище 2.
      - sunshine (float): Сонячне сяйво.
      - ground_state_snow (str): Стан снігу на землі.
      - ground_state (str): Стан землі.
    Параметри ініціалізації:
      - csv_file (str): шлях до CSV файлу (за замовчуванням "default_data.csv")
      - api_url (str): URL для API запиту (за замовчуванням, наприклад, "http://127.0.0.1:8000/filter_telegrams/")
      - aggregate_field (str): назва числового поля для агрегації (наприклад, "temperature")
      - **kwargs: усі додаткові параметри фільтрації (наприклад, country_code, station_id, date, hour тощо)
    """

    def __init__(self, *, api_url=None,
                 aggregate_field=None, fields_to_return=None, **kwargs):
        self.api_url = api_url
        self.aggregate_field = aggregate_field
        self.fields_to_return = fields_to_return
        self.filter_params = kwargs

    def fetch_data_api(self):
        """
        Виконує запит до API для завантаження даних за заданими параметрами.

        Повертає:
          results (list): список отриманих записів.
        """
        payload = self.filter_params.copy()
        if self.fields_to_return:
            payload["fields_to_return"] = self.fields_to_return

        headers = {"accept": "application/json", "Content-Type": "application/json"}
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            results = response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            print("Помилка при виконанні запиту до API:", e)
            return []
        return results


    def get_raw_data(self):
        """
        Повертає сирі дані як DataFrame.
        Якщо force_api=True або CSV-файл відсутній, дані завантажуються через API.
        """
        results = self.fetch_data_api()
        if not results:
            print("За заданими параметрами даних не знайдено.")
            return None
        data_list = [record.get("data", {}) for record in results]
        df = pd.DataFrame(data_list)
        return df


    def get_daily_data(self):
        """
        Агрегує сирі дані до середньодобових значень.

        Повертає:
          time_index (np.ndarray): масив дат (тип date).
          values (np.ndarray): масив агрегованих значень для aggregate_field.
          df_daily (DataFrame): агрегований DataFrame.
        """
        df = self.get_raw_data()
        if df is None:
            return None, None, None

        if "datetime" not in df.columns:
            if all(col in df.columns for col in ["year", "month", "day", "hour"]):
                df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]], errors="coerce")
            else:
                df = df.copy()
                df["datetime"] = pd.to_datetime(df.index, errors="coerce")
        df.sort_values(by="datetime", inplace=True)

        df.set_index("datetime", inplace=True)
        df_daily = df.resample("D").mean(numeric_only=True).reset_index()
        # Перетворюємо datetime на об’єкти типу date
        df_daily["datetime"] = df_daily["datetime"].dt.date

        # Визначаємо, який саме стовпець агрегувати:
        if self.aggregate_field and self.aggregate_field in df_daily.columns:
            values = df_daily[self.aggregate_field].to_numpy()
        else:
            num_cols_in_df = df_daily.select_dtypes(include=[np.number]).columns
            if len(num_cols_in_df) > 0:
                values = df_daily[num_cols_in_df[0]].to_numpy()
            else:
                values = df_daily.iloc[:, 0].to_numpy()

        time_index = df_daily["datetime"].to_numpy()
        return time_index, values, df_daily

    def plot_data(self, time_index, data, title="Дані"):
        """Побудова графіку даних."""
        plt.figure()
        plt.plot(time_index, data, label="Значення")
        plt.xlabel("Дата")
        plt.ylabel("Значення")
        plt.title(title)
        plt.legend()
        plt.show()


# =================== Приклад використання ===================

if __name__ == '__main__':
    # Приклад: Завантаження даних за певну дату для країни "ua"
    # Ми задаємо, який параметр агрегувати через aggregate_field.
    loader = TelegramDataLoader(
        api_url="http://127.0.0.1:8000/filter_telegrams/",
        country_code="ua",
        fields_to_return=["pressure", "year", "month", "day", "hour"],
        aggregate_field="pressure"
    )

    # Завантаження сирих даних
    raw_df = loader.get_raw_data()
    if raw_df is not None:
        print("Сирі дані:")
        print(raw_df.head())

    # Отримання агрегованих (середньодобових) даних
    time_idx,values, df_daily = loader.get_daily_data()
    if values is not None:
        loader.plot_data(time_idx, values, title="Середньодобові дані")