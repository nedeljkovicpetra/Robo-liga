#include <iostream>
using namespace std;
int main(){

    int n;
    cin >> n;

    for(int i = 0; i < 4; i++ ){
        cout << ++n << '\n';
    }

    return 0;
}