import sys

def seat_shift(shift, seats):
    # Your code here!
    pass

print('Enter shift: ', end="", file=sys.stderr, flush=True)
shift = int(input())
print('Enter seats separated by spaces: ', end="", file=sys.stderr, flush=True)
seats = list(map(int, input().split()))
print(seat_shift(shift, seats))
