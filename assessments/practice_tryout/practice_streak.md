# Practice Streak *(Problem 7)*

Teja is finally practicing consistently! A list `days` records whether he practiced on each day, in order, where $1$ means he practiced and $0$ means he did not. Write a program that prints the greatest number of consecutive days on which he practiced. A day marked $0$ ends a streak. If he did not practice on any day, the program should print $\boxed{0}$.

**Input Format**
<br>
Line 1: `days1 days2 days3` .. `daysN` (space separated integers)

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`1 1 0 1 1 1 0 1`|`3`|
|2 |`0 0 0`|`0`|
|3 |`0 1 1 1 1`|`4`|

Constraints:
<br>
$1\leq$ `days` $\text{length}\leq10^5$
<br>
Each number in `days` is either $0$ or $1$.

**Sample Explanations**

Sample Input 1: The practice streaks have lengths $2$, $3$, and $1$. The longest of these has length $\boxed{3}$.

Sample Input 2: Teja did not practice on any day, thus the program should print $\boxed{0}$.

Sample Input 3: The last four days form a streak of length $\boxed{4}$. Notice how a streak can continue all the way to the end of the list.
