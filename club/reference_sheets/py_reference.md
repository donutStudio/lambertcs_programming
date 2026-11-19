# Python reference

Python 3 syntax and common standard-library operations. Entries are independent examples, not one program. Names such as `a`, `s`, `x`, and `key` stand for your own values. Indices start at zero; slice ends are excluded.

## Values, types, and operators

```python
n = 12                    # int: arbitrary-precision integer
x = 2.5                   # float: approximate floating-point number
ok = True                 # bool: True or False
s = "hello"               # str: immutable Unicode text
missing = None            # No value; check with "is None"
int("12"); float("2.5")   # Parse numbers; invalid text raises ValueError
str(12); bool([])          # Convert to text; empty containers are false
type(x); isinstance(x, int)  # Inspect a type; test a type
a + b; a - b; a * b        # Arithmetic; + also concatenates lists/strings
a / b                     # Division producing float
a // b; a % b             # Floor division and remainder; -7 // 3 == -3
a ** b; abs(a)            # Exponentiation; absolute value
a == b; a != b; a < b     # Value comparisons; also <=, >, >=
not ok; p and q; p or q    # Short-circuit boolean operators
x in a; x not in a        # Membership tests
a & b; a | b; a ^ b       # Integer bitwise AND, OR, XOR
a << 1; a >> 1            # Shift integer bits left/right
# Zero, None, False, and empty strings/containers are false in conditions.
# == compares values; "is" compares object identity.
```

## Conditions, loops, and functions

```python
if n > 0:                 # Indentation defines each block
    print("positive")
elif n == 0:
    print("zero")
else:
    print("negative")

for i in range(5):        # i = 0, 1, 2, 3, 4
    print(i)
for i in range(2, 9, 2):  # i = 2, 4, 6, 8
    pass                 # Empty statement
for i in range(4, -1, -1):  # i = 4, 3, 2, 1, 0
    pass
while n > 0:
    n -= 1               # Also +=, *=, //=, etc.
    if n == 2:
        continue         # Skip to the next iteration
    if n == 1:
        break            # Exit the nearest loop

def twice(x):            # Define a function
    return x * 2         # Return a value; no return means None
f = lambda x: x * 2      # A single-expression function
try:
    n = int(s)
except ValueError:
    n = 0                # Handle a conversion error
# A function can read an outer variable; rebinding a global needs "global".
# Recursion depth is limited; very deep recursive calls raise RecursionError.
```

## Standard input and output

```python
line = input()                     # Read a line, without the final newline
n = int(input())                   # Read one integer
a, b = map(int, input().split())   # Read two whitespace-separated integers
values = list(map(int, input().split()))  # Read a list of integers
print(n)                           # Print followed by newline
print(a, b, sep=" ", end="\n")     # Customize separator and ending
print(*values)                     # Print list items separated by spaces
print(f"{x:.2f}")                  # Format to two decimal places
import sys
line = sys.stdin.readline()        # Includes newline; returns "" at EOF
tokens = sys.stdin.buffer.read().split()  # Read all input as byte tokens
sys.stdout.write("text\n")         # Write exactly this text
# input() raises EOFError at EOF. Do not mix token readers carelessly.
```

## Strings and characters

```python
s = "hello"
len(s); s[0]; s[-1]       # Length; first character; last character
s[1:4]; s[:3]; s[2:]     # Substrings with exclusive end; omitted bounds
s[::-1]                  # A reversed copy
s + "!"; "ab" * 3        # Concatenate; repeat
s.find("ll")             # First index, or -1 if absent
s.count("l")             # Count non-overlapping occurrences
s.startswith("he"); s.endswith("lo")  # Prefix/suffix checks
s.split()                # Split on runs of whitespace
s.split(",")             # Split on literal commas; keeps empty fields
",".join(["a", "b"])     # Join strings -> "a,b"
s.strip(); s.rstrip()    # Remove leading/trailing whitespace; trailing only
s.replace("l", "x")      # Return text with all matching pieces replaced
s.lower(); s.upper()     # Return lowercase/uppercase text
s.isdigit(); s.isalpha() # Test character categories (Unicode-aware)
ord("A"); chr(65)        # Character to integer code point; inverse
list(s)                  # List of characters
# Strings cannot be changed in place; methods above return new values.
```

## Lists, tuples, slices, and comprehensions

```python
a = [3, 1, 2]; empty = []  # Mutable ordered sequences
a[0]; a[-1]; a[1:3]       # Indexing; negative indexing; slice copy
a[0] = 8                  # Replace one element
a.append(4); a.extend([5, 6])  # Append one item; append multiple items
a.insert(1, 9)            # Insert before index 1; shifts later items
x = a.pop()               # Remove and return the last item
x = a.pop(0)              # Remove first item; shifts later items, O(n)
a.remove(9)               # Remove first matching value; absent -> ValueError
del a[0]                  # Delete by index
a.index(5); a.count(5)    # First index (or ValueError); number of matches
b = a.copy(); b = a[:]   # Shallow copies; nested objects are still shared
a.reverse()               # Reverse in place; returns None
a.clear()                 # Remove all elements
t = (3, 4); x, y = t      # Immutable tuple; unpack two elements
single = (3,)             # A one-element tuple needs the comma
squares = [x*x for x in range(5)]  # Construct a list
evens = [x for x in a if x % 2 == 0]  # Filter while constructing
grid = [[0] * 3 for _ in range(2)]   # Independent rows
# b = a aliases the same list. [[0]*3]*2 aliases its rows; avoid for mutation.
```

