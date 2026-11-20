#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

int practiceStreak([[maybe_unused]] const vector<int>& days) {
    // Your code here!
    return 0;
}

int main() {
    cerr << "Enter days separated by spaces: " << flush;
    vector<int> days;
    string daysLine;
    getline(cin, daysLine);
    istringstream daysInput(daysLine);
    int daysValue;
    while (daysInput >> daysValue) days.push_back(daysValue);
    cout << practiceStreak(days) << endl;
    return 0;
}
