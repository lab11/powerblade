#include <msp430.h> 
#include <stdint.h>

#define RX_PIN		BIT1
#define TX_PIN		BIT0

#define I_PIN		BIT3

#define LED1_PIN	BIT7
#define LED2_PIN	BIT2
#define LED3_PIN	BIT6
#define LED1_DIR	P1DIR
#define LED2_DIR	P2DIR
#define LED3_DIR	P1DIR
#define LED1_OUT	P1OUT
#define LED2_OUT	P2OUT
#define LED3_OUT	P1OUT

// Definitions for inventory phase
#define QUERY_LEN		22
#define RN16_LEN		16
#define ACK_LEN			RN16_LEN+2
#define EPC_LEN			48
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

// Definitions for miller encoding
#define LEN_TONE		16
#define LEN_PMBL		6
#define LEN_EOS			1

#define RF_TIMEOUT		1200

//#define RN16			"1010101010101010"
#define RN16			"1111111100000000"
//#define EPC 			PC + EPC + CRC
#define EPC 			"000010000000000000010001000100011100110010101110"

typedef enum {
	rf_idle,
	rf_inInv_d0,
	rf_inInv_RTCal,
	rf_inInv_TRCal,
	rf_inInv_query,
	rf_inInv_reply
} rf_mode_t;

typedef enum {
	inv_query,
	inv_ack
} inv_mode_t;

rf_mode_t rf_mode;
inv_mode_t inv_mode;

// Globals used in preamble timing capture
uint16_t d0_len;
uint16_t rt_len;
volatile uint16_t rt_pivot;
uint16_t tr_len;
uint16_t blf;
uint16_t blf_3;

uint8_t numQueries;

// Globals used for query (from inventory round)
uint16_t query_bitcount;
uint16_t query_bitlen;
uint16_t query_bittime;
char miller_prev;
uint16_t miller_inBitCount;
char query_buf[(EPC_LEN + LEN_PMBL + LEN_EOS + LEN_TONE)*2];
char halfBit;
uint16_t txBitLen;
uint16_t txBitCount;

void miller_encode(char* buf, char* data, uint16_t len);
char string_cmp(char* buf1, char* buf2, uint16_t len);

int main(void) {
    WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

    CSCTL0_H = 0xA5;
    //CSCTL1 = DCOFSEL0 + DCOFSEL1;   			// Set 8MHz. DCO setting
    CSCTL1 = DCORSEL + DCOFSEL0 + DCOFSEL1;   	// Set max. DCO setting
    CSCTL2 = SELA_3 + SELS_3 + SELM_3;        	// set ACLK = MCLK = DCO
    CSCTL3 = DIVA_0 + DIVS_0 + DIVM_0;        	// set all dividers to 0

    // Set up LEDs as outputs
    LED1_DIR |= LED1_PIN;
    LED2_DIR |= LED2_PIN;
    LED3_DIR |= LED3_PIN;

    // Set up RX input
    P2DIR &= ~RX_PIN;							// Set RX to input
    P2SEL0 |= RX_PIN;							// Set to TB0.CCR0A
    P2SEL1 |= RX_PIN;

    // Set up TX output
    P2DIR |= TX_PIN;
    P2OUT &= ~TX_PIN;

    // Set up debug output (I_SENSE)
    P1DIR |= I_PIN;
    P1OUT &= ~I_PIN;

    // Set up timer capture
    TB0CCTL0 = CM_1 + CCIS_0 + CAP;  			// Capture on rising edge for preamble
    TB0CCTL0 &= ~CCIFG;
    TB0CTL = TBSSEL_2 + MC_2 + TBCLR + ID_2;
    TB0CCTL0 |= CCIE;
    // Set up timer timeout
    TB0CCR1 = RF_TIMEOUT;						// Timeout of 200us
    TB0CCTL1 = CCIE;

    // Initialize mode
    rf_mode = rf_idle;
    inv_mode = inv_query;
    numQueries = 0;

	//blf = 282;		// Bit time = 47us
    blf = 250;
	blf_3 = blf >> 4;

    __enable_interrupt();

    while(1) {
    	volatile unsigned long i = 0;

    	LED1_OUT ^= LED1_PIN;

    	for(i = 1000000; i > 0; i--);
    }
}

