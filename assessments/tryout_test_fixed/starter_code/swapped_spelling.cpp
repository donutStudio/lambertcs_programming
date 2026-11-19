#include <iostream>
#include <string>
using namespace std;

bool swappedSpelling(const string& misspelling, const string& spelling) {
    // Your code here! Return true for Yes! or false for No!.
    return false;
}

int main() {
    string misspelling, spelling;
    cerr << "Enter first string (misspelling): " << flush;
    cin >> misspelling;
    cerr << "Enter second string (correct spelling): " << flush;
    cin >> spelling;
    cout << (swappedSpelling(misspelling, spelling) ? "Yes!" : "No!") << endl;
    return 0;
}
