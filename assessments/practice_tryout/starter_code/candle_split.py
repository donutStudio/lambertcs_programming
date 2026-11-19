import sys

def candle_split(n) -> bool:
    # Your code here! Return True for YES or False for NO.
    return False

print('Enter n: ', end="", file=sys.stderr, flush=True)
n = int(input())
print("YES" if candle_split(n) else "NO")
