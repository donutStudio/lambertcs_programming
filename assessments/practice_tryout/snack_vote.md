# Movie Vote *(Problem 8)*

A group is voting on a Movie, and each Movie is represented by a lowercase English letter. An input string `votes` contains one letter for each member's vote. Write a program that prints the letter with the most votes. If two or more letters have the same greatest number of votes, print the one that comes first in the alphabet. Only letters that received at least one vote can win.

**Input Format**
<br>
Line 1: `votes`

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`bbacb`|`b`|
|2 |`ccbb`|`b`|
|3 |`zzz`|`z`|

Constraints:
<br>
$1\leq$ `votes` $\text{length}\leq10^5$
<br>
`votes` contains only lowercase English letters, with no whitespace anywhere.

**Sample Explanations**

Sample Input 1: The letter `b` has three votes, while `a` and `c` each have one, so the program should print `b`.

Sample Input 2: Both `b` and `c` have two votes. Because `b` comes first in the alphabet, the program should print `b`.

Sample Input 3: Only `z` received any votes, thus the program prints `z`.
