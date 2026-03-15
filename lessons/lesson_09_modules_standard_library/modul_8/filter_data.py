import seaborn as sns

from data_downloader import load_df


tips_dfm = sns.load_dataset("tips")
print(tips_dfm.head())
load_df(tips_dfm)