void miller_encode(char* buf, char* data, uint16_t len) {
	unsigned int i;
	for(i = 0; i < (LEN_TONE * 2); i++) {
		query_buf[i] = 0xAA;
	}

	query_buf[i++] = 0xAA;	// 0
	query_buf[i++] = 0xAA;

	query_buf[i++] = 0xAA;	// 1
	query_buf[i++] = 0x55;

	query_buf[i++] = 0x55;	// 0
	query_buf[i++] = 0x55;

	query_buf[i++] = 0x55;	// 1
	query_buf[i++] = 0xAA;

	query_buf[i++] = 0xAA;	// 1
	query_buf[i++] = 0x55;

	query_buf[i++] = 0x55;	// 1
	query_buf[i++] = 0xAA;

	unsigned int j;
	char prev = '1';
	for(j = 0; j < len; j++) {
		if(prev == '0' && data[j] == '0') {			// data == 0, prev == 0
			query_buf[i] = (query_buf[i-1] >> 1);
			if(!(query_buf[i] & 0x01)) {
				query_buf[i] |= 0x80;
			}
			i++;
			query_buf[i] = query_buf[i-1];
			i++;
		}
		else if(data[j] == '0') {					// data == 0, prev == 1
			query_buf[i] = query_buf[i-1];
			i++;
			query_buf[i] = query_buf[i-1];
			i++;
		}
		else {										// data == 1
			query_buf[i] = query_buf[i-1];
			i++;
			query_buf[i] = (query_buf[i-1] >> 1);
			if(!(query_buf[i] & 0x01)) {
				query_buf[i] |= 0x80;
			}
			i++;
		}
		prev = data[j];
	}

	// Add trailing 1
	query_buf[i] = query_buf[i-1];
	i++;
	query_buf[i] = (query_buf[i-1] >> 1);
	if(!(query_buf[i] & 0x01)) {
		query_buf[i] |= 0x80;
	}
	i++;

}

char string_cmp(char* buf1, char* buf2, uint16_t len) {
	unsigned int i;
	for(i = 0; i < len; i++) {
		if(buf1[i] != buf2[i]) {
			return 1;
		}
	}
	return 0;
}

