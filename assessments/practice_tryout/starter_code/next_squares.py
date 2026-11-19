import sys

def next_squares(k, n):
    # Your code here!
    pass

print('Enter k and n separated by a space: ', end="", file=sys.stderr, flush=True)
k, n = map(int, input().split())
print(next_squares(k, n))
