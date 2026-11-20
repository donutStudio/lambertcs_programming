#include <iostream>
#include <vector>
#include <sstream>
#include <string>
using namespace std;

int droppingGrades([[maybe_unused]] const vector<int>& grades) {
    // Your code here!
    return 0;
}

int main() {
    vector<int> grades;
    int grade;
    string line;
    cerr << "Enter grades separated by spaces: " << flush;
    getline(cin, line);
    istringstream input(line);
    while (input >> grade) {
        grades.push_back(grade);
    }
    cout << droppingGrades(grades) << endl;
    return 0;
}