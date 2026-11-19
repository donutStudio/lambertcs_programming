# Candle Split *(Problem 1)*

Out of $365$ days in a year, Octavius and Samzua-chan just so happen to share the same birthday! Today is their birthday, and they each want their own cake. However, they look in the pantry and only see `n` candles. Both of them want a positive, even number of candles, and neither wants the same number as the other. Write a program that prints `YES` if all `n` candles can be split between their two cakes while meeting these conditions, and prints `NO` if there is no way to do so.

**Input Format**
<br>
Line 1: `n`

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`8`|`YES`|
|2 |`11`|`NO`|
|3 |`14`|`YES`|
|4 |`4`|`NO`|

Constraints:
<br>
$1\leq$ `n` $\leq10^9$

**Sample Explanations**

Sample Input 1: The candles can be split into $2$ candles on one cake and $6$ on the other. Both numbers are positive and even, and they are different, thus the program should print `YES`.

Sample Input 2: There is no way to split $11$ candles into two even numbers, thus the program should print `NO`.

Sample Input 3: One cake can have $4$ candles and the other can have $10$, so the program prints `YES`. Notice how all $14$ candles are used.

Sample Input 4: The only split into two positive, even numbers is $2$ and $2$. Because the two cakes would have the same number of candles, the program should print `NO`.
