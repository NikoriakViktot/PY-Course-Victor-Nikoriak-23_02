import os
import mymod

our_path = os.getcwd()
our_file_list = os.listdir(our_path)

name_our_file = ''
for file in our_file_list:
    if '.txt' in file:
        name_our_file = file

mymod.test(name_our_file)
