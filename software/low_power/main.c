/*
 * powerblade
 *
 * The purpose of this app is to measure power
 *
 * Reported values at 1Hz:
 * 	   PowerBlade ID:	1 byte
 * 	        sequence:	4 bytes		(since power on)
 * 	            time:	4 bytes		(since data confirmation)
 * 	            Vrms:	1 byte		(over last 1s)
 * 	      true_power: 	2 bytes		(over last 1s)
 * 	  apparent_power:	2 bytes		(over last 1s)
 * 	      watt_hours:	4 bytes		(since data confirmation)
 * 	           flags:	1 byte
 */

#include <msp430.h> 

#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#include "powerblade_test.h"

//#define CALIBRATE

// Transmission variables
bool ready;
uint8_t data;

// Delay (used at startup)
uint16_t delay_count;

// Variables for integration
int16_t agg_current;
int32_t agg_average;

// Used for data visualizer
uint16_t pwm_duty;
uint16_t voltage_duty;
uint32_t tx_i_ave;

// Count each sample and 60Hz measurement
uint8_t sampleCount;
uint8_t measCount;

// Global variables used interrupt-to-interrupt
int8_t current;
int8_t voltage;
int32_t acc_p_ave;
uint32_t acc_i_rms;
uint32_t acc_v_rms;
uint32_t wattHoursToAverage;
uint32_t voltAmpsToAverage;

// Near-constants to be transmitted
// Near-constants
uint16_t uart_len = 20;
uint8_t ad_len = 19;
uint8_t powerblade_id = 1;

// Transmitted values
uint32_t sequence;
uint32_t time;
uint8_t Vrms;
uint16_t truePower;
uint16_t apparentPower;
uint64_t wattHours;
uint32_t wattHoursSend;
uint8_t flags;

// Buffer to hold old voltage measurements
// This is used to account for a phase delay between current and voltage
int8_t vbuff[SAMCOUNT];
volatile uint8_t vbuff_head;
uint8_t getVoltageForPhase(uint8_t head);

void uart_send(char* buf, unsigned int len);
char *txBuf;
unsigned int txLen;
int txCt;

uint32_t SquareRoot(uint32_t a_nInput) {
	uint32_t op = a_nInput;
	uint32_t res = 0;
	uint32_t one = 1uL << 30; // The second-to-top bit is set: use 1u << 14 for uint16_t type; use 1uL<<30 for uint32_t type

	// "one" starts at the highest power of four <= than the argument.
	while (one > op) {
		one >>= 2;
	}

	while (one != 0) {
		if (op >= res + one) {
			op = op - (res + one);
			res = res + 2 * one;
		}
		res >>= 1;
		one >>= 2;
	}
	return res;
}

/*
 * main.c
 */
