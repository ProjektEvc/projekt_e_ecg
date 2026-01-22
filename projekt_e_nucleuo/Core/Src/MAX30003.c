#include "MAX30003.h"
#include <stdint.h>

int MAX30003_ReadECG(SPI_HandleTypeDef *hspi)
{
    uint8_t tx_buf[4] = {0,0,0,0};
    uint8_t rx_buf[4] = {0,0,0,0};

	/* Read ECG FIFO command */
	tx_buf[0] = (0x21 << 1) | 1;   // INFO read
	tx_buf[1] = 0x00;
	tx_buf[2] = 0x00;
	tx_buf[3] = 0x00;

	MAX30003_CS_Low();

	/* We only send the FIFO read command, rest are dummy bytes */
	HAL_SPI_TransmitReceive(hspi, tx_buf,rx_buf, 4, 10000);

	MAX30003_CS_High();

    /*
     * rx_buf[1..3] contain ECG data
     * ECG FIFO data format:
     * [23:6] = ECG sample (18-bit signed)
     * [5:0]  = status bits
     */
	// 1. Combine the 3 bytes into a 24-bit unsigned container
	uint32_t raw_data = ((uint32_t)rx_buf[1] << 16) |
	                    ((uint32_t)rx_buf[2] << 8)  |
	                     (uint32_t)rx_buf[3];

	// 2. Remove the 6 status bits (ETAG/PTAG)
	// This moves the 18-bit sample into the range [17:0]
	int32_t ecg_sample = (int32_t)(raw_data >> 6);

	// 3. Handle the Sign Bit (Bit 17)
	// Since it's an 18-bit signed number, we must fill the
	// remaining 14 bits of the 32-bit integer with 1s if negative.
	if (ecg_sample & (1 << 17)) {
	    ecg_sample |= 0xFFFC0000; // Apply sign extension mask
	}

    return ecg_sample;
}

void MAX30003_CS_Low(void)
{
     HAL_GPIO_WritePin(MAX30003_CS_PORT, MAX30003_CS_PIN, GPIO_PIN_RESET);
}

void MAX30003_CS_High(void)
{
     HAL_GPIO_WritePin(MAX30003_CS_PORT, MAX30003_CS_PIN, GPIO_PIN_SET);
}

void MAX30003_Write_Register(SPI_HandleTypeDef *hspi, uint8_t addr, uint32_t data) {
    uint8_t tx_buf[4];

    // Command: (Address << 1) | 0 for Write
    tx_buf[0] = (addr << 1) | 0;
    tx_buf[1] = (uint8_t)(data >> 16);
    tx_buf[2] = (uint8_t)(data >> 8);
    tx_buf[3] = (uint8_t)(data);

    MAX30003_CS_Low();
    HAL_SPI_Transmit(hspi, tx_buf, 4, 10);
    MAX30003_CS_High();
}

void MAX30003_Init(SPI_HandleTypeDef *hspi) {
    // 1. Software Reset
    MAX30003_Write_Register(hspi, 0x08, 0x000000);
    HAL_Delay(100);

    // 2. CNFG_GEN (0x10): Osnovne postavke
    // Bit 19: EN_ECG = 1 (enable ECG channel)
    // Bits 21-20: FMSTR = 00 (32.768kHz master clock → 512sps)
    // Bits 13-12: EN_DCLOFF = 00 (disable DC lead-off detection)
    // Bits 5-4: EN_RBIAS = 01 (enable resistive bias)
    // Bits 3-2: RBIASV = 10 (200MΩ bias resistors)
    // Bit 1: RBIASP = 1 (bias ECGP)
    // Bit 0: RBIASN = 1 (bias ECGN)
    //
    // Binary: 0000 1000 0000 0000 0010 1011
    // Hex:    0x08002B
    MAX30003_Write_Register(hspi, 0x10, 0x08002B);

    HAL_Delay(150);  // Daj vremena da PLL locka

    // 3. Provjeri PLL lock (opciono)}

    // 4. CNFG_EMUX (0x14): Otvori input switcheve
    // Bit 21: OPENP = 0 (zatvori ECGP switch)
    // Bit 20: OPENN = 0 (zatvori ECGN switch)
    MAX30003_Write_Register(hspi, 0x14, 0x000000);

    // 5. CNFG_ECG (0x15): Sample rate i filteri
    // Bits 23-22: RATE = 00 (512 sps uz FMSTR=00)
    // Bits 17-16: GAIN = 00 (20V/V)
    // Bit 14: DHPF = 1 (0.5Hz high-pass filter)
    // Bits 13-12: DLPF = 01 (40Hz low-pass filter)
    //
    // Binary: 0000 0000 0101 0000 0000 0000
    // Hex:    0x005000
    MAX30003_Write_Register(hspi, 0x15, 0x005000);

    // 6. MNGR_INT (0x04): FIFO interrupt threshold
    // Bits 23-19: EFIT = 00000 (threshold = 1 sample)
    MAX30003_Write_Register(hspi, 0x04, 0x000004);

    // 7. EN_INT (0x02): Omogući FIFO interrupt (opciono)
    // Bit 23: EN_EINT = 1 (enable ECG FIFO interrupt)
    MAX30003_Write_Register(hspi, 0x02, 0x800000);

    // 8. SYNCH (0x09): Synchronize i pokreni akviziciju
    MAX30003_Write_Register(hspi, 0x09, 0x000000);

    HAL_Delay(100);  // Daj vremena da se FIFO napuni

    // 9. Flush prvi sample (može biti invalid)
    MAX30003_ReadECG(hspi);
}
