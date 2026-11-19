# Vowel Check *(Problem 3)*

Alec is checking the vowels in a word for his spelling homework. Write a program which from an input string `word`, prints how many of its letters are vowels. For this problem, the vowels are `a`, `e`, `i`, `o`, and `u`. Each time a vowel appears, it should be counted again, and `y` is not a vowel.

**Input Format**
<br>
Line 1: `word`

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`banana`|`3`|
|2 |`rhythm`|`0`|
|3 |`queue`|`4`|

Constraints:
<br>
$1\leq$ `word` $\text{length}\leq10^5$
<br>
`word` contains only lowercase English letters, with no whitespace anywhere.

**Sample Explanations**

Sample Input 1: The letter `a` appears three times in `banana`, and none of the other letters are vowels, thus the program should print $\boxed{3}$.

Sample Input 2: None of the letters in `rhythm` are vowels, making the answer $\boxed{0}$.

Sample Input 3: The vowels are `u`, `e`, `u`, and `e`. Both appearances of each letter are counted, so the program prints $\boxed{4}$.
