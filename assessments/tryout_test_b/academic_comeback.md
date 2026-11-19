# Academic Comeback *(Problem 3)*

Teja is cooked! He wants to get an A in his class, but might not be able to. A list `grades` contains all of his whole number test scores in the class before the midterm, where if the average of the test scores is a $90$ or higher, then he will have an A average. 

When Teja takes the midterm, his midterm score will go in as an additional grade equally weighted with the rest of his tests, and the midterm will also replace his lowest test score if the midterm score is higher. 

Write a program that prints out the minimum grade he must achieve on his midterm to get an A in the class, or if he already has an A, the lowest grade he can get on the midterm and still maintain the A average.

Every test including the midterm has a minimum score of $0$ and a maximum score of $100$. If not even a perfect score on the midterm can give him an A average, the program should print `-1`.

**Input Format**
<br>
Line 1: `grade1 grade2 grade3` .. `gradeN` (space separated integers)

|#|**Sample Input**|**Sample Output**|
|:---|---:|---:|
|1 |`80 85 90`|`93`|
|2 |`70 75 80`|`-1`|
|3 |`95 95 95`|`75`|

Constraints:
<br>
$1\leq$ `grades` $\text{length}\leq10^6$
<br>
Each `grade` in `grades`: $0\leq$ `grade` $\leq100$

**Sample Explanations**

Sample Input 1: Currently, the three tests have a summed score of $255$ and the lowest test score is $80$. If Teja gets a $92$ on the midterm and replaces the $80$ test, his average will be $\frac{359}{4}=89.75$, which is less than $90$ and will not be sufficient for an A. However, if he gets a $\boxed{93}$ on the midterm and replaces the same test, the average becomes $\frac{361}{4}=90.25$, which is greater than or equal to $90$ and will give an A.

Sample Input 2: If Teja gets a perfect $100$ on the midterm and replaces the lowest score $70$ in this sample with $100$, his highest possible average will become $\frac{355}{4}=88.75$, making achieving an A impossible, thus the program should print $\boxed{-1}$.

Sample Input 3: Teja got a $95$ on all three tests in this sample, and if he gets a $74$ on the midterm, none of his past tests will be replaced because none are lower than $74$. However, $74$ test grade makes his overall average $\frac{359}{4}=89.75$, which is not high enough for an A. However if he gets a instead $75$ on the midterm, his overall average becomes $\frac{360}{4}=90$, which is greater than or equal to $90$, meaning the minimum grade he has to get on the midterm to maintain an A is $\boxed{75}$.