#include <iostream>
#include <string>
using namespace std;

string swappedSpelling(const string& misspelling, const string& spelling) {
    // Your code here!
    return "";
}

int main() {
    string misspelling, spelling;
    cerr << "Enter first string (misspelling): " << flush;
    cin >> misspelling;
    cerr << "Enter second string (correct spelling): " << flush;
    cin >> spelling;
    cout << swappedSpelling(misspelling, spelling) << endl;
    return 0;
}