int main(void) {
	WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
	TA0CCR0 = 12;						// PWM Period
	TA0CCR1 = 2;                     	// TA0.1 ADC trigger
	TA0CCTL1 = OUTMOD_7 + CCIE;                       	// TA0CCR0 toggle
	TA0CTL = TASSEL_1 + MC_1 + TACLR;          	// ACLK, up mode
	delay_count = 1250;
	__bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts
	TA0CTL = 0;

	// XT1 Setup
	PJSEL0 |= BIT4 + BIT5;

	CSCTL0_H = 0xA5;
	CSCTL1 = DCOFSEL0 + DCOFSEL1;             // Set max. DCO setting
	CSCTL2 = SELA_0 + SELS_3 + SELM_3;        // set ACLK = XT1; MCLK = DCO
	CSCTL3 = DIVA_0 + DIVS_1 + DIVM_1;        // set all dividers
	CSCTL4 |= XT1DRIVE_0;
	CSCTL4 &= ~XT1OFF;

	do {
		CSCTL5 &= ~XT1OFFG;					  // Clear XT1 fault flag
		SFRIFG1 &= ~OFIFG;
	} while (SFRIFG1 & OFIFG);                   // Test oscillator fault flag

//  	__bis_SR_register(LPM3_bits);        	// Enter LPM3 w/ interrupts

	// Low power in port J
	PJDIR = 0;
	PJOUT = 0;
	PJREN = 0xFF;

	// Output ACLK
//    PJDIR |= BIT2;
//    PJSEL1 &= ~BIT2;
//    PJSEL0 |= BIT2;

	// Low power in port 1
//    P1DIR = BIT2 + BIT3;
	P1DIR = 0;
	P1OUT = 0;
	P1REN = 0xFF;

	// Low power in port 2
	P2DIR = 0;
	P2OUT = 0;
	P2REN = 0xFF;

	// Set SEN_EN to output and disable (~200uA)
	SEN_EN_OUT &= ~SEN_EN_PIN;
	SEN_EN_DIR |= SEN_EN_PIN;

	// Zero all sensing values
	sampleCount = 0;
	measCount = 0;
	acc_p_ave = 0;
	acc_i_rms = 0;
	acc_v_rms = 0;
	wattHours = 0;
	wattHoursToAverage = 0;
	voltAmpsToAverage = 0;
	sequence = 0;
	time = 0;
	flags = 0;
	agg_current = 0;
	vbuff_head = 0;

	// Set SYS_EN to output and disable (PMOS)
	SYS_EN_OUT |= SYS_EN_PIN;
	SYS_EN_DIR |= SYS_EN_PIN;
	ready = 0;

	// Set up UART
//    P2SEL0 &= ~(BIT0);// + BIT1);
//    P2SEL1 |= BIT0;// + BIT1;
//    P2DIR |= BIT1;
//    P2OUT |= BIT1;
//    P1DIR |= BIT6;
//    P1OUT |= BIT6;
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
	P1SEL1 |= BIT0 + BIT1 + BIT4 + BIT5;
	P1SEL0 |= BIT0 + BIT1 + BIT4 + BIT5;
//    P1DIR |= BIT4 + BIT5;
//    P1OUT |= BIT4 + BIT5;
	P1DIR |= BIT4 + BIT0;
	P1OUT |= BIT4 + BIT0;
	ADC10CTL0 |= ADC10ON;                  // + ADC10MSC;          	// ADC10ON
	ADC10CTL1 |= ADC10SHS_0 + ADC10SHP + ADC10CONSEQ_3; // rpt series of ch; TA0.1 trig sample start
	ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
	ADC10MCTL0 |= ADC10INCH_5 + ADC10SREF_0; // A3,4,5 ADC input select; Vref=AVCC

	ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
	ADC10IE |= ADC10IE0;                   // Enable ADC conv complete interrupt

	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
	TA0CCR0 = 12;						// PWM Period
	TA0CCR1 = 2;                     	// TA0.1 ADC trigger
	TA0CCTL1 = OUTMOD_7 + CCIE;                       	// TA0CCR0 toggle
	TA0CTL = TASSEL_1 + MC_1 + TACLR;          	// ACLK, up mode

	// Set up PWM for side channel data
  	P1DIR |= BIT2 + BIT3;
  	P1SEL0 |= BIT2 + BIT3;
  	TA1CCR0 = 1572;
  	TA1CCR1 = 100;
  	TA1CCR2 = 100;
  	pwm_duty = 100;
  	voltage_duty = 100;
  	TA1CCTL1 = OUTMOD_7;
  	TA1CCTL2 = OUTMOD_7;
  	TA1CTL = TASSEL_2 + MC_1 + TAIE + TACLR;

	__bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts

	return 0;
}

#pragma vector=TIMER0_A1_VECTOR
__interrupt void TIMERA0_ISR(void) {
	TA0CCTL1 &= ~CCIFG;
	//P2OUT ^= BIT0;
	if (delay_count > 1) {
		delay_count--;
	} else if (delay_count == 1) {
		delay_count--;
		__bic_SR_register_on_exit(LPM3_bits);
	} else {
		ADC10CTL0 += ADC10SC;
	}
}

#pragma vector=TIMER1_A1_VECTOR
__interrupt void TIMERA1_ISR(void) {
	TA1CTL &= ~TAIFG;
	TA1CCR1 = pwm_duty;
	TA1CCR2 = voltage_duty;
}

