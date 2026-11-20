#include <iostream>
#include <string>
using namespace std;

string snackVote([[maybe_unused]] const string& votes) {
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
