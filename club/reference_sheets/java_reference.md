# Java reference

Basic Java syntax and common standard-library operations (Java 8+). Entries are independent examples, not one program. Names such as `a`, `s`, `x`, and `key` stand for your own values. Indices start at zero; range ends are usually excluded.

## Program structure and types

```java
import java.util.*;             // Collections, Arrays, Scanner, etc.
import java.io.*;               // BufferedReader, PrintWriter, etc.
public class Main {
    public static void main(String[] args) throws IOException {
        System.out.println("Hello"); // Program execution begins here
    }
    static int twice(int x) { return x * 2; } // Helper method
}
int n = 12;                    // Signed 32-bit integer
long big = 3000000000L;         // Signed 64-bit integer; L marks long literal
double x = 2.5;                // Approximate floating-point number
boolean ok = true;             // true or false
char c = 'A';                  // One UTF-16 code unit
String s = "hello";            // Immutable text
Integer boxed = 3;             // Wrapper used in generic collections
String absent = null;          // No object; accessing it throws NullPointerException
final int LIMIT = 100;         // Cannot reassign this variable
Integer.MIN_VALUE; Integer.MAX_VALUE; // int bounds: -2^31 through 2^31-1
Long.MIN_VALUE; Long.MAX_VALUE;       // long bounds: -2^63 through 2^63-1
// Local variables must be initialized before reading them.
```

## Operators and conversions

```java
a + b; a - b; a * b; a / b; a % b; // Arithmetic; integer / truncates toward zero
// -7 / 3 is -2; -7 % 3 is -1. Integer division by zero throws.
a == b; a != b; a < b; a <= b;    // Comparisons; also > and >=
!ok; p && q; p || q;              // Short-circuit logical operators
a & b; a | b; a ^ b; ~a;         // Bitwise operations
a << 1; a >> 1; a >>> 1;         // Left, signed right, zero-fill right shifts
n++; n--; n += 2;                // Increment, decrement, compound assignment
int smaller = p ? a : b;         // Conditional expression
double ratio = (double) a / b;   // Cast before dividing to keep fractional part
long product = (long) a * b;     // Promote before multiplying to avoid int overflow
int n = Integer.parseInt("12");  // Parse decimal; invalid text -> NumberFormatException
long n = Long.parseLong("12");
double x = Double.parseDouble("2.5");
String s = String.valueOf(12);   // Convert a value to text
// Integer overflow wraps. Use equals() for String/collection value equality.
// Math.pow(a, b), not ^, computes a power. ^ means bitwise XOR.
```

## Conditions, loops, and methods

```java
if (n > 0) {
    System.out.println("positive");
} else if (n == 0) {
    System.out.println("zero");
} else {
    System.out.println("negative");
}
for (int i = 0; i < n; i++) { }  // Count from 0 through n-1
for (int value : a) { }          // Visit array or collection values
while (n > 0) { n--; }           // Repeat while condition is true
do { n--; } while (n > 0);       // Execute body at least once
// break exits nearest loop; continue starts its next iteration.
static int add(int a, int b) {
    return a + b;                // Return value to caller
}
static void show(int x) {
    System.out.println(x);       // void methods return no value
}
// Arguments are passed by value. An object reference can refer to shared data.
// Very deep recursion can throw StackOverflowError.
```

## Standard input and output

```java
Scanner in = new Scanner(System.in); // java.util.Scanner
int n = in.nextInt();
long k = in.nextLong();
double x = in.nextDouble();
String token = in.next();        // Next whitespace-delimited token
String line = in.nextLine();     // Remainder of current line, without line ending
in.hasNext(); in.hasNextInt();   // Check for another token/integer
// After nextInt(), nextLine() may read an empty remainder; consume it if needed.
BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
String line = br.readLine();     // null at EOF; method can throw IOException
StringTokenizer st = new StringTokenizer(line); // java.util.StringTokenizer
int a = Integer.parseInt(st.nextToken());
System.out.print(a);             // Print with no added newline
System.out.println(a);           // Print followed by newline
System.out.printf("%.2f%n", x);   // Format to two decimal places and newline
PrintWriter out = new PrintWriter(System.out);
out.println(a); out.flush();     // Buffered output; flush before program exits
// Choose one input reader; do not mix readers on System.in.
```

