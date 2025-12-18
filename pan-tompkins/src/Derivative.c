#include Derivative.h

int Derivative(int data){

    int y, i;
    static int x_d[4];

    y = (data << 1) + x_d[3] - x_d[1] - (x_d[0] << 1;)

    y >>= 3;
    for (i = 0; i < 3; i++)
        x_d[i] = x_d[i + 1];
    x_d[3] = data;

    return(y);

}