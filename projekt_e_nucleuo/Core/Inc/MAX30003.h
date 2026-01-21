/*
 * MAX30003.h
 *
 *  Created on: Jan 18, 2026
 *      Author: glusc
 */

#ifndef MAX30003_H
#define MAX30003_H

#include "main.h"
#include "stm32g4xx_hal.h"

// CS Pin Definition - adjust to match your hardware
#define MAX30003_CS_PORT GPIOC
#define MAX30003_CS_PIN  GPIO_PIN_9


int MAX30003_ReadECG(SPI_HandleTypeDef *hspi);
void MAX30003_CS_Low(void);
void MAX30003_CS_High(void);
void MAX30003_Init(SPI_HandleTypeDef *hspi);
void MAX30003_Write_Register(SPI_HandleTypeDef *hspi, uint8_t addr, uint32_t data);

#endif /* MAX30003_H */
