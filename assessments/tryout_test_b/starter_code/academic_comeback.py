import sys

def academic_comeback(grades):  # grades is a list of integers
    # Your code here!
    pass

print('Enter grades separated by spaces: ', end="", file=sys.stderr, flush=True)
grades = [int(g) for g in input().split()]
print(academic_comeback(grades))