## String and StringBuilder

```java
s.length(); s.charAt(0);         // Length; character at index
s.substring(1, 4);              // Characters at indices 1, 2, 3
s.substring(2);                 // Suffix beginning at index 2
s.indexOf("ab");                // First index, or -1 if absent
s.lastIndexOf("ab");            // Last index, or -1
s.equals(t);                    // Same text; == tests reference identity
s.compareTo(t);                 // Negative/zero/positive for lexical ordering
s.contains("ab");               // Substring membership
s.startsWith("ab"); s.endsWith("z"); // Prefix/suffix checks
s.toLowerCase(); s.toUpperCase();   // Return changed text; original unchanged
s.trim();                       // Remove leading/trailing characters <= U+0020
s.replace("a", "b");            // Literal replacement; returns new String
s.split("\\s+");                // Split on whitespace regex
s.split(",", -1);               // Split on commas; preserve trailing empty fields
s.toCharArray();                // Copy into char[]
String.join(" ", words);        // Join strings with spaces
Character.isDigit(c); Character.isLetter(c); // Character categories
StringBuilder sb = new StringBuilder(); // Mutable text builder
sb.append("ab").append(12);     // Append text or another value
sb.charAt(0); sb.setCharAt(0, 'x'); // Read/change a character
sb.length(); sb.reverse();      // Size; reverse in place
sb.delete(0, 2); sb.insert(0, "hi"); // Delete exclusive-end range; insert
sb.toString();                  // Obtain an immutable String
```

## Arrays and Arrays helpers

```java
int[] a = new int[5];            // Five zero-initialized integers
int[] b = {3, 1, 2};
int[][] grid = new int[2][3];    // Two rows, three columns
a.length; a[0]; a[a.length - 1]; // Size, first, last (must be nonempty)
a[0] = 7;                       // Replace an element
Arrays.fill(a, 9);              // Set every element to 9
Arrays.sort(a);                 // Ascending sort in place
Arrays.sort(a, 1, 4);            // Sort indices [1,4)
Arrays.copyOf(a, 8);             // Copy; pad with zeros if longer
Arrays.copyOfRange(a, 1, 4);     // Copy indices [1,4)
Arrays.equals(a, b);             // Element-by-element equality
Arrays.toString(a);              // Debug representation such as [1, 2, 3]
Arrays.binarySearch(a, x);       // Sorted array: index, or -(insertionPoint)-1
// Binary search may return any matching duplicate, not necessarily the first.
// Out-of-bounds indices throw ArrayIndexOutOfBoundsException.
// b = a aliases the same array. Arrays.copyOf on nested arrays is shallow.
```

## ArrayList and sorting collections

```java
ArrayList<Integer> a = new ArrayList<>(); // java.util; generic type is a wrapper
a.add(4); a.add(0, 2);          // Append; insert at index and shift elements
a.get(0); a.set(0, 8);          // Read; replace and return old value
a.size(); a.isEmpty();          // Entry count; empty check
a.contains(4); a.indexOf(4);    // Membership; first index or -1
a.remove(0);                    // Remove by index and return old value
a.remove(Integer.valueOf(4));   // Remove first value 4, rather than index 4
a.clear();                      // Remove all elements
ArrayList<Integer> b = new ArrayList<>(a); // Shallow copy
Collections.sort(a);            // Ascending order, in place
a.sort(Comparator.reverseOrder()); // Descending order, in place
words.sort(Comparator.comparingInt(String::length)); // Sort strings by length
Collections.reverse(a);         // Reverse order in place
Collections.min(a); Collections.max(a); // Require nonempty collection
Collections.binarySearch(a, x); // Sorted list; same negative-result encoding as Arrays
// Prefer Integer.compare(x, y) in comparators; x-y can overflow.
```

## Maps and sets

