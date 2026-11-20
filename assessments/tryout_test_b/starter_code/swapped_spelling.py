def swapped_spelling(misspelling, spelling) -> bool:
    # Your code here! Return True for Yes! or False for No!.
    return False

misspelling = input('Enter first string (misspelling): ')
spelling = input('Enter second string (correct spelling): ')
print("Yes!" if swapped_spelling(misspelling, spelling) else "No!")
