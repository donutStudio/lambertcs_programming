# C++ reference

C++17 syntax and common standard-library operations. Entries are independent examples, not one program. Names such as `a`, `s`, `x`, and `key` stand for your own values. Indices start at zero; iterator ranges exclude their end.

## Program structure, headers, and types

```cpp
#include <iostream>      // cin, cout
#include <string>        // string, stoi, to_string
#include <vector>        // vector
#include <algorithm>     // sort, reverse, lower_bound, etc.
#include <numeric>       // accumulate, gcd, iota
#include <map>           // map
#include <unordered_map> // unordered_map
#include <set>           // set
#include <unordered_set> // unordered_set
#include <queue>         // queue, priority_queue
#include <stack>         // stack
#include <deque>         // deque
#include <cmath>         // sqrt, pow, floor, ceil
#include <limits>        // numeric_limits
#include <utility>       // pair
#include <tuple>         // tuple
#include <functional>    // greater
using namespace std;    // Examples below omit the std:: prefix
int main() {
    cout << "Hello\n";
    return 0;
}
int n = 12;             // Signed integer; width is implementation-dependent
long long big = 3000000000LL; // At least 64 bits; LL marks long long literal
double x = 2.5;         // Approximate floating-point number
bool ok = true;         // true or false
char c = 'A';           // One character code unit
string s = "hello";     // Mutable string of char values
auto value = 12;        // Infer type from initializer
const int LIMIT = 100;  // Cannot change this variable
numeric_limits<int>::min(); numeric_limits<int>::max(); // Actual int bounds
// Initialize local numeric variables: uninitialized values are unsafe to read.
```

## Operators, references, and conversions

```cpp
a + b; a - b; a * b; a / b; a % b; // Arithmetic; integer / truncates toward zero
// -7 / 3 is -2; -7 % 3 is -1. Integer division by zero is undefined behavior.
a == b; a != b; a < b; a <= b; // Comparisons; also > and >=
!ok; p && q; p || q;           // Short-circuit logical operators
a & b; a | b; a ^ b; ~a;      // Bitwise AND, OR, XOR, complement
a << 1; a >> 1;              // Shift bits; prefer nonnegative operands
n++; n--; n += 2;             // Increment, decrement, compound assignment
int result = p ? a : b;       // Conditional expression
double ratio = static_cast<double>(a) / b; // Convert before dividing
long long product = 1LL * a * b; // Promote before multiplying
int n = stoi("12");          // Parse int; may throw invalid_argument/out_of_range
long long k = stoll("12");   // Parse long long
double x = stod("2.5");      // Parse double
string s = to_string(12);     // Convert number to text
int& ref = n;                // Reference aliases n; writes change n
int* ptr = &n;               // Pointer holds address; *ptr accesses n
// Signed integer overflow is undefined behavior. ^ is XOR, not exponentiation.
// Avoid mixing signed indices with unsigned size() in subtraction.
```

## Conditions, loops, functions, and lambdas

```cpp
if (n > 0) {
    cout << "positive\n";
} else if (n == 0) {
    cout << "zero\n";
} else {
    cout << "negative\n";
}
for (int i = 0; i < n; ++i) { } // i = 0 through n-1
for (int value : a) { }         // Iterate copies of elements
for (auto& value : a) { }       // Iterate references; can modify elements
for (const auto& value : a) { } // Read without copying or modifying
while (n > 0) { --n; }
do { --n; } while (n > 0);      // Body executes at least once
// break exits nearest loop; continue starts its next iteration.
int add(int a, int b) { return a + b; } // Define outside main
void change(vector<int>& a) { a.push_back(3); } // Reference parameter
int first(const vector<int>& a) { return a[0]; } // Read-only reference
auto twice = [](int x) { return x * 2; }; // Lambda expression
auto addOffset = [offset](int x) { return x + offset; }; // Capture by value
// [ & ] without spaces captures outer variables by reference.
// Deep recursion can exhaust the call stack.
```

## Standard input and output

