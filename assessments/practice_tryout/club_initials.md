# Club Initials *(Problem 5)*

Samvid is making a short name for a new club. From an input string `name` containing the words in the club's name, write a program that prints the first letter of each word, in the same order the words appear. Print these letters together with no spaces between them.

**Input Format**
<br>
Line 1: `name`

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`competitive programming club`|`cpc`|
|2 |`lambert`|`l`|
|3 |`a very cool club`|`avcc`|

Constraints:
<br>
$1\leq$ `name` $\text{length}\leq10^5$
<br>
`name` contains only lowercase English letters and spaces, with exactly one space between consecutive words and no spaces at the beginning or end.

**Sample Explanations**

Sample Input 1: The first letters of `competitive`, `programming`, and `club` are `c`, `p`, and `c`, so the program should print `cpc`.

Sample Input 2: There is only one word, so the program prints its first letter, `l`.

Sample Input 3: Taking the first letter from each of the four words gives `avcc`. Notice how the one-letter word `a` also contributes a letter.