void uart_enable(bool enable) {
	if (enable) {
		P2SEL0 &= ~(BIT0);        	// + BIT1);
		P2SEL1 |= BIT0;        	// + BIT1;
	} else {
		//P2SEL0 |= BIT0;
		P2SEL1 &= ~BIT0;
	}
}

void uart_send(char* buf, unsigned int len) {
	txBuf = buf;
	txLen = len;
	txCt = 0;

	UCA0IE |= UCTXIE;
	txCt = txLen - 1;
	if (txCt >= 0) {
		UCA0TXBUF = buf[txCt--];
	}
}

void transmitTry(void) {

	// Integrate current
	agg_current += (int16_t) (current + (current >> 1));
	agg_average = agg_current >> 5;
	agg_current -= agg_average;

	// Subtract offset, if not in calibration mode
#ifndef CALIBRATE
	int32_t new_current;
	if(agg_current > 0) {
		new_current = agg_current - CUROFF;
	}
	else {
		new_current = agg_current + CUROFF;
	}
#else
	int32_t new_current = agg_current;
#endif

	// Perform calculations for I^2, V^2, and P
	new_current = agg_current;
	acc_i_rms += new_current * new_current;
	acc_p_ave += voltage * new_current;
	acc_v_rms += voltage * voltage;

	// Set side channel output
	pwm_duty = (agg_current >> 3) + 786;
	voltage_duty = voltage + 786;

	sampleCount++;
	if (sampleCount == SAMCOUNT) { // Entire AC wave sampled (60 Hz)
		// Reset sampleCount once per wave
		sampleCount = 0;

		// Increment energy calc and reset accumulator
		if (acc_p_ave < 0) {
			acc_p_ave = 0;
		}
		wattHoursToAverage += (uint32_t) (acc_p_ave / SAMCOUNT);
		acc_p_ave = 0;

		// Calculate Irms, Vrms, and apparent power
		uint16_t Irms = (uint16_t) SquareRoot(acc_i_rms / SAMCOUNT);
		Vrms = (uint8_t) SquareRoot(acc_v_rms / SAMCOUNT);
		acc_i_rms = 0;
		acc_v_rms = 0;
		voltAmpsToAverage += (uint32_t) (Irms * Vrms);

		measCount++;
		if (measCount >= 60) { // Another second has passed
			measCount = 0;

			sequence++;
			time++;

#ifdef CALIBRATE
			tx_i_ave = (uint32_t) Irms;
#endif

			truePower = (uint16_t) (wattHoursToAverage / 60);
			wattHours += (uint64_t) truePower;
			apparentPower = (uint16_t) (voltAmpsToAverage / 60);
			wattHoursToAverage = 0;
			voltAmpsToAverage = 0;

//			ready = 1;
			if (ready == 1) {
				SYS_EN_OUT &= ~SYS_EN_PIN;
				uart_enable(1);
				__delay_cycles(80000);
				//uart_send((char*) &powerblade_id, sizeof(powerblade_id));
				uart_send((char*) &uart_len, sizeof(uart_len));
				data = NUM_DATA;
			}
		}
	}
}

