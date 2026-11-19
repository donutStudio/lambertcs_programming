# Swapped Spelling *(Problem 2)*
When Alec did his spelling homework, he accidentally misspelled several words. Alec decides to go through his misspelled words and swap exactly two letters to correct the spelling. Write a program which from two input strings `misspelling` and `spelling`, where `misspelling` is the misspelled word and `spelling` is the correct spelling, prints `Yes!` if the misspelled word can be spelled correctly by swapping the positions of two letters, and prints `No!` if there is no way swapping two of the letters can produce a correct spelling. If the word is already spelled correctly, print `Yes!`.

Constraints:
<br>
$1\leq$ `misspelling` $\text{length}\leq10^5$
<br>
$1\leq$ `spelling` $\text{length}\leq10^5$
<br>
Both `misspelling` and `spelling` contain only lowercase English letters, with no whitespace anywhere.

**Input Format**
<br>
Line 1: `misspelling`
<br>
Line 2: `spelling`

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`freind`<br>`friend`|`Yes!`|
|2 |`bca`<br>`abc`|`No!`|
|3 |`tung`<br>`tung`|`Yes!`|
|4 |`rahus`<br>`sahur`|`Yes!`|

**Sample Explanations**

Sample Input 1: In the misspelled word `freind` swapping the third letter `e` and the fourth letter `i`, a resulting string of `friend` is produced. Because the correct spelling could be produced by swapping two letters, the code should print `Yes!`.

Sample Input 2: In the string `bca`, none of the possible strings resulting from two letter swaps (`cba`, `acb`, and `bac`) are equivalent to the correct spelling `abc`, thus the code should print `No!`.

Sample Input 3: Both of these spellings of the string `tung` are equivalent, thus the code should print `Yes!`.

Sample Input 4: In the misspelled word `rahus`, the first letter `r` and the last letter `s` can be swapped to produce the correct spelling `sahur`, thus the code prints `Yes!`.