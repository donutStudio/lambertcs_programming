# Fizzes and Buzzes *(Problem 1)*

From $0$ to an integer `n` inclusive, print the sum of all integers that are divisible by $3$ or divisible by $5$, **but not both**.

**Input Format**<br>
Line 1: `n`

| # | **Sample Input** | **Sample Output** |
|:---|---:|---:|
| 1 | `13` | `45` |
| 2 | `40` | `363` |

**Constraints**<br>
$0 \leq n \leq 10^6$

The sum can exceed the range of a 32-bit integer. Use `long` in Java or `long long` in C++.

**Sample Explanations**

Sample Input 1: The qualifying numbers are $3,5,6,9,10,12$. Their sum is $\boxed{45}$. Zero is divisible by both $3$ and $5$, so it is excluded.

Sample Input 2: The multiples of $3$ sum to $273$, and the multiples of $5$ sum to $180$. The numbers $15$ and $30$ are divisible by both and were counted twice, so subtract them twice: $273+180-2(15+30)=\boxed{363}$.
