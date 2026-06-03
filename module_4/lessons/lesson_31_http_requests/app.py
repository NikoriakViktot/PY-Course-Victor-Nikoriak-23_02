import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from telegram_filter import TelegramDataLoader


STATIONS = {
    1: ("Харків", "34300"),
    2: ("Дніпро", "34504"),
    3: ("Чернігів", "33135"),
    4: ("Суми", "33275"),
    5: ("Рівне", "33301"),
    6: ("Житомир", "33325"),
    7: ("Київ", "33345"),
    8: ("Львів", "33393"),
    9: ("Тернопіль", "33415"),
    10: ("Хмельницький", "33429"),
    11: ("Полтава", "33506"),
}


API_URL = "http://127.0.0.1:8000/filter_telegrams/"


def choose_station(stations: dict[int, tuple[str, str]]) -> tuple[str, str]:
    print("\nОберіть номер станції:")

    for number, (city, code) in stations.items():
        print(f"{number} - {city} (код {code})")

    try:
        station_choice = int(input("\nВведіть номер станції: "))
    except ValueError:
        print("Помилка: потрібно ввести число.")
        sys.exit(1)

    if station_choice not in stations:
        print("Невірний вибір станції.")
        sys.exit(1)

    station_name, station_id = stations[station_choice]
    print(f"\nОбрано станцію: {station_name} (код {station_id})")

    return station_name, station_id


def create_loader(station_id: str) -> TelegramDataLoader:
    return TelegramDataLoader(
        api_url=API_URL,
        country_code="ua",
        station_id=station_id,
        fields_to_return=[
            "year",
            "month",
            "day",
            "hour",
            "temperature",
            "pressure",
            "relative_humidity",
            "wind_speed",
        ],
        aggregate_field="temperature",
    )


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = ["year", "month", "day", "hour"]

    if not all(column in df.columns for column in required_columns):
        raise ValueError(f"У DataFrame немає потрібних колонок: {required_columns}")

    df = df.copy()

    df["dt"] = pd.to_datetime(
        df[["year", "month", "day", "hour"]],
        errors="coerce",
    )

    df = df.sort_values("dt").reset_index(drop=True)
    df["time_idx"] = range(len(df))

    if "temperature" in df.columns:
        df["temperature_rolling_24"] = df["temperature"].rolling(window=24).mean()

    return df


def show_http_json_preview(loader: TelegramDataLoader, limit: int = 2) -> None:
    print("\n" + "=" * 80)
    print("HTTP / JSON PREVIEW")
    print("=" * 80)

    raw_results = loader.fetch_data_api()

    print(f"\nКількість записів у JSON response: {len(raw_results)}")
    print(f"\nПерші {limit} JSON records:")

    for item in raw_results[:limit]:
        print(item)


def show_dataframe_preview(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("PANDAS DATAFRAME PREVIEW")
    print("=" * 80)

    print("\nПерші 10 записів:")
    print(df.head(10))

    print("\nОстанні 10 записів:")
    print(df.tail(10))

    print("\nКолонки:")
    print(list(df.columns))

    print("\nРозмір таблиці:")
    print(df.shape)


def show_statistics(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)

    print("\nОписова статистика:")
    numeric_df = df.select_dtypes(include=[np.number])
    print(numeric_df.describe())

    if "temperature" in df.columns:
        print("\nТемпература:")
        print(f"Min:  {df['temperature'].min()}")
        print(f"Max:  {df['temperature'].max()}")
        print(f"Mean: {df['temperature'].mean():.2f}")
        print(f"Std:  {df['temperature'].std():.2f}")

    print("\nКореляція числових змінних:")
    print(df.corr(numeric_only=True))


def plot_temperature(df: pd.DataFrame, station_name: str) -> None:
    if "temperature" not in df.columns:
        print("Колонки temperature немає у даних.")
        return

    plt.figure(figsize=(14, 6))

    plt.plot(
        df["dt"],
        df["temperature"],
        linewidth=1.2,
        label="Температура",
    )

    plt.title(f"Температура — {station_name}")
    plt.xlabel("Дата")
    plt.ylabel("Температура, °C")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_temperature_with_rolling(df: pd.DataFrame, station_name: str) -> None:
    if "temperature" not in df.columns:
        print("Колонки temperature немає у даних.")
        return

    plt.figure(figsize=(14, 6))

    plt.plot(
        df["dt"],
        df["temperature"],
        alpha=0.35,
        label="Raw temperature",
    )

    plt.plot(
        df["dt"],
        df["temperature_rolling_24"],
        linewidth=2.5,
        label="Rolling mean, window=24",
    )

    plt.title(f"Температура зі згладжуванням — {station_name}")
    plt.xlabel("Дата")
    plt.ylabel("Температура, °C")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def load_station_data(stations: dict[int, tuple[str, str]]):
    station_name, station_id = choose_station(stations)

    loader = create_loader(station_id)

    show_http_json_preview(loader)

    df = loader.get_raw_data()

    if df is None or df.empty:
        print("Дані не знайдено.")
        sys.exit(1)

    df = prepare_dataframe(df)

    show_dataframe_preview(df)
    show_statistics(df)

    plot_temperature(df, station_name)
    plot_temperature_with_rolling(df, station_name)

    time_series = df["time_idx"].values.reshape(-1, 1)
    data_series = df["temperature"].values
    n = len(data_series)

    return station_name, station_id, time_series, data_series, n, df


def main():

    print("=" * 80)
    print("WEATHER API DATA VIEWER")
    print("=" * 80)

    station_name, station_id, time_series, data_series, n, df = load_station_data(STATIONS)

    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)

    print(f"Станція: {station_name}")
    print(f"Код станції: {station_id}")
    print(f"Кількість вимірів: {n}")

    print(f"\ntime_series shape: {time_series.shape}")
    print(f"data_series shape: {data_series.shape}")

    print("\nЗавантаження та аналіз завершено успішно.")



if __name__ == "__main__":
    main()