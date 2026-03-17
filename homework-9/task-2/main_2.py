import sys

print("До зміни:")
print(sys.path)

sys.path.append("my_modules")

print("Після зміни:")
print(sys.path)

import test_module
test_module.hello()
