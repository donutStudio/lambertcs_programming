def seat_shift(shift, seats):
    # Your code here!
    pass

shift = int(input('Enter shift: '))
seats = list(map(int, input('Enter seats separated by spaces: ').split()))
print(seat_shift(shift, seats))
