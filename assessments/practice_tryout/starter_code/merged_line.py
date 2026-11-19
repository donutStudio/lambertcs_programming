import sys

def merged_line(first, second):
    # Your code here!
    pass

print('Enter first separated by spaces: ', end="", file=sys.stderr, flush=True)
first = list(map(int, input().split()))
print('Enter second separated by spaces: ', end="", file=sys.stderr, flush=True)
second = list(map(int, input().split()))
print(merged_line(first, second))
