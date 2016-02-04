#include <msp430.h>
#include <stdint.h>
#include <stdbool.h>

#include "uart.h"
#include "checksum.h"

//void uart_send(char* buf, unsigned int len);
char* txBufSave;
unsigned int txLen;
int txCt;

int capCt;

void uart_init(void) {
	UCA0CTL1 |= UCSWRST;						// Put UART into reset
	UCA0CTL1 |= UCSSEL_1;						// Set to SMCLK
	UCA0BR0 = 3;								// Baud configuration for 9600
	UCA0BR1 = 0;
	UCA0MCTLW = 0x9200;
//    UCA0BR0 = 104;								// Baud configuration for 38400
//    UCA0BR1 = 0;
//    UCA0MCTLW = 0x1100;
//	UCA0BR0 = 34;								// Baud configuration for 115200
//	UCA0BR1 = 0;
//	UCA0MCTLW = 0xBB00;
	UCA0CTL1 &= ~UCSWRST;						// Take UART out of reset
	UCA0IE |= UCRXIE;// + UCTXCPTIE;				// Enable RX, TX Complete interrupts

	// Initialize UART receive count
	rxCt = 0;
}

void uart_enable(bool enable) {
	if (enable) {
		P2SEL1 |= BIT0 + BIT1;
	} else {
		P2SEL1 &= ~(BIT0 + BIT1);
	}
}

void uart_stuff(unsigned int offset, char* srcbuf, unsigned int len) {
	// XXX can i just use len (without tempCt)?
	int tempCt = len - 1;
	while(tempCt >= 0) {
		txBuf[offset++] = srcbuf[tempCt--];
	}
}

void uart_send(int offset, uint16_t uart_len) {
	txBufSave = txBuf + offset;

	// Calculate checksum and append to buffer
	txLen = uart_len;
	txBufSave[txLen-1] = additive_checksum((uint8_t*)txBufSave, txLen-1);

	// Enable interrupt and transmit
	UCA0IE |= UCTXIE;
	txCt = 0;
	UCA0TXBUF = txBufSave[txCt++];
}

int processMessage(void) {
	// Check if message is long enough
	if(rxCt <= 2) {
		return 0;
	}

	// Capture rx length
	int rxLen = (rxBuf[0] << 8) + rxBuf[1];

	// Check if we have received the entire message
	if(rxLen > rxCt) {
		return 0;
	}

	int rxIndex;
	capCt = 0;
	if(additive_checksum((uint8_t*)rxBuf, rxLen - 1) == rxBuf[rxLen - 1]){

		captureType = rxBuf[2];

		// Get all bytes but checksum
		for(rxIndex = 3; rxIndex < (rxLen-1); rxIndex++){
			captureBuf[capCt++] = rxBuf[rxIndex];
		}
	}
	rxCt = 0;

	return capCt + 1;
}

#pragma vector=USCI_A0_VECTOR
__interrupt void USCI_A0_ISR(void) {

	switch (__even_in_range(UCA0IV, 8)) {
	case 0:
		break;								// No interrupt
	case 2: 								// RX interrupt
		P1OUT |= (BIT2 + BIT3);
		rxBuf[rxCt++] = UCA0RXBUF;
		P1OUT &= ~(BIT2 + BIT3);
		break;
	case 4:									// TX interrupt
		if (txCt < txLen) {
			UCA0TXBUF = txBufSave[txCt++];
		} else {
			UCA0IE &= ~UCTXIE;
			UCA0IE |= UCTXCPTIE;
		}
		break;
	case 6:
		break;								// Start bit received
	case 8: 								// Transmit complete
		UCA0IE &= ~UCTXCPTIE;
		break;
	default:
		break;
	}

}


