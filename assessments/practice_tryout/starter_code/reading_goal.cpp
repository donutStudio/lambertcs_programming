#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

int readingGoal([[maybe_unused]] int goal, [[maybe_unused]] const vector<int>& pages) {
    // Your code here!
    return 0;
}

int main() {
    cerr << "Enter goal: " << flush;
    int goal;
    cin >> goal;
    string remainder;
    getline(cin, remainder);
    cerr << "Enter pages separated by spaces: " << flush;
    vector<int> pages;
    string pagesLine;
    getline(cin, pagesLine);
    istringstream pagesInput(pagesLine);
    int pagesValue;
    while (pagesInput >> pagesValue) pages.push_back(pagesValue);
    cout << readingGoal(goal, pages) << endl;
    return 0;
}
