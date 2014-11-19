#include <msp430.h> 
#include <stdint.h>

#define RX_PIN		BIT1
#define TX_PIN		BIT0

#define LED1_PIN	BIT7
#define LED2_PIN	BIT2
#define LED3_PIN	BIT6
#define LED1_DIR	P1DIR
#define LED2_DIR	P2DIR
#define LED3_DIR	P1DIR
#define LED1_OUT	P1OUT
#define LED2_OUT	P2OUT
#define LED3_OUT	P1OUT

// Definitions for query command
#define QUERY_LEN	22
#define QUERY_COMMAND	0x200000
#define QUERY_COMMASK	0x3C0000
#define QUERY_DRMASK	0x020000
#define QUERY_MMASK		0x018000
#define QUERY_TRMASK	0x004000
#define QUERY_SELMASK	0x003000
#define QUERY_SESMASK	0x000C00
#define QUERY_TARMASK	0x000200
#define QUERY_QMASK		0x0001E0
#define QUERY_CRCMASK	0x00001F

typedef enum {
	rf_idle,
	rf_inInv_d0,
	rf_inInv_RTCal,
	rf_inInv_TRCal,
	rf_inInv_query,
	rf_inInv_queryReply,
	rf_inInv_queryArb,
	rf_inMsg
} rf_mode_t;

rf_mode_t rf_mode;

// Globals used in preamble timing capture
uint16_t d0_len;
uint16_t rt_len;
uint16_t rt_pivot;
uint16_t tr_len;
uint16_t blf;

// Globals used for query (from inventory round)
uint16_t query_bitcount;
uint16_t query_bittime;
char query_buf[QUERY_LEN];
char halfBit;

int main(void) {
    WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

    CSCTL0_H = 0xA5;
    CSCTL1 |= DCORSEL + DCOFSEL0 + DCOFSEL1;   // Set max. DCO setting
    CSCTL2 = SELA_3 + SELS_3 + SELM_3;        // set ACLK = MCLK = DCO
    CSCTL3 = DIVA_0 + DIVS_0 + DIVM_0;        // set all dividers to 0

    // Set up LEDs as outputs
    LED1_DIR |= LED1_PIN;
    LED2_DIR |= LED2_PIN;
    LED3_DIR |= LED3_PIN;

    // Set up RX input
    P2DIR &= ~RX_PIN;	// Set RX to input
    P2SEL0 |= RX_PIN;	// Set to TB0.CCR0A
    P2SEL1 |= RX_PIN;

    // Set up TX output
    P2DIR |= TX_PIN;
    P2OUT &= ~TX_PIN;

    // Set up debug output (I_SENSE)
    P1DIR |= BIT3;

    // Set up timer capture
    TB0CCTL0 = CM_1 + CCIS_0 + CAP;  	// Capture on rising edge for preamble
    TB0CCTL0 &= ~CCIFG;
    TB0CTL = TBSSEL_2 + MC_2 + TBCLR + ID_2;
    TB0CCTL0 |= CCIE;

    // Initialize mode
    rf_mode = rf_idle;

    __enable_interrupt();

    while(1) {
    	volatile unsigned long i = 0;

    	LED1_OUT ^= LED1_PIN;

    	for(i = 1000000; i > 0; i--);
    }
}

#pragma vector=TIMERB0_VECTOR
__interrupt void TIMER_B (void) {

	// Clear interrupt
	TB0CCTL0 &= ~CCIFG;

	// Indicate RX
	LED2_OUT ^= LED2_PIN;
	P1OUT ^= BIT3;

	switch(rf_mode) {
	case rf_idle:
		rf_mode = rf_inInv_d0;
		TB0CTL |= TBCLR;
		//d0_len = TB0CCR0;
		d0_len = 0;
		break;
	case rf_inInv_d0:
		rf_mode = rf_inInv_RTCal;
		d0_len = TB0CCR0 - d0_len;
		rt_len = TB0CCR0;
		break;
	case rf_inInv_RTCal:
		rf_mode = rf_inInv_TRCal;
		rt_len = TB0CCR0 - rt_len;
		rt_pivot = rt_len >> 1;
		tr_len = TB0CCR0;
		break;
	case rf_inInv_TRCal:
		rf_mode = rf_inInv_query;
		tr_len = TB0CCR0 - tr_len;
		blf = 125;
		query_bitcount = QUERY_LEN - 1;
		query_bittime = TB0CCR0;
		break;
	case rf_inInv_query:
		query_bittime = TB0CCR0 - query_bittime;
		if(query_bittime > rt_pivot) {	// Received a '1'
			query_buf[query_bitcount] = 1;
		}
		else {
			query_buf[query_bitcount] = 0;
		}

		if(query_bitcount == 0) { 	// Query command over
			//if((query_buf && QUERY_COMMASK) == QUERY_COMMAND) {
				//if((query_buf && QUERY_QMASK) == 0) {
					rf_mode = rf_inInv_queryReply;

					// Switch to replying mode:
					TB0CTL |= TBCLR;
					TB0CCTL0 = CCIE;	// Set to compare mode
					//TB0CCR0 = rt_len;	// Set to tx time
					TB0CCR0 = 1500;

					memcpy(query_buf, "1111111111111111110101", QUERY_LEN);
					query_bitcount = QUERY_LEN;
					halfBit = 0;

					P1OUT ^= BIT3;
					P1OUT ^= BIT3;
					break;
				//}
			//}
		}
		else {
			query_bitcount--;
			query_bittime = TB0CCR0;
			break;
		}
	case rf_inInv_queryReply:

		if(query_bitcount == 0) {
			P2OUT &= ~TX_PIN;
			P2OUT &= ~TX_PIN;
			rf_mode = rf_idle;
			break;
		}

		if(query_bitcount != 18) {
			P2OUT ^= TX_PIN;
		}
		TB0CCR0 = blf;

		if(query_buf[--query_bitcount] == '0') {
			TB0CCR1 = (blf >> 1);
			TB0CCTL1 = CCIE;
		}

		TB0CTL |= TBCLR;
		break;
	}
}

#pragma vector=TIMERB1_VECTOR
__interrupt void TIMER_B1 (void) {
	TB0CCTL1 = 0;
	P2OUT ^= TX_PIN;
}


