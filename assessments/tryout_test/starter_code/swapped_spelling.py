import sys

def swapped_spelling(misspelling, spelling) -> bool:
    # Your code here! Return True for Yes! or False for No!.
    return False

print('Enter first string (misspelling): ', end="", file=sys.stderr, flush=True)
misspelling = input()
print('Enter second string (correct spelling): ', end="", file=sys.stderr, flush=True)
spelling = input()
print("Yes!" if swapped_spelling(misspelling, spelling) else "No!")
