from typing import NamedTuple
import seaborn as sns



class Order(NamedTuple):
    total_bill: float
    tip: float
    sex: str
    smoker: str
    day: str
    time: str
    size: int


def  load_df(df):
    orders = [
    Order(
        total_bill = row["total_bill"],
        tip = row["tip"],
        sex= row["sex"],
        smoker= row["smoker"],
        day= row["day"],
        time= row["time"],
        size = row["size"]
    )
for _, row in df.iterrows()]
    return orders

# if __name__ == "__main__":
#     tips_dfm = sns.load_dataset("tips")
#     print(tips_dfm.head(20))
#     load_df(tips_dfm)

