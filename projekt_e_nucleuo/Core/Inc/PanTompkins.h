/*
 * PanTompkins.h
 *
 *  Created on: Jan 18, 2026
 *      Author: Gluscic
 */

#ifndef PANTOMPKINS_H_
#define PANTOMPKINS_H_

#define REFRACTORY_SAMPLES (int)(0.2 * FS)

#include <stdint.h>

/* Constants */
#define FS 128          // Sampling frequency
#define BUF_SIZE 64     // Buffer for peak search



#include <stdio.h>

int PanTompkins(int data);


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

#endif /* PANTOMPKINS_H_ */
