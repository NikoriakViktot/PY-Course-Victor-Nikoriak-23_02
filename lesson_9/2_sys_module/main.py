import sys

print("Before changing sys.path:")
print(sys.path)

sys.path.append("my_modules")

print("\nAfter changing sys.path:")
print(sys.path)

import test_module

test_module.say_hello()