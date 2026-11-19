# Seat Shift *(Problem 6)*

A teacher wants to change the seating order for their class. A list `seats` contains the student IDs in their current order. During one shift, the last student in the list moves to the front, and everyone else moves one position to the right. Write a program that prints the seating order after exactly `shift` shifts. Print the IDs on one line separated by single spaces. If `shift` is $0$, print the original order.

**Input Format**
<br>
Line 1: `shift`
<br>
Line 2: `seats1 seats2 seats3` .. `seatsN` (space separated integers)

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`2`<br>`10 20 30 40 50`|`40 50 10 20 30`|
|2 |`5`<br>`1 2 3`|`2 3 1`|
|3 |`0`<br>`8 4`|`8 4`|

Constraints:
<br>
$0\leq$ `shift` $\leq10^9$
<br>
$1\leq$ `seats` $\text{length}\leq10^4$
<br>
Each `id` in `seats`: $1\leq$ `id` $\leq10^6$
<br>
Student IDs in `seats` are all different.

**Sample Explanations**

Sample Input 1: After one shift, the order is `50 10 20 30 40`. After the second shift, the order becomes `40 50 10 20 30`, which is what the program should print.

Sample Input 2: After three shifts, the order is back to `1 2 3`. Two more shifts give `2 3 1`.

Sample Input 3: No shifts are made, so the program prints the original order, `8 4`.
