#include <iostream>
#include <string>
using namespace std;

int vowelCheck([[maybe_unused]] const string& word) {
    // Your code here!
    return 0;
}

int main() {
    cerr << "Enter word: " << flush;
    string word;
    getline(cin, word);
    cout << vowelCheck(word) << endl;
    return 0;
}