#pragma vector=TIMERB0_VECTOR
__interrupt void TIMER_B (void) {

	// Clear interrupt
	TB0CCTL0 &= ~CCIFG;

	// Indicate RX
	//LED2_OUT ^= LED2_PIN;

	switch(rf_mode) {
	case rf_idle:
		TB0CTL |= TBCLR;
		rf_mode = rf_inInv_d0;
		break;
	case rf_inInv_d0:
		rf_mode = rf_inInv_RTCal;
		d0_len = TB0CCR0;
		rt_len = TB0CCR0;
		break;
	case rf_inInv_RTCal:
		if(inv_mode == inv_query) {
			rf_mode = rf_inInv_TRCal;
			query_bitlen = QUERY_LEN;
			query_bitcount = 0;
		}
		else {
			rf_mode = rf_inInv_query;
			query_bitlen = ACK_LEN;
			query_bittime = TB0CCR0;
			query_bitcount = 0;
		}
		rt_len = TB0CCR0 - rt_len;
		rt_pivot = rt_len >> 1;
		tr_len = TB0CCR0;
		break;
	case rf_inInv_TRCal:
		rf_mode = rf_inInv_query;
		tr_len = TB0CCR0 - tr_len;
		query_bittime = TB0CCR0;
		break;
	case rf_inInv_query:
		query_bittime = TB0CCR0 - query_bittime;
		if(query_bittime > rt_pivot) {	// Received a '1'
			query_buf[query_bitcount++] = '1';
		}
		else {
			query_buf[query_bitcount++] = '0';
		}

		if(query_bitcount == query_bitlen) { 	// Query command over
			if(inv_mode == inv_query) {
				rf_mode = rf_inInv_reply;

				// Temporarily assuming TRext = 0

//				P1OUT ^= I_PIN;
//				P1OUT ^= I_PIN;

//				numQueries++;
//				if(numQueries == 2) {
					inv_mode = inv_ack;	// Prepare for next R->T
//				}

				// Encode RN16 in M-8
				miller_encode(query_buf, RN16, RN16_LEN);

				// Set up transmit length (two bytes for each bit, 8 bits per byte)
				txBitLen = (RN16_LEN + LEN_EOS + LEN_PMBL + LEN_TONE) * 2 * 8;
				txBitCount = 0;

				// Switch to replying mode:
				TB0CTL |= TBCLR;
				TB0CCTL0 = 0;	// Turn off capture
				TB0CCR1 = 500;
				TB0CCTL1 = CCIE;
			}
			else {
 				rf_mode = rf_inInv_reply;

 				if(string_cmp(query_buf+2, RN16, RN16_LEN) == 0) {		// Valid RN16
					inv_mode = inv_query;

					miller_encode(query_buf, EPC, EPC_LEN);

					// Set up transmit length (two bytes for each bit, 8 bits per byte)
					txBitLen = (EPC_LEN + LEN_EOS + LEN_PMBL + LEN_TONE) * 2 * 8;
					txBitCount = 0;

					//Switch to replying mode
					TB0CTL |= TBCLR;
					TB0CCTL0 = 0;	// Turn off capture
					TB0CCR1 = 500;
					TB0CCTL1 = CCIE;
 				}
 				else if(string_cmp(query_buf, "1000", 4)) {				// Another query
					inv_mode = inv_ack;	// Prepare for next R->T

					// Encode RN16 in M-8
					miller_encode(query_buf, RN16, RN16_LEN);

					// Set up transmit length (two bytes for each bit, 8 bits per byte)
					txBitLen = (RN16_LEN + LEN_EOS + LEN_PMBL + LEN_TONE) * 2 * 8;
					txBitCount = 0;

					// Switch to replying mode:
					TB0CTL |= TBCLR;
					TB0CCTL0 = 0;	// Turn off capture
					TB0CCR1 = 1500;
					TB0CCTL1 = CCIE;
 				}
			}
			break;
		}
		else {
			//query_bitcount--;
			query_bittime = TB0CCR0;
			break;
		}
	}

	if(rf_mode != rf_inInv_reply) {
		// Stalve timeout
		TB0CCR1 = TB0R + RF_TIMEOUT;
		TB0CCTL1 = CCIE;
	}
}

#pragma vector=TIMERB1_VECTOR
__interrupt void TIMER_B1 (void) {

	if(rf_mode == rf_inInv_reply) {
		TB0CCTL1 &= ~CCIFG;

		uint16_t timerVal = TB0CCR1;

		__disable_interrupt();

		while(txBitCount < txBitLen) {
			timerVal += blf_3;

			uint16_t txIndex = txBitCount / 8; 			// Which byte
			char bitMask = 1 << (txBitCount % 8);		// Bit mask
			char set = query_buf[txIndex] & bitMask;

			if(set) {
				P2OUT |= TX_PIN;
				P2OUT |= TX_PIN;
			}
			else {
				P2OUT &= ~TX_PIN;
				P2OUT &= ~TX_PIN;
			}

			txBitCount++;

			while(TB0R < timerVal) {
				_nop();
			}
		}

		TB0CCTL1 = 0;						// Disable interrupt

		// Restore idle state (Set up timer capture)
		TB0CCTL0 = CM_1 + CCIS_0 + CAP;  	// Capture on rising edge for preamble
		TB0CCTL0 &= ~CCIFG;
		TB0CTL = TBSSEL_2 + MC_2 + TBCLR + ID_2;
		TB0CCTL0 |= CCIE;
		rf_mode = rf_idle;
		TB0CCR1 = RF_TIMEOUT;
		TB0CCTL1 = CCIE;

		__enable_interrupt();
	}
	else {		// Timeout
		rf_mode = rf_idle;
		P1OUT ^= I_PIN;
	}
}


