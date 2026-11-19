# Digit Difference *(Problem 2)*

From a positive integer `n`, write a program that prints the greatest digit in `n` minus the least digit in `n`. If all of the digits are the same, the program should print `0`.

**Input Format**
<br>
Line 1: `n`

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`5824`|`6`|
|2 |`7003`|`7`|
|3 |`9`|`0`|

Constraints:
<br>
$1\leq$ `n` $\leq10^9$

**Sample Explanations**

Sample Input 1: The greatest digit in $5824$ is $8$ and the least digit is $2$, making the difference $8-2=\boxed{6}$.

Sample Input 2: The greatest digit is $7$ and the least digit is $0$, so the program should print $\boxed{7}$.

Sample Input 3: There is only one digit in $9$, so both the greatest and least digits are $9$. The difference is $9-9=\boxed{0}$.
