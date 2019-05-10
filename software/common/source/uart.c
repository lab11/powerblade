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

static void uart_setBaud_9600(void) {
    // put UART into reset
    UCA0CTL1 |= UCSWRST;

    // baud configuration for 9600 baud off of 32 kHz clock
    UCA0CTL1 &= ~UCSSEL_3; // Clear clock bits
    UCA0CTL1 |= UCSSEL_1; // ACLK source (32 kHz)
    UCA0BR0 = 3;
    UCA0BR1 = 0;
    UCA0MCTLW = 0x9200;

    // take UART out of reset, clear pending interrupts, and enable RX interrupts
    UCA0CTL1 &= ~UCSWRST;
    UCA0IV = 0;
    UCA0IE |= UCRXIE;
}

static void uart_setBaud_232400(void) {

    // put UART into reset
    UCA0CTL1 |= UCSWRST;

    // baud configuration for 232400 baud off of 4 MHz clock
    UCA0CTL1 &= ~UCSSEL_3; // Clear clock bits
    UCA0CTL1 |= UCSSEL_3; // SMCLK source (4 MHz)
    UCA0BR0 = 17;
    UCA0BR1 = 0;
    UCA0MCTLW = 0x4A00;

    // take UART out of reset, clear pending interrupts, and enable TX interrupts
    UCA0CTL1 &= ~UCSWRST;
    UCA0IV = 0;
    UCA0IE |= UCTXIE;
}

void uart_init(void) {

    // We can only receive in sleep mode while running at 9600 baud
    uart_setBaud_9600();

	// Initialize UART receive count
	rxCt = 0;
	savedCount = 0;
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

    // Reconfigure TX parameters
    txCt = 0;
    // Add a bonus garbage byte so change baudrates doesn't mess up the checksum
    txLen = uart_len+1;

	// Calculate checksum and append to buffer
	txBufSave = txBuf + offset;
	txBufSave[uart_len-1] = additive_checksum((uint8_t*)txBufSave, uart_len-1);

    P1OUT &= ~BIT2;

    // switch to high-speed UART (232400 baud)
    uart_setBaud_232400();

	// begin transmitting
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
		P1OUT ^= BIT2;
		rxBuf[rxCt++] = UCA0RXBUF;
		P1OUT ^= BIT2;
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

	    // switch to low-speed UART (9600 baud)
		// note that doing this here will screw up the last couple bits of the
		// transmission, which is why we send a bonus garbage byte
		uart_setBaud_9600();
	    P1OUT |= BIT2;
		break;
	default:
		break;
	}

}