## Iteration and built-in helpers

```python
len(a); sum(a); min(a); max(a)   # Size, sum, smallest/largest
min(a, default=0)                # Handle an empty iterable
abs(-3); round(2.5)              # Absolute value; ties round to even
any(a); all(a)                   # Any/all values truthy; all([]) is True
for i, value in enumerate(a):    # Index and value
    pass
for x, y in zip(a, b):           # Pair items; stops at shorter input
    pass
for value in reversed(a):       # Reverse iterator, not a list copy
    pass
sorted(a)                       # Return a new ascending list
sorted(a, reverse=True)          # Descending order
sorted(words, key=len)           # Sort by a key; ties preserve input order
a.sort()                        # Sort list in place; returns None
list(map(int, ["1", "2"]))      # Apply conversion to each item
# min/max without a default raise ValueError on an empty iterable.
```

## Dictionaries and sets

```python
d = {"red": 2}; d = {}          # Mutable key/value mapping
d["blue"] = 3                   # Insert or replace a value
d["red"]                        # Lookup; missing key raises KeyError
d.get("green", 0)               # Lookup with default; does not insert
"red" in d                      # Test keys, not values
d.setdefault("green", 0)        # Insert default if absent; return value
d.update({"red": 4})            # Merge entries, replacing matching keys
d.pop("red", 0)                 # Remove key and return value or default
for key, value in d.items():     # Iterate key/value pairs
    pass
d.keys(); d.values(); len(d)    # Views of keys/values; entry count
s = {1, 2}; s = set()           # Unique elements; {} is a dict
s.add(3); s.discard(2)          # Add; remove if present
s.remove(3)                     # Remove, raising KeyError if absent
1 in s                          # Membership
s | t; s & t; s - t; s ^ t     # Union, intersection, difference, symmetric difference
s <= t                          # Subset check
# Keys/set elements must be hashable: integers, strings, suitable tuples.
# Dicts preserve insertion order. Sets do not promise sorted order.
```

## Counting and queues: collections

```python
from collections import Counter, defaultdict, deque
counts = Counter(["a", "a", "b"])  # Map each value to its frequency
counts["z"]                         # Missing counts read as zero
counts.most_common(2)                # Up to two (value, count) pairs
groups = defaultdict(list)           # Missing key inserts a new empty list
groups["a"].append(3)
totals = defaultdict(int)            # Missing key inserts zero
q = deque([1, 2])                    # Double-ended queue
q.append(3); q.appendleft(0)         # Add at right/left
q.pop(); q.popleft()                 # Remove at right/left; empty -> IndexError
q[0]; q[-1]; len(q)                  # Endpoints and length
q.rotate(1)                          # Move rightmost element to left
# deque append/pop operations at either end are O(1).
```

## Heaps and binary-search helpers

```python
import heapq
h = [4, 1, 3]
heapq.heapify(h)                  # Rearrange list into a min-heap in O(n)
heapq.heappush(h, 2)              # Add an item in O(log n)
heapq.heappop(h)                  # Remove smallest in O(log n); empty -> IndexError
h[0]                             # Peek smallest; heap is not a fully sorted list
heapq.nlargest(2, a)              # Up to two largest items, descending
heapq.nsmallest(2, a)             # Up to two smallest items, ascending
from bisect import bisect_left, bisect_right, insort
i = bisect_left(a, x)             # First insertion position before equal values
j = bisect_right(a, x)            # Insertion position after equal values
insort(a, x)                     # Insert in order; shifting makes this O(n)
# bisect requires a sorted sequence; i/j may equal len(a).
```

## Mathematics

```python
import math
math.sqrt(9)                # Floating square root -> 3.0
math.isqrt(10)              # Exact integer floor of square root -> 3
math.floor(2.7); math.ceil(2.1)  # Round down/up to integer
math.gcd(12, 18)            # Greatest common divisor -> 6
math.factorial(5)           # 5! -> 120
math.comb(5, 2)             # Number of unordered choices -> 10
math.perm(5, 2)             # Number of ordered choices -> 20
math.log(8, 2)              # Logarithm base 2 (floating point)
math.inf; math.pi           # Positive infinity; pi
pow(2, 10, 1000)            # Modular exponentiation -> 24
# Floating point may be inexact. Integer arithmetic stays exact.
```

## Itertools, caching, and classes

```python
from itertools import accumulate, combinations, permutations, product
list(accumulate([2, 3, 4]))     # Running totals -> [2, 5, 9]
list(combinations([1, 2, 3], 2))  # Unordered pairs, no repeated positions
list(permutations([1, 2, 3], 2))  # Ordered pairs, no repeated positions
list(product([0, 1], repeat=2))   # Cartesian product; repetition allowed
from functools import lru_cache
@lru_cache(maxsize=None)          # Cache function results for hashable arguments
def square(x):
    return x * x

class Point:
    def __init__(self, x, y):    # Initialize a new instance
        self.x, self.y = x, y
    def total(self):             # Instance methods receive self
        return self.x + self.y
p = Point(2, 3)
p.x; p.total()                  # Read an attribute; call a method
# itertools functions return iterators. Large products/permutations grow fast.
```