```java
Map<String, Integer> m = new HashMap<>(); // Key/value mapping
m.put("red", 2);                // Insert or replace; returns old value or null
m.get("red");                   // Lookup; missing key returns null
m.getOrDefault("blue", 0);      // Default if absent; does not insert
m.containsKey("red");           // Test key membership
m.remove("red");                // Remove key; returns old value or null
m.size(); m.isEmpty(); m.clear(); // Size, empty check, remove all
for (Map.Entry<String, Integer> e : m.entrySet()) {
    e.getKey(); e.getValue();   // Iterate key/value pairs
}
m.keySet(); m.values();         // Views backed by the map
Set<Integer> s = new HashSet<>(); // Unique values
s.add(3); s.contains(3); s.remove(3); // Add, test, remove
s.size(); s.isEmpty();
TreeMap<Integer, String> ordered = new TreeMap<>(); // Sorted keys; O(log n)
ordered.floorKey(x); ordered.ceilingKey(x); // Nearest <= / >= key; null if absent
TreeSet<Integer> sorted = new TreeSet<>(); // Sorted unique values
sorted.lower(x); sorted.higher(x); // Nearest strictly smaller/larger; null if absent
// HashMap/HashSet have no sorted-order guarantee. Typical lookups are O(1).
// Collections use equals/hashCode for value equality; mutable keys need care.
```

## Queues, stacks, and priority queues

```java
Deque<Integer> q = new ArrayDeque<>(); // Double-ended queue; no null elements
q.addLast(3); q.addFirst(2);    // Insert at back/front
q.peekFirst(); q.peekLast();   // Read endpoints; null when empty
q.pollFirst(); q.pollLast();   // Remove endpoints; null when empty
q.push(4); q.pop();            // Stack operations at front; pop throws if empty
q.size(); q.isEmpty();
Queue<Integer> fifo = new ArrayDeque<>();
fifo.offer(3); fifo.poll(); fifo.peek(); // Add back, remove front, read front
PriorityQueue<Integer> h = new PriorityQueue<>(); // Min-heap
h.offer(3); h.peek(); h.poll(); // Add, read smallest, remove smallest
PriorityQueue<Integer> max = new PriorityQueue<>(Comparator.reverseOrder());
// Heap insert/remove are O(log n); peek O(1). Iterating a heap is not sorted.
// Unboxing a null result into int throws NullPointerException.
```

## Mathematics and large integers

```java
Math.abs(-3); Math.min(a, b); Math.max(a, b); // Basic numeric helpers
Math.sqrt(9); Math.pow(2, 3);   // Floating square root / power (double results)
Math.floor(2.7); Math.ceil(2.1); // Round down/up; return double
Math.round(2.5);                // Nearest long; ties toward positive infinity
Math.floorDiv(-7, 3);           // Floor division -> -3
Math.floorMod(-7, 3);           // Floor remainder -> 2
Math.log(x); Math.log10(x);     // Natural / base-10 logarithm
Math.PI; Double.POSITIVE_INFINITY;
import java.math.BigInteger;   // Arbitrary-precision integers
BigInteger x = new BigInteger("12345678901234567890");
BigInteger y = BigInteger.valueOf(10);
x.add(y); x.subtract(y); x.multiply(y); // Return new BigInteger values
x.divide(y); x.remainder(y); x.gcd(y);
x.modPow(y, modulus);          // Modular exponentiation; positive modulus
x.compareTo(y); x.toString();  // Compare; convert to decimal text
// Math.abs(Integer.MIN_VALUE) still overflows int; promote to long first.
```

## Classes, objects, and exceptions

```java
static class Point {           // May be nested inside Main
    int x, y;
    Point(int x, int y) {       // Constructor has no return type
        this.x = x; this.y = y;
    }
    int total() { return x + y; }
}
Point p = new Point(2, 3);
p.x; p.total();                // Field access; instance method call
try {
    int n = Integer.parseInt(text);
} catch (NumberFormatException error) {
    System.out.println("invalid");
}
// Methods that can throw checked IOException must catch or declare it.
```
