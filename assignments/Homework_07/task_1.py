#Task_1

in_str = str(input("Please write aa string: "))
res_dict = {}

for i in in_str:
    if i in res_dict:
        res_dict[i] += 1
    else:
        res_dict[i] = 1

print(res_dict)