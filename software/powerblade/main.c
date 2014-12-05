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
#define EPC_LEN			80
#define EPC_BASE_LEN	64
#define EPC_ADD_LEN		16
#define CRC_LEN			16

// Definitions for miller encoding
#define LEN_TONE		16
#define LEN_PMBL		6
#define LEN_EOS			1

#define RF_TIMEOUT		1200

//#define POLY 			0x8408
#define P_CCITT     	0x1021

//#define RN16			"1010101010101010"
#define RN16_BITS		0xFACE
//#define RN16			"1111101011001110"
//#define EPC1_BITS		0x2000111122223333
#define EPC1_BITS		0x2000B00B00000000
uint16_t crc_base_bits;
uint16_t crc_bits;
//#define EPC 			"00001000000000000001000100010001"

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

uint16_t tx_count;

// Globals used for query (from inventory round)
uint16_t query_bitcount;
uint16_t query_bitlen;
uint16_t query_bittime;
char query_buf[(RN16_LEN + LEN_PMBL + LEN_EOS + LEN_TONE)*2];
char epc_buf[(EPC_LEN + CRC_LEN + LEN_PMBL + LEN_EOS + LEN_TONE)*2];
uint16_t txBitLen;
uint16_t txBitCount;

void miller_encode(char buf[], unsigned int qOffset, char* data, uint16_t len);
char string_cmp(char* buf1, char* buf2, uint16_t len);
uint16_t calc_crc(uint16_t crc_start, char* dat, unsigned short len);

static unsigned short   crc_tabccitt[256];
static void init_crcccitt_tab( void ) {

    int i, j;
    unsigned short crc, c;

    for (i=0; i<256; i++) {

        crc = 0;
        c   = ((unsigned short) i) << 8;

        for (j=0; j<8; j++) {

            if ( (crc ^ c) & 0x8000 ) crc = ( crc << 1 ) ^ P_CCITT;
            else                      crc =   crc << 1;

            c = c << 1;
        }

        crc_tabccitt[i] = crc;
    }

}

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

	//blf = 282;		// Bit time = 47us
    blf = 250;
	blf_3 = blf >> 4;

	tx_count = 0;

	init_crcccitt_tab();
	const uint64_t epc_temp1_bits = EPC1_BITS;
	//const uint64_t epc_temp2_bits = EPC2_BITS;
	//crc_bits = calc_crc("08001111", 4);
	//calc_crc("100011112222", 12);
	miller_encode(epc_buf, 0, (char*)&epc_temp1_bits, EPC_BASE_LEN / 8);
	//miller_encode(epc_buf, EPC_BASE1_LEN, (char*)&epc_temp2_bits, EPC_BASE2_LEN / 8);
	crc_base_bits = calc_crc(0x0000, (char*)&epc_temp1_bits, EPC_BASE_LEN / 8);
	//crc_bits = calc_crc(crc_bits, (char*)&epc_temp2_bits, EPC_BASE2_LEN / 8);

    __enable_interrupt();

    while(1) {
    	volatile unsigned long i = 0;

    	LED1_OUT ^= LED1_PIN;

    	for(i = 1000000; i > 0; i--);
    }
}

void miller_encode(char buf[], unsigned int qOffset, char* data, uint16_t len) {
	unsigned int i = qOffset*2;
	if(len != 0 && i == 0) {
		for(i = 0; i < (LEN_TONE * 2); i++) {
			buf[i] = 0xAA;
		}

		buf[i++] = 0xAA;	// 0
		buf[i++] = 0xAA;

		buf[i++] = 0xAA;	// 1
		buf[i++] = 0x55;

		buf[i++] = 0x55;	// 0
		buf[i++] = 0x55;

		buf[i++] = 0x55;	// 1
		buf[i++] = 0xAA;

		buf[i++] = 0xAA;	// 1
		buf[i++] = 0x55;

		buf[i++] = 0x55;	// 1
		buf[i++] = 0xAA;
	}
	else {
		i = i + ((LEN_TONE + LEN_PMBL)*2);
	}

	int j, k;
	char cur;
	char bit;
	char prev = 1;
	for(j = len-1; j >= 0; j--) {
		cur = data[j];
		for(k = 7; k >= 0; k--) {
			bit = (cur >> k) & 0x01;
			if(prev == 0 && bit == 0) {			// data == 0, prev == 0
				buf[i] = (buf[i-1] >> 1);
				if(!(buf[i] & 0x01)) {
					buf[i] |= 0x80;
				}
				i++;
				buf[i] = buf[i-1];
				i++;
			}
			else if(bit == 0) {					// data == 0, prev == 1
				buf[i] = buf[i-1];
				i++;
				buf[i] = buf[i-1];
				i++;
			}
			else {										// data == 1
				buf[i] = buf[i-1];
				i++;
				buf[i] = (buf[i-1] >> 1);
				if(!(buf[i] & 0x01)) {
					buf[i] |= 0x80;
				}
				i++;
			}
			prev = bit;
		}
	}

	if(len == 0) {
		// Add trailing 1
		buf[i] = buf[i-1];
		i++;
		buf[i] = (buf[i-1] >> 1);
		if(!(buf[i] & 0x01)) {
			buf[i] |= 0x80;
		}
		i++;
	}
}

