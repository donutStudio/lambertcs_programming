import sys

def reading_goal(goal, pages):
    # Your code here!
    pass

print('Enter goal: ', end="", file=sys.stderr, flush=True)
goal = int(input())
print('Enter pages separated by spaces: ', end="", file=sys.stderr, flush=True)
pages = list(map(int, input().split()))
print(reading_goal(goal, pages))
