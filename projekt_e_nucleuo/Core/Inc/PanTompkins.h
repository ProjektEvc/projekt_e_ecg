/*
 * PanTompkins.h
 *
 *  Created on: Jan 18, 2026
 *      Author: Gluscic
 */

#ifndef INC_PANTOMPKINS_H_
#define INC_PANTOMPKINS_H_

void PanTompkins();
int LowPassFilter(int data);
int HighPassFilter(int data);
int Derivative(int data);
int MovingWindowIntegral(int data);
int PeakDetection(int prev_prev_data, int prev_data, int data);
int SignalPeak(int p, int sp);
int SignalPeak2(int p, int sp);
int Threshold1(int np, int sp);
int Threshold2(int t1);
int RRAverage1(int rr);
int RRAverage2(int rr, int rr_avg2);


#endif /* INC_PANTOMPKINS_H_ */
