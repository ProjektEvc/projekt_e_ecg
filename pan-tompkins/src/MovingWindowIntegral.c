#include MovingWindowIntegral.h

int MovingWindowIntegral(int data){

    static int x[32], i = 0;
    static long sum = 0;
    long ly;
    int y;

    if(++i == 32)
        i = 0;
    sum -= x[i];
    sum += data;
    x[i] = data;
    ly = sum >> 5;
    
    if(ly > 32400)
        y = 32400;
    else
        y = (int) ly;

    return(y);

}