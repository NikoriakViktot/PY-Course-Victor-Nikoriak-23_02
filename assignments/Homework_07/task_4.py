#Task_4

list_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dict_week = {}
dict_week_right = {}

for i, week in enumerate(list_week): dict_week[i + 1] = week

print(dict_week)

for i , week in dict_week.items(): dict_week_right[week] = i

print(dict_week_right)