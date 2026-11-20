#include <iostream>
#include <string>
using namespace std;

bool splling([[maybe_unused]] const string& misspelling, [[maybe_unused]] const string& spelling) {
    // Your code here! Return true for Yes! or false for No!.
    return false;
}

int main() {
    string misspelling, spelling;
    cerr << "Enter first string (misspelling): " << flush;
    cin >> misspelling;
    cerr << "Enter second string (correct spelling): " << flush;
    cin >> spelling;
    cout << (splling(misspelling, spelling) ? "Yes!" : "No!") << endl;
    return 0;
}
