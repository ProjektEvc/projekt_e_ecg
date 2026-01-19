/*
 * MAX30003.h
 *
 *  Created on: Jan 18, 2026
 *      Author: glusc
 */


/*
 * Ako je CS (Chip select) low, onda je SPI aktivan
 *
 *
 *
 *
 *
 *
 */
#ifndef MAX30003_H
#define MAX30003_H

#define MAX30003_CS_PORT GPIOA
#define MAX30003_CS_PIN  GPIO_PIN_4

static void MAX30003_CS_Low(void);

static void MAX30003_CS_High(void);

int MAX30003_ReadECG(void);

#endif
