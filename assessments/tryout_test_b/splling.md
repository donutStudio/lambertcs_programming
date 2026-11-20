# Splling *(Problem 2)*

Alec has flunked his spelling homework yet again! To correct a misspelled word, he may insert the letter `e` exactly once anywhere **except the beginning or end**.

Given `misspelling` and `spelling`, print `Yes!` if inserting one `e` inside `misspelling` produces `spelling`. Also print `Yes!` if the words are already identical. Otherwise, print `No!`.

**Constraints**<br>
$1 \leq$ length of `misspelling` $\leq 10^5$<br>
$1 \leq$ length of `spelling` $\leq 10^5$<br>
Both strings contain only lowercase English letters, with no whitespace. Their lengths may differ.

**Input Format**<br>
Line 1: `misspelling`<br>
Line 2: `spelling`

| # | **Sample Input** | **Sample Output** |
|:---|---:|---:|
| 1 | `splling`<br>`spelling` | `Yes!` |
| 2 | `codng`<br>`coding` | `No!` |
| 3 | `tung`<br>`tung` | `Yes!` |
| 4 | `car`<br>`care` | `No!` |

**Sample Explanations**

Sample Input 1: Insert `e` after `p`, between the second and third letters, to turn `splling` into `spelling`. Print `Yes!`.

Sample Input 2: No insertion of `e` turns `codng` into `coding`. Print `No!`.

Sample Input 3: `tung` is already identical to `tung`. Print `Yes!`.

Sample Input 4: The only insertion that turns `car` into `care` is at the end, which is not allowed. Print `No!`.
