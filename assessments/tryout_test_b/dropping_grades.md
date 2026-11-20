# Dropping Grades *(Problem 3)*

Teja bombed his midterm, so he is still cooked! However, by practicing programming, he was able to hack into the school system. He can now drop up to $3$ grades from the list `grades`.

Print the **minimum** number of grades he must drop to get an A (an average of $90$ or higher). Print `0` if he already has an A, or `-1` if an A is impossible within the three-drop limit. **At least one grade must remain.**

**Input Format**<br>
Line 1: `grade1 grade2 grade3 ... gradeN` (space-separated integers; there will always be an even number of grades)

| # | **Sample Input** | **Sample Output** |
|:---|---:|---:|
| 1 | `90 92 94 88` | `0` |
| 2 | `60 72 94 94 94 94` | `2` |
| 3 | `60 65 70 75 80 85` | `-1` |

**Constraints**<br>
$2 \leq$ length of `grades` $\leq 10^6$, and the length is even.<br>
Each grade is an integer between $0$ and $100$, inclusive.

**Sample Explanations**

Sample Input 1: The four grades sum to $364$, giving an average of $\frac{364}{4}=91$. Teja already has an A, so he needs to drop $\boxed{0}$ grades.

Sample Input 2: The six grades sum to $508$, giving an average of $\frac{508}{6}\approx84.67$. Dropping $60$ leaves $448$ points across five grades, averaging $89.6$, still below $90$. Dropping both $60$ and $72$ leaves four grades totaling $376$, averaging $94$. The minimum number to drop is $\boxed{2}$.

Sample Input 3: The six grades total $435$, averaging $72.5$. Even dropping the three lowest grades ($60$, $65$, and $70$) leaves $75$, $80$, and $85$, averaging $80$. An A is impossible within the three-drop limit, so print $\boxed{-1}$.