```cpp
ios::sync_with_stdio(false); cin.tie(nullptr); // Optional faster C++ streams
int n; long long k; string word;
cin >> n >> k >> word;         // Read whitespace-delimited tokens
string line;
getline(cin, line);            // Read a whole line, removing its newline
// After >>, getline may read the remaining empty line.
cin.ignore(numeric_limits<streamsize>::max(), '\n'); // Discard remainder
while (cin >> n) { }           // Read integers until input fails / EOF
cout << n << '\n';             // Write value and newline
cout << a << ' ' << b << '\n'; // Space-separated output
#include <iomanip>
cout << fixed << setprecision(2) << x; // Two digits after decimal point
#include <sstream>
istringstream in(line);        // Parse tokens from a string
in >> word;
// endl also flushes output. '\n' usually avoids unnecessary flushing.
// With sync disabled, do not mix C stdio and C++ streams carelessly.
```

## Strings and characters

```cpp
string s = "hello";
s.size(); s.length();          // Number of char elements
s[0]; s.back();                // First / last character; must exist
s[0] = 'H';                   // Modify one character
s.substr(1, 3);               // Start index and COUNT, not end index -> "ell"
s.substr(2);                  // Suffix beginning at index 2
s.find("ll");                 // First position, or string::npos if absent
s.rfind("l");                 // Last position, or string::npos
s += "!"; s.push_back('!');    // Append string / character
s.pop_back();                 // Remove last character; must be nonempty
s.erase(1, 2);                // Remove two characters starting at index 1
s.insert(0, "hi");            // Insert text before index 0
s == t; s < t;                // Compare contents; < is lexicographic
#include <cctype>
isdigit(static_cast<unsigned char>(c)); // Nonzero if a digit
isalpha(static_cast<unsigned char>(c)); // Nonzero if a letter
tolower(static_cast<unsigned char>(c)); // Lowercase character as int
toupper(static_cast<unsigned char>(c)); // Uppercase character as int
// Cast to unsigned char for cctype calls (or pass EOF).
// string indices count char code units, not general Unicode characters.
```

## Arrays, vectors, and iterators

```cpp
int a[3] = {3, 1, 2};          // Fixed-size built-in array
vector<int> v = {3, 1, 2};
vector<int> zeros(5, 0);        // Five copies of zero
vector<vector<int>> grid(2, vector<int>(3, 0)); // Independent rows
v.size(); v.empty();           // Element count; empty check
v[0]; v.at(0);                 // Unchecked access; checked access (throws)
v.front(); v.back();           // First/last; require nonempty vector
v.push_back(4); v.pop_back();   // Append; remove last (requires nonempty)
v.insert(v.begin() + 1, 9);     // Insert before index 1; shifts later elements
v.erase(v.begin() + 1);        // Remove at index 1; shifts later elements
v.resize(8, 0);                // Change size; fill new elements with zero
v.reserve(100);                // Reserve capacity; does not change size
v.clear();                     // Remove all elements
auto b = v;                    // Copy vector contents
v.begin(); v.end();            // Iterators: first element / one past last
// Never dereference end(). Vector growth can invalidate iterators/references.
// v[i] outside valid indices is undefined behavior.
```

## Sorting, searching, and numeric helpers

```cpp
sort(v.begin(), v.end());             // Ascending in-place sort, O(n log n)
sort(v.begin(), v.end(), greater<int>()); // Descending sort
stable_sort(v.begin(), v.end());      // Preserve relative order of equal items
sort(words.begin(), words.end(), [](const string& a, const string& b) {
    return a.size() < b.size();       // Custom order; strict comparison, not <=
});
reverse(v.begin(), v.end());          // Reverse in place
min(a, b); max(a, b);                 // Smaller / larger value
min_element(v.begin(), v.end());      // Iterator to minimum; end() if empty
max_element(v.begin(), v.end());      // Iterator to maximum; end() if empty
find(v.begin(), v.end(), x);          // First match or end(); linear search
count(v.begin(), v.end(), x);         // Number of equal elements
binary_search(v.begin(), v.end(), x); // Membership in sorted ascending range
auto lo = lower_bound(v.begin(), v.end(), x); // First element >= x
auto hi = upper_bound(v.begin(), v.end(), x); // First element > x
int index = int(lo - v.begin());      // Index; may equal size() if not found
accumulate(v.begin(), v.end(), 0LL);  // Sum using long long accumulator
iota(v.begin(), v.end(), 0);          // Fill 0, 1, 2, ...
fill(v.begin(), v.end(), 7);          // Set every element to 7
v.erase(unique(v.begin(), v.end()), v.end()); // Remove adjacent duplicates
next_permutation(v.begin(), v.end()); // Next lexical order; false on wraparound
// Bounds/binary_search require an appropriately sorted range.
// unique alone returns a new logical end; it does not shrink the vector.
```

