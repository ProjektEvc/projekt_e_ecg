#include HighPassFilter.h

int HighPassFilter(int data) {

    static int y1 = 0, x[66], n = 32;
    int y0;

    x[n] = x[n + 33] = data;
    y0 = y1 + x[n] - x[n + 32];
    y1 = y0;

    if(--n < 0)
        n = 32;

    return(x[n + 16] - (y0 >> 5));

}