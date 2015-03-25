/*
 * calibrate_ct
 *
 * The purpose of this app is to determine the slope and offset of the
 * relationship between metered current and peak to peak voltage of
 * the current sense channel
 *
 * Reported values at 1Hz:
 * 	   PowerBlade ID:	1 byte
 * 	            Ippk:	4 bytes		(average over last 10 seconds)
 * 	            Ippk:	4 bytes		(average over last 1 second)
 */

#include <msp430.h> 

#include <stdint.h>
//#include <stdbool.h>
//#include <math.h>

#include "powerblade_test.h"

uint8_t data;

// Count each sample and 60Hz measurement
uint8_t sampleCount;
uint8_t measCount;

// Global variables used interrupt-to-interrupt
int8_t current;
int8_t voltage;
uint32_t acc_i_ave;
uint32_t acc_v_ave;
uint32_t i_ave;
uint32_t v_ave;
uint8_t i_min;
uint16_t i_max;
uint16_t v_min;
uint32_t v_max;

// Transmitted values
uint32_t sequence;

// Variables used to center both waveforms at Vcc/2-ish
uint8_t isense_vmax;
uint8_t isense_vmin;
uint8_t vsense_vmax;
uint8_t vsense_vmin;

void uart_send(char* buf, unsigned int len);
char *txBuf;
unsigned int txLen;
unsigned int txCt;

/*
 * main.c
 */
int main(void) {
    WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

    // XT1 Setup
    PJSEL0 |= BIT4 + BIT5;

    CSCTL0_H = 0xA5;
  	CSCTL1 = DCOFSEL0 + DCOFSEL1;             // Set max. DCO setting
  	CSCTL2 = SELA_0 + SELS_3 + SELM_3;        // set ACLK = XT1; MCLK = DCO
  	CSCTL3 = DIVA_0 + DIVS_1 + DIVM_1;        // set all dividers
  	CSCTL4 |= XT1DRIVE_0;
  	CSCTL4 &= ~XT1OFF;

  	do
  	{
    	CSCTL5 &= ~XT1OFFG;					  // Clear XT1 fault flag
    	SFRIFG1 &= ~OFIFG;
  	}while (SFRIFG1&OFIFG);                   // Test oscillator fault flag

    // Low power in port J
    PJDIR = 0;
    PJOUT = 0;
    PJREN = 0xFF;

    // Low power in port 1
    P1DIR = BIT2 + BIT6;
    P1OUT = 0;
    P1REN = 0xFF;

    // Low power in port 2
    P2DIR = 0;
    P2OUT = 0;
    P2REN = 0xFF;

    __delay_cycles(4000);                      // ref delay

    // Set SEN_EN to output and enable (~200uA)
    SEN_EN_DIR |= SEN_EN_PIN;
    SEN_EN_OUT |= SEN_EN_PIN;

    // Zero all sensing values
    sampleCount = 0;
    measCount = 0;
    acc_i_ave = 0;
    acc_v_ave = 0;
    i_ave = 0;
    v_ave = 0;
    sequence = 0;

    // Vmid values are initally set to defaults, adjusted during run
    vsense_vmax = 0;
    vsense_vmin = 255;
    isense_vmax = 0;
    isense_vmin  = 255;

    // Set SYS_EN to output and enable
    SYS_EN_DIR |= SYS_EN_PIN;
    SYS_EN_OUT |= SYS_EN_PIN;

    // Set up UART
    P2SEL0 &= ~(BIT0);
    P2SEL1 |= BIT0;
    UCA0CTL1 |= UCSWRST;
    UCA0CTL1 |= UCSSEL_2;
//    UCA0BR0 = 52;
//    UCA0BR1 = 0;
//    UCA0MCTLW = 0x0200;
    UCA0BR0 = 104;
    UCA0BR1 = 0;
    UCA0MCTLW = 0x1100;
    UCA0CTL1 &= ~UCSWRST;
    UCA0IE |= UCRXIE + UCTXCPTIE;

    // Enable ADC for VCC_SENSE, I_SENSE, V_SENSE
    P1SEL1 |= BIT3 + BIT4 + BIT5;
    P1SEL0 |= BIT3 + BIT4 + BIT5;
	ADC10CTL0 |= ADC10ON;// + ADC10MSC;          	// ADC10ON
  	ADC10CTL1 |= ADC10SHS_0 + ADC10SHP + ADC10CONSEQ_3;  	// rpt series of ch; TA0.1 trig sample start
  	ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
  	ADC10MCTL0 |= ADC10INCH_5 + ADC10SREF_0;  	// A3,4,5 ADC input select; Vref=AVCC

  	ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
  	ADC10IE |= ADC10IE0;                       	// Enable ADC conv complete interrupt
  
  	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
  	TA0CCR0 = 9;						// PWM Period
  	TA0CCR1 = 2;                     	// TA0.1 ADC trigger
  	TA0CCTL1 = OUTMOD_7 + CCIE;                       	// TA0CCR0 toggle
  	TA0CTL = TASSEL_1 + MC_1 + TACLR;          	// ACLK, up mode

  	__bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts

	return 0;
}

