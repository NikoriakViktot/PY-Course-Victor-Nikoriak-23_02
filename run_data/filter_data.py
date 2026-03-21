import seaborn as sns
from module_1.lessons.lesson_09_modules_standard_library.data_downloader import load_df

tips_dfm = sns.load_dataset("tips")
print(tips_dfm.head(9))
load_df(tips_dfm)