char string_cmp(char* buf1, char* buf2, uint16_t len) {
	int i, j;
	char cur;
	for(i = 0; i < len; i++) {
		cur = buf2[len - 1 - i];
		for(j = 7; j >= 0; j--) {
			char temp1 = buf1[(i*8) + (7-j)];
			char temp2 = (((cur >> j) & 0x01) + '0');
			if(temp1 != temp2) {
				return 1;
			}
		}
	}
	return 0;
}

uint16_t calc_crc(uint16_t crc_start, char* dat, unsigned short len) {
	//unsigned char i;
	//volatile unsigned int data;
	unsigned short tmp, short_c;
	volatile unsigned int crc;

	crc = ~crc_start;
	//len >>= 1;

	do {
//		unsigned short c1 = (unsigned short)((*dat++ - '0') << 4);
//		unsigned short c2 = (unsigned short)(*dat++ - '0');
//		short_c = (unsigned short)(c1 | c2);//(0x00ff & (unsigned short)*dat) - '0';
		short_c = (unsigned short)(*(dat + len - 1));
//		dat += temp;
//		short_c = 0x0000;

		tmp = (crc >> 8) ^ short_c;
		crc = (crc << 8) ^ crc_tabccitt[tmp];

//		data = (unsigned int)0xff & *dat++;
//		crc ^= data;
//		//data = 0x0000;
//		for(i = 0; i < 8; i++, data >>= 1) {
//			if(crc & 0x0001) {
//				crc = (crc >> 1) ^ POLY;
//			}
//			else {
//				crc = (crc >> 1);
//			}
//		}
	} while(--len);

	crc = ~crc;

//	data = crc;
//	crc = (crc << 8) | (data >> 8 & 0xFF);

	return crc;
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

				inv_mode = inv_ack;	// Prepare for next R->T

				// Encode RN16 in M-8
				const uint16_t rn16_bits = RN16_BITS;
				miller_encode(query_buf, 0, (char*)&rn16_bits, RN16_LEN / 8);
				miller_encode(query_buf, RN16_LEN, 0x0, 0);

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

 				const uint16_t rn16_bits = RN16_BITS;
 				if(string_cmp(query_buf+2, (char*)&rn16_bits, RN16_LEN / 8) == 0) {		// Valid RN16
					inv_mode = inv_query;

					// Encode EPC in M-8
					//const uint64_t epc_bits = EPC_BITS;
//					miller_encode(query_buf, 0, (char*)&epc_bits, EPC_BASE_LEN / 8);
					//const uint16_t epc2_bits = 0x6666;
					miller_encode(epc_buf, EPC_BASE_LEN, (char*)&tx_count, EPC_ADD_LEN / 8);
					crc_bits = calc_crc(crc_base_bits, (char*)&tx_count, EPC_ADD_LEN / 8);
					tx_count++;
					miller_encode(epc_buf, EPC_BASE_LEN + EPC_ADD_LEN, (char*)&crc_bits, CRC_LEN / 8);
					miller_encode(epc_buf, EPC_BASE_LEN + EPC_ADD_LEN + CRC_LEN, 0x0, 0);

					// Set up transmit length (two bytes for each bit, 8 bits per byte)
					txBitLen = (EPC_LEN + CRC_LEN + LEN_EOS + LEN_PMBL + LEN_TONE) * 2 * 8;
					txBitCount = 0;

					P1OUT ^= I_PIN;
					P1OUT ^= I_PIN;

					//Switch to replying mode
					TB0CTL |= TBCLR;
					TB0CCTL0 = 0;	// Turn off capture
					TB0CCR1 = 500;
					TB0CCTL1 = CCIE;
 				}
 				else if(string_cmp(query_buf, "8", 1)) {				// Another query
					inv_mode = inv_ack;	// Prepare for next R->T

					// Encode RN16 in M-8
					const uint16_t rn16_bits = RN16_BITS;
					miller_encode(query_buf, 0, (char*)&rn16_bits, RN16_LEN / 8);
					miller_encode(query_buf, RN16_LEN, 0x0, 0);

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
		char *buf;
		TB0CCTL1 &= ~CCIFG;

		if(inv_mode == inv_query) {
			buf = epc_buf;
		}
		else {
			buf = query_buf;
		}

		uint16_t timerVal = TB0CCR1;

		__disable_interrupt();

		while(txBitCount < txBitLen) {
			timerVal += blf_3;

			uint16_t txIndex = txBitCount / 8; 			// Which byte
			char bitMask = 1 << (txBitCount % 8);		// Bit mask
			char set = buf[txIndex] & bitMask;

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