#pragma vector=TIMER0_A1_VECTOR
__interrupt void TIMERA0_ISR(void) {
	TA0CCTL1 &= ~CCIFG;
	//P2OUT ^= BIT0;
	ADC10CTL0 += ADC10SC;
}

void uart_send(char* buf, unsigned int len) {
	txBuf = buf;
	txLen = len;
	txCt = 0;

	UCA0IE |= UCTXIE;
	if(txCt < txLen) {
		UCA0TXBUF = buf[txCt++];
	}
}

#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR(void) {

	uint8_t ADC_Result;
	unsigned char ADC_Channel;

	switch(__even_in_range(ADC10IV,12)) {
    case  0: break;                          // No interrupt
    case  2: break;                          // conversion result overflow
    case  4: break;                          // conversion time overflow
    case  6: break;                          // ADC10HI
    case  8: break;                          // ADC10LO
    case 10: break;                          // ADC10IN
    case 12: ADC_Result = ADC10MEM0;
    	ADC_Channel = ADC10MCTL0 & ADC10INCH_7;
    	switch(ADC_Channel) {
    	case 4:	// I_SENSE
    		// Reset timer to sample these three quickly
    		TA0CCR0 = 2;

    		// Set debug pin
    		P1OUT |= BIT2;

    		// Grab peak values
    		if(ADC_Result > isense_vmax) {
    			isense_vmax = ADC_Result;
    		}
    		else if(ADC_Result < isense_vmin) {
    			isense_vmin = ADC_Result;
    		}
    		acc_i_ave += ADC_Result;
    		break;
    	case 3:	// V_SENSE
    	{
    		// Set debug pin
    		P1OUT |= BIT2;

    		// Grab peak values
    		if(ADC_Result > vsense_vmax) {
				vsense_vmax = ADC_Result;
			}
    		else if(ADC_Result < vsense_vmin) {
				vsense_vmin = ADC_Result;
			}
    		acc_v_ave += ADC_Result;
    		break;
    	}
    	case 2:	// VCC_SENSE
    		// Set dubug pin
    		P1OUT |= BIT2;
	    	break;
    	default: // ADC Reset condition
    	{
    		TA0CCR0 = 9;
    		ADC10CTL1 &= ~ADC10CONSEQ_3;
    		ADC10CTL0 &= ~ADC10ENC;
    		ADC10CTL1 |= ADC10CONSEQ_3;
    		ADC10CTL0 |= ADC10ENC;

    		// Set debug pin
    		P1OUT |= BIT6;

    		sampleCount++;
    		if(sampleCount == SAMCOUNT) { // Entire AC wave sampled (60 Hz)
    			// Reset sampleCount once per wave
    			sampleCount = 0;

    			measCount++;
    			if(measCount >= 60) { // Another second has passed
    				measCount = 0;

    				sequence++;

    				i_ave = acc_i_ave / (sequence * 2520);
    				v_ave = acc_v_ave / (sequence * 2520);

    				i_min = isense_vmin;
    				isense_vmin = 255;
    				i_max = (uint16_t)isense_vmax;
    				isense_vmax = 0;
    				v_min = (uint16_t)vsense_vmin;
    				vsense_vmin = 255;
    				v_max = (uint32_t)vsense_vmax;
    				vsense_vmax = 0;

					__delay_cycles(40000);
					uart_send((char*)&i_ave, sizeof(i_ave));
					data = 6;
    			}
    		}
    		break;
    	}
	    }
        break;                          // Clear CPUOFF bit from 0(SR)
    default: break;
  	}
	P1OUT &= ~(BIT2 + BIT6);
}

#pragma vector=USCI_A0_VECTOR
__interrupt void USCI_A0_ISR(void) {
	switch(__even_in_range(UCA0IV,8)) {
	case 0: break;							// No interrupt
	case 2: 								// RX interrupt
		break;
	case 4:									// TX interrupt
		if(txCt < txLen) {
			UCA0TXBUF = txBuf[txCt++];
		}
		else {
			UCA0IE &= ~UCTXIE;
			UCA0IE |= UCTXCPTIE;
		}
		break;
	case 6: break;							// Start bit received
	case 8: 								// Transmit complete
		UCA0IE &= ~UCTXCPTIE;
		data--;
		switch(data){
		case 5:
			uart_send((char*)&v_ave, sizeof(v_ave));
			break;
		case 4:
			uart_send((char*)&i_min, sizeof(i_min));
			break;
		case 3:
			uart_send((char*)&i_max, sizeof(i_max));
			break;
		case 2:
			uart_send((char*)&v_min, sizeof(v_min));
			break;
		case 1:
			uart_send((char*)&v_max, sizeof(v_max));
			break;
		default: break;
		}
		break;
	default: break;
	}
}

uint8_t getVoltageForPhase(uint8_t head) {
	if(head > PHASEOFF) {
		return head - PHASEOFF - 1;
	}
	else {
		return SAMCOUNT + head - PHASEOFF - 1;
	}
}


