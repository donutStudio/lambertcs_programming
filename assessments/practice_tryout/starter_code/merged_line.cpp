#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

string mergedLine([[maybe_unused]] const vector<int>& first, [[maybe_unused]] const vector<int>& second) {
    // Your code here!
    return "";
}

int main() {
    cerr << "Enter first separated by spaces: " << flush;
    vector<int> first;
    string firstLine;
    getline(cin, firstLine);
    istringstream firstInput(firstLine);
    int firstValue;
    while (firstInput >> firstValue) first.push_back(firstValue);
    cerr << "Enter second separated by spaces: " << flush;
    vector<int> second;
    string secondLine;
    getline(cin, secondLine);
    istringstream secondInput(secondLine);
    int secondValue;
    while (secondInput >> secondValue) second.push_back(secondValue);
    cout << mergedLine(first, second) << endl;
    return 0;
}
