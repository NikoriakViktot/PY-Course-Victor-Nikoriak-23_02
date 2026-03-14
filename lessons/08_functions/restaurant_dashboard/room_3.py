

from typing import NamedTuple

class Order(NamedTuple):
    total_bill: float
    tip: float
    sex: str
    smoker: str
    day: str
    time: str
    size: int

import seaborn as sns

tips_df = sns.load_dataset("tips")
print(tips_df.head())

def orders_from_df(df) -> list[Order]:
    orders = []

    for _, row in df.iterrows():
        order = Order(
            total_bill=float(row["total_bill"]),
            tip=float(row["tip"]),
            sex=str(row["sex"]),
            smoker=str(row["smoker"]),
            day=str(row["day"]),
            time=str(row["time"]),
            size=int(row["size"]),
        )
        orders.append(order)

    return orders


orders = orders_from_df(tips_df)

print(len(orders))
print(orders[0])
orders: list[Order]

smoker_orders = []

for o in orders:
    if o.smoker == "Yes":
        smoker_orders.append(o)

print(smoker_orders)
print(f"Smokers orders: {len(smoker_orders)}")

tip_percentages = []

for o in smoker_orders:
    tip_percent = o.tip / o.total_bill * 100
    tip_percentages.append(tip_percent)

average_bill_sum = 0

for o in smoker_orders:
    average_bill_sum += o.total_bill

average_bill = average_bill_sum / len(smoker_orders)
print(f"Average bill (smokers): {average_bill:.2f}")

average_tip_sum = 0

for o in tip_percentages:
    average_tip_sum += o

average_tip = average_tip_sum / len(tip_percentages)

print(f"Average tip % (smokers): {average_tip:.2f}")



