import sys

def swapped_spelling(misspelling, spelling):
    # Your code here!
    pass

print('Enter first string (misspelling): ', end="", file=sys.stderr, flush=True)
misspelling = input()
print('Enter second string (correct spelling): ', end="", file=sys.stderr, flush=True)
spelling = input()
print(swapped_spelling(misspelling, spelling))