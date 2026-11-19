#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

string seatShift(int shift, const vector<int>& seats) {
    // Your code here!
    return "";
}

int main() {
    cerr << "Enter shift: " << flush;
    int shift;
    cin >> shift;
    string remainder;
    getline(cin, remainder);
    cerr << "Enter seats separated by spaces: " << flush;
    vector<int> seats;
    string seatsLine;
    getline(cin, seatsLine);
    istringstream seatsInput(seatsLine);
    int seatsValue;
    while (seatsInput >> seatsValue) seats.push_back(seatsValue);
    cout << seatShift(shift, seats) << endl;
    return 0;
}
