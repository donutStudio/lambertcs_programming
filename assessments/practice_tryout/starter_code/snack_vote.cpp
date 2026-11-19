#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

string snackVote(const string& votes) {
    // Your code here!
    return "";
}

int main() {
    cerr << "Enter votes: " << flush;
    string votes;
    getline(cin, votes);
    cout << snackVote(votes) << endl;
    return 0;
}
