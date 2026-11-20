#include <iostream>
#include <string>
using namespace std;

string clubInitials([[maybe_unused]] const string& name) {
    // Your code here!
    return "";
}

int main() {
    cerr << "Enter name: " << flush;
    string name;
    getline(cin, name);
    cout << clubInitials(name) << endl;
    return 0;
}
