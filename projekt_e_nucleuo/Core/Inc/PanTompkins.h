/*
 * PanTompkins.h
 *
 *  Created on: Jan 18, 2026
 *      Author: Gluscic
 */

#ifndef PANTOMPKINS_H_
#define PANTOMPKINS_H_

#include <stdint.h>

/* Constants */
#define FS 128          // Sampling frequency
#define BUF_SIZE 64     // Buffer for peak search

/* Function Prototypes */
void PanTompkins_Init(void);
int PanTompkins_Process(int raw_sample);

#endif /* PANTOMPKINS_H_ */
