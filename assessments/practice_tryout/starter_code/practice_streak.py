import sys

def practice_streak(days):
    # Your code here!
    pass

print('Enter days separated by spaces: ', end="", file=sys.stderr, flush=True)
days = list(map(int, input().split()))
print(practice_streak(days))
