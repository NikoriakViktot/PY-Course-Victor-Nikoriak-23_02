COL_MAP = {
    # базові
    "date": "дата",
    "commodity": "товар",
    "price": "ціна",
    "usdprice": "ціна_usd",

    # географія
    "admin1": "область",
    "admin2": "район",
    "market": "ринок",
    "market_id": "id_ринку",
    "latitude": "широта",
    "longitude": "довгота",

    # типи
    "category": "категорія",
    "commodity_id": "id_товару",
    "unit": "одиниця",
    "currency": "валюта",

    # економіка
    "value": "значення",
    "indicator": "індикатор",

    # порти
    "port": "порт",
    "shipments": "перевезення",

    # борг
    "debt": "борг",

    # інше
    "region": "регіон",
}


def translate_columns(df):
    return df.rename(columns={k: v for k, v in COL_MAP.items() if k in df.columns})