#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR(void) {

	uint8_t ADC_Result;
	unsigned char ADC_Channel;

	switch (__even_in_range(ADC10IV, 12)) {
	case 0:
		break;                          // No interrupt
	case 2:
		break;                          // conversion result overflow
	case 4:
		break;                          // conversion time overflow
	case 6:
		break;                          // ADC10HI
	case 8:
		break;                          // ADC10LO
	case 10:
		break;                          // ADC10IN
	case 12:
		ADC_Result = ADC10MEM0;
		ADC_Channel = ADC10MCTL0 & ADC10INCH_7;
		switch (ADC_Channel) {
#if defined (VERSION0) | defined (VERSION1)
		case 4:	// I_SENSE
#elif defined (VERSION31)
		case 5:	// I_SENSE (A0) (case 0 for filt, 5 for isense)
#elif defined (VERSION32)
		case 3:	// I_SENSE
#endif
		{
			// Set debug pin
			//P1OUT |= BIT2;

			// Store current value for future calculations
			current = (int8_t) (ADC_Result - I_VCC2);

			// Enable next sample
			//ADC10CTL0 += ADC10SC;
			transmitTry();
			break;
		}
#if defined (VERSION32)
		case 5:	// V_SENSE
#else
		case 3:	// V_SENSE (same in versions 0, 1, and 3.1)
#endif
		{
			// Set debug pin
			//P1OUT |= BIT2;

			// Store voltage value
			voltage = (int8_t) (ADC_Result - V_VCC2) * -1;

			// Store and account for phase offset
			vbuff[vbuff_head++] = voltage;
			voltage = vbuff[getVoltageForPhase(vbuff_head)];
			if (vbuff_head == SAMCOUNT) {
				vbuff_head = 0;
			}

			// Enable next sample
			ADC10CTL0 += ADC10SC;
			break;
		}
#if defined (VERSION0) | defined (VERSION1)
			case 2:	// VCC_SENSE
#elif defined (VERSION31) | defined (VERSION32)
		case 4:	// VCC_SENSE
#endif
			// Set debug pin
			//P1OUT |= BIT2;

			// Perform Vcap measurements
			if (ADC_Result < ADC_VMIN) {
				uart_enable(0);
				SYS_EN_OUT |= SYS_EN_PIN;
				ready = 0;
			} else if (ready == 0) {
				if (ADC_Result > ADC_VCHG) {
					SEN_EN_OUT |= SEN_EN_PIN;
					agg_current = 0;
					agg_average = 0;
					ready = 1;
				}
			}

			// Enable next sample
			ADC10CTL0 += ADC10SC;
			break;
		default: // ADC Reset condition
			// Set debug pin
			//P1OUT |= BIT3;

			ADC10CTL0 += ADC10SC;
			break;
		}
		break;                          // Clear CPUOFF bit from 0(SR)
	default:
		break;
	}
	//P1OUT &= ~(BIT3 + BIT2);
}

#pragma vector=USCI_A0_VECTOR
__interrupt void USCI_A0_ISR(void) {
	switch (__even_in_range(UCA0IV, 8)) {
	case 0:
		break;								// No interrupt
	case 2: 								// RX interrupt
		break;
	case 4:									// TX interrupt
		if (txCt >= 0) {
			UCA0TXBUF = txBuf[txCt--];
		} else {
			UCA0IE &= ~UCTXIE;
			UCA0IE |= UCTXCPTIE;
		}
		break;
	case 6:
		break;								// Start bit received
	case 8: 								// Transmit complete
		UCA0IE &= ~UCTXCPTIE;
		data--;
		switch (data) {
		case 9:
			uart_send((char*) &ad_len, sizeof(ad_len));
			break;
		case 8:
			uart_send((char*) &powerblade_id, sizeof(powerblade_id));
			break;
		case 7:
			uart_send((char*) &sequence, sizeof(sequence));
			break;
		case 6:
#ifdef CALIBRATE
			time = 0;
#else
			time = PSCALE;
			time = (time<<8)+VSCALE;
			time = (time<<8)+WHSCALE;
#endif
			uart_send((char*)&time, sizeof(time));
			break;
		case 5:
			uart_send((char*) &Vrms, sizeof(Vrms));
			break;
		case 4:
			uart_send((char*) &truePower, sizeof(truePower));
			break;
		case 3:
			uart_send((char*) &apparentPower, sizeof(apparentPower));
			break;
		case 2:
#ifdef CALIBRATE
			uart_send((char*) &tx_i_ave, sizeof(tx_i_ave));
#else
			wattHoursSend = (uint32_t)(wattHours >> 9);
			uart_send((char*) &wattHoursSend, sizeof(wattHoursSend));
#endif
			break;
		case 1:
			uart_send((char*) &flags, sizeof(flags));
			break;
		default:
			break;
		}
		break;
	default:
		break;
	}
}

uint8_t getVoltageForPhase(uint8_t head) {
	if (head > PHASEOFF) {
		return head - PHASEOFF - 1;
	} else {
		return SAMCOUNT + head - PHASEOFF - 1;
	}
}