## Maps and sets

```cpp
map<string, int> m;             // Sorted unique keys; operations O(log n)
unordered_map<string, int> h;   // Hash table; average O(1), not sorted
m["red"] = 2;                  // Insert/update; missing [] inserts default 0
m.at("red");                   // Read existing key; throws if absent
m.count("red");                // 0 or 1 for these unique-key maps
auto it = m.find("red");        // Iterator, or m.end() if absent
m.erase("red");                // Remove key; return number removed
m.size(); m.empty(); m.clear();
for (const auto& [key, value] : m) { } // Structured bindings (C++17)
set<int> s;                    // Sorted unique elements
unordered_set<int> hs;          // Hash-based unique elements, not sorted
s.insert(3); s.erase(3);        // Insert / remove
s.count(3); s.find(3);          // Membership; iterator or end()
s.lower_bound(x);              // First element >= x, or end()
s.upper_bound(x);              // First element > x, or end()
multiset<int> duplicates;       // Sorted elements; duplicates allowed
duplicates.erase(x);           // Erases ALL copies of x
auto p = duplicates.find(x);
if (p != duplicates.end()) duplicates.erase(p); // Erase only one copy
// lower_bound/upper_bound members belong to ordered map/set types.
```

## Queues, stacks, deques, and heaps

```cpp
queue<int> q;                  // First in, first out
q.push(3); q.front(); q.back(); // Add back; inspect endpoints
q.pop();                       // Remove front; returns no value
stack<int> st;                 // Last in, first out
st.push(3); st.top(); st.pop(); // Add, inspect, remove top
deque<int> d;                  // Double-ended queue with indexing
d.push_back(3); d.push_front(2);
d.front(); d.back(); d[0];
d.pop_front(); d.pop_back();
priority_queue<int> h;          // MAX-heap by default
h.push(3); h.top(); h.pop();    // Add, inspect largest, remove largest
priority_queue<int, vector<int>, greater<int>> minHeap; // MIN-heap
h.size(); h.empty();           // Available for the queue/stack types above
// Check empty() before front/back/top/pop. pop() does not return the item.
// Heap insert/remove are O(log n); top O(1).
```

## Mathematics

```cpp
abs(-3); min(a, b); max(a, b); // Absolute value; smaller/larger
sqrt(9.0); pow(2.0, 3.0);     // Floating-point square root / power
floor(2.7); ceil(2.1);        // Round down / up; floating-point result
round(2.5);                   // Round to nearest; ties away from zero
gcd(12, 18); lcm(12, 18);     // <numeric>, C++17; results must fit the type
log(x); log10(x);             // Natural / base-10 logarithm
numeric_limits<double>::infinity(); // Positive infinity
// Floating-point values may be approximate; pow is not exact integer power.
// abs of the most negative signed integer cannot fit that signed type.
// C++17 has no standard-library arbitrary-precision integer type.
```

## Pairs, tuples, structs, and exceptions

```cpp
pair<int, string> p = {3, "red"};
p.first; p.second;             // Access two fields
auto [number, color] = p;      // Unpack into copies (C++17)
tuple<int, int, string> t = {1, 2, "hi"};
get<0>(t);                    // Read tuple field using compile-time index
// Pairs/tuples compare lexicographically, field by field.
struct Point {
    int x, y;                 // Public fields by default
    int total() const { return x + y; } // Read-only member function
};
Point point{2, 3};
point.x; point.total();
try {
    int value = stoi(text);
} catch (const std::exception& error) {
    cout << "invalid\n";
}
// Many indexing/overflow mistakes are undefined behavior, not exceptions.
```
