import sys

print("Original sys.path:")

for path in sys.path:
    print(path)

# Change sys.path inside Python
sys.path.append("example_directory")

print("\nUpdated sys.path:")

for path in sys.path:
    print(path)

print("\nConclusion:")
print("Yes, sys.path can be changed from within Python.")
print("It affects where Python looks for module files.")