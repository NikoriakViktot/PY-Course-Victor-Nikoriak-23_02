days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

days_dict = {i + 1: day for i, day in enumerate(days)}

reverse_dict = {day: i for i, day in days_dict.items()}

print(days_dict)
print(reverse_dict)