# Reading Goal *(Problem 10)*

Alec is catching up on his reading! A list `pages` contains the number of pages he read each day, in order. He wants to find a block of consecutive days during which he read at least `goal` pages in total. Write a program that prints the minimum number of days in such a block. The block can start and end anywhere in the list, but days cannot be skipped. If there is no block with a total of at least `goal` pages, the program should print `-1`.

**Input Format**
<br>
Line 1: `goal`
<br>
Line 2: `pages1 pages2 pages3` .. `pagesN` (space separated integers)

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`7`<br>`2 3 1 2 4 3`|`2`|
|2 |`8`<br>`3 1 3`|`-1`|
|3 |`6`<br>`3 1 3 6 2`|`1`|

Constraints:
<br>
$1\leq$ `goal` $\leq10^7$
<br>
$1\leq$ `pages` $\text{length}\leq1000$
<br>
Each number in `pages`: $1\leq$ `number` $\leq10^4$

**Sample Explanations**

Sample Input 1: The last two days have a total of $4+3=7$ pages, meeting the goal in $2$ days. No single day has at least $7$ pages, making the minimum number of days $\boxed{2}$.

Sample Input 2: Even all three days together have only $7$ pages, which is less than $8$, thus the program should print `-1`.

Sample Input 3: The fourth day alone has $6$ pages, so the program should print $\boxed{1}$.
