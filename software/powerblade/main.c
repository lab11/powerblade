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
#define EPC_LEN			66
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

//#define RN16			"1010101010101010"
#define RN16			"1111111100000000"

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
uint16_t blf_3;

// Globals used for query (from inventory round)
uint16_t query_bitcount;
uint16_t query_bittime;
char miller_prev;
uint16_t miller_inBitCount;
char query_buf[EPC_LEN + LEN_PMBL + LEN_EOS + LEN_TONE];
char halfBit;
uint16_t txBitLen;
uint16_t txBitCount;

uint16_t responseCount;

void miller_encode(char* buf, char* data, uint16_t len);

int main(void) {
    WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

    CSCTL0_H = 0xA5;
    //CSCTL1 = DCOFSEL0 + DCOFSEL1;   			// Set 8MHz. DCO setting
    CSCTL1 = DCORSEL + DCOFSEL0 + DCOFSEL1;   // Set max. DCO setting
    CSCTL2 = SELA_3 + SELS_3 + SELM_3;        // set ACLK = MCLK = DCO
    CSCTL3 = DIVA_0 + DIVS_0 + DIVM_0;        // set all dividers to 0

//    P2OUT = 0;                              // output ACLK
//    P2DIR |= BIT0;
//    P2SEL1 |= BIT0;
//    P2SEL0 |= BIT0;

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

    responseCount = 0;

    // Set up debug output (I_SENSE)
    P1DIR |= I_PIN;
    P1OUT &= ~I_PIN;

    // Set up timer capture
    TB0CCTL0 = CM_1 + CCIS_0 + CAP;  	// Capture on rising edge for preamble
    TB0CCTL0 &= ~CCIFG;
    TB0CTL = TBSSEL_2 + MC_2 + TBCLR + ID_2;
    TB0CCTL0 |= CCIE;

    // Initialize mode
    rf_mode = rf_idle;

//	rf_mode = rf_inInv_query;

	//blf = 282;		// Bit time = 47us
    blf = 250;
	blf_3 = blf >> 4;

	// Switch to replying mode:
//	TB0CTL |= TBCLR;
//	TB0CCR0 = 1500;
//	TB0CCTL0 = CCIE;	// Set to compare mode
//	TB0CCTL0 &= ~CCIFG;
//	TB0CCTL0 &= ~CCIFG;
	//TB0CCR0 = rt_len;	// Set to tx time
//	miller_prev = 1;

//	query_buf[0] = 0;
//	query_buf[1] = 1;
//	query_buf[2] = 1;
//	//memcpy(query_buf, "1111111111111111110101", QUERY_LEN);
//	//query_bitcount = QUERY_LEN;
//	query_bitcount = 0;

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

//	query_buf[i++] = 0xAA;	// 1 (RN16)
//	query_buf[i++] = 0x55;

	unsigned int j;
	char prev = '1';
	for(j = 0; j < len; j++) {
		if(prev == '0' && data[j] == '0') {
			query_buf[i] = (query_buf[i-1] >> 1);
			if(!(query_buf[i] & 0x01)) {
				query_buf[i] |= 0x80;
			}
			i++;
			query_buf[i] = query_buf[i-1];
			i++;
		}
		else if(prev == '0' && data[j] == '1') {
			query_buf[i] = query_buf[i-1];
			i++;
			query_buf[i] = (query_buf[i-1] >> 1);
			if(!(query_buf[i] & 0x01)) {
				query_buf[i] |= 0x80;
			}
			i++;
		}
		else if(data[j] == '0') {	// prev == 1
			query_buf[i] = query_buf[i-1];
			i++;
			query_buf[i] = query_buf[i-1];
			i++;
		}
		else {
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

	query_buf[i] = query_buf[i-1];
	i++;
	query_buf[i] = (query_buf[i-1] >> 1);
	if(!(query_buf[i] & 0x01)) {
		query_buf[i] |= 0x80;
	}
	i++;

//	query_buf[22] = 0x55;	// 1 (EOS)
//	query_buf[23] = 0xAA;
}

#pragma vector=TIMERB0_VECTOR
__interrupt void TIMER_B (void) {

	// Clear interrupt
	//TB0CCTL0 &= ~CCIFG;

	// Indicate RX
	//LED2_OUT ^= LED2_PIN;
	//P1OUT ^= BIT3;

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

					// Temporarily assuming TRext = 0

					miller_encode(query_buf, RN16, RN16_LEN);
//					unsigned int i;
//					for(i = 0; i < 8; i++) {
//						query_buf[i] = 0xAA;
//					}
//					query_buf[8] = 0xAA;	// 0
//					query_buf[9] = 0xAA;
//
//					query_buf[10] = 0xAA;	// 1
//					query_buf[11] = 0x55;
//
//					query_buf[12] = 0x55;	// 0
//					query_buf[13] = 0x55;
//
//					query_buf[14] = 0x55;	// 1
//					query_buf[15] = 0xAA;
//
//					query_buf[16] = 0xAA;	// 1
//					query_buf[17] = 0x55;
//
//					query_buf[18] = 0x55;	// 1
//					query_buf[19] = 0xAA;
//
//					query_buf[20] = 0xAA;	// 1 (RN16)
//					query_buf[21] = 0x55;
//
//					query_buf[22] = 0x55;	// 1 (EOS)
//					query_buf[23] = 0xAA;

					txBitLen = (RN16_LEN + LEN_EOS + LEN_PMBL + LEN_TONE) * 2 * 8;
					txBitCount = 0;

					// Switch to replying mode:
					//TB0CTL |= TBCLR;
					TB0CCTL0 = 0;	// Turn off capture
					TB0CCR1 = TB0CCR0 + 800;
					TB0CCTL1 = CCIE;

					//TB0CCR0 = rt_len;	// Set to tx time
					//miller_prev = 0;

					//memcpy(query_buf, "1111111111111111110101", QUERY_LEN);
					//query_bitcount = QUERY_LEN;
					//query_bitcount = 6;
					//halfBit = 0;

//					P1OUT ^= BIT3;
//					P1OUT ^= BIT3;
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
			while(1);
			break;
		}

		uint16_t capture = TB0CCR0;
		TB0CCR1 = capture + blf_3;
		TB0CCR0 = capture + blf;

		// FM0 Encoding
//		if(query_bitcount != 18) {
//			P2OUT ^= TX_PIN;
//		}
//		if(query_buf[--query_bitcount] == '0') {
//			TB0CCR1 = (blf >> 1);
//			TB0CCTL1 = CCIE;
//		}

		char txChar = query_buf[--query_bitcount];

		// Miller 2 Encoding
		if(!(miller_prev == 0 & txChar == 0)) {
			P2OUT ^= TX_PIN;	// Toggle at bit transition unless 0->0
		}

		TB0CCTL1 = CCIE;
		miller_prev = txChar;
		miller_inBitCount = 0;

		//TB0CTL |= TBCLR;
		break;
	}
}

#pragma vector=TIMERB1_VECTOR
__interrupt void TIMER_B1 (void) {

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

	TB0CCTL1 = 0;	// Disable interrupt
	// Set up timer capture
	TB0CCTL0 = CM_1 + CCIS_0 + CAP;  	// Capture on rising edge for preamble
	TB0CCTL0 &= ~CCIFG;
	TB0CTL = TBSSEL_2 + MC_2 + TBCLR + ID_2;
	TB0CCTL0 |= CCIE;
	rf_mode = rf_idle;

	responseCount++;
	if(responseCount == 2) {
		responseCount = 0;
	}

	__enable_interrupt();

//
//	if(miller_inBitCount < 3 | (miller_inBitCount > 3 && miller_inBitCount < 6)) {
//		P2OUT ^= TX_PIN;
//	}
//	else if(miller_inBitCount == 3) {
//		if(query_buf[query_bitcount] == 0) {
//			P2OUT ^= TX_PIN;
//		}
//	}
//	else if(miller_inBitCount == 6) {
//		P2OUT ^= TX_PIN;
//		TB0CCTL1 = 0;
//	}
//	miller_inBitCount++;
}


