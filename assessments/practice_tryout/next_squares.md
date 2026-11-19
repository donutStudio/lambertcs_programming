# Next Squares *(Problem 4)*

From two integers `k` and `n`, write a program that prints the `n`th positive perfect square greater than or equal to `k`, when these squares are listed from least to greatest. A positive perfect square is the square of a positive integer, such as $1$, $4$, or $9$. If `k` is itself a positive perfect square, it is the first square in the list.

**Input Format**
<br>
Line 1: `k n` (space separated integers)

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`10 3`|`36`|
|2 |`16 1`|`16`|
|3 |`0 2`|`4`|

Constraints:
<br>
$0\leq$ `k` $\leq10^8$
<br>
$1\leq$ `n` $\leq10^4$

**Sample Explanations**

Sample Input 1: The first three positive perfect squares greater than or equal to $10$ are $16$, $25$, and $36$. The third of these is $\boxed{36}$.

Sample Input 2: Because $16$ is already a positive perfect square, it is the first square greater than or equal to $16$, so the program should print $\boxed{16}$.

Sample Input 3: The squares must be positive, so $0$ is not included. The first two are $1$ and $4$, making the answer $\boxed{4}$.
