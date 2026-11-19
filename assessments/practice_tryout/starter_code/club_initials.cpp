#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

string clubInitials(const string& name) {
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
