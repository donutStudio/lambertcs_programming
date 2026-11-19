# Odd Ones Out *(Problem 1)*
From $0$ to an integer `n`, write a program that prints the sum of all odd numbers from $0$ to `n` inclusive that do not end with a last digit of $1$, which are odd ones out.

**Input Format**
<br>
Line 1: `n`

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`13`|`37`|
|2 |`40`|`336`|

Constraints:
<br>
$0\leq$ `n` $\leq10^6$

**Sample Explanations**

Sample Input 1: From $0$ to $13$ inclusive, the sum of all odd numbers that DO NOT end in a $1$ are $3+5+7+9+13=\boxed{37}$. Notice how in the odd numbers being added, $1$ and $11$ were not included in the sum because they end in a $1$.

Sample Input 2: Similar to Sample Input 1, adding all odd numbers from $0$ to $40$ that do not end in $1$ results in $\boxed{336}$.