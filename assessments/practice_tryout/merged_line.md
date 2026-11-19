# Merged Line *(Problem 9)*

Two groups of club members are waiting in separate lines. Each member has a number, and the numbers in each line are already ordered from least to greatest. Write a program which from two lists `first` and `second`, prints all of their numbers together in order from least to greatest. Print the numbers on one line separated by single spaces. If a number appears more than once, include every appearance in the output.

**Input Format**
<br>
Line 1: `first1 first2 first3` .. `firstN` (space separated integers)
<br>
Line 2: `second1 second2 second3` .. `secondN` (space separated integers)

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`1 4 7`<br>`2 4 8`|`1 2 4 4 7 8`|
|2 |`5 6`<br>`1 2 3`|`1 2 3 5 6`|
|3 |`2`<br>`2`|`2 2`|

Constraints:
<br>
$1\leq$ `first` $\text{length}\leq5000$
<br>
$1\leq$ `second` $\text{length}\leq5000$
<br>
Each number in either list: $0\leq$ `number` $\leq10^6$
<br>
Each list is already ordered from least to greatest; equal consecutive numbers are allowed.

**Sample Explanations**

Sample Input 1: Combining the lists in order gives `1 2 4 4 7 8`. Notice how both appearances of $4$ are included.

Sample Input 2: Every number in `second` comes before every number in `first`, so the program should print `1 2 3 5 6`.

Sample Input 3: Each list contains a $2$, and both must appear in the output, thus the program prints `2 2`.
