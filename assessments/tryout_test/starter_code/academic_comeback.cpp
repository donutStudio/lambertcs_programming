#include <iostream>
#include <vector>
using namespace std;

int academicComeback([[maybe_unused]] const vector<int>& grades) {
    // Your code here!
    return 0;
}

int main() {
    vector<int> grades;
    int grade;
    cerr << "Enter grades separated by spaces, then press EOF: " << flush;
    // Enter grades, then choose EOF in the terminal to finish input.
    while (cin >> grade) {
        grades.push_back(grade);
    }
    cout << academicComeback(grades) << endl;
    return 0;
}