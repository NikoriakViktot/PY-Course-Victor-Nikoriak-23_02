from data_utils import get_dataset


# ============================================
# 🍞 FOOD ANALYSIS
# ============================================

def get_food_timeseries(commodity):
    df = get_dataset("food")

    dff = df[df["товар"] == commodity]

    return (
        dff.groupby("дата")["ціна"]
        .mean()
        .reset_index()
    )


def get_region_prices(commodity):
    df = get_dataset("food")

    dff = df[df["товар"] == commodity]

    return (
        dff.groupby("область")["ціна"]
        .mean()
        .reset_index()
    )


# ============================================
# 💱 ECONOMY ANALYSIS
# ============================================

def get_exchange_timeseries():
    df = get_dataset("exchange")

    if "дата" not in df.columns:
        return None

    return df.sort_values("дата")

