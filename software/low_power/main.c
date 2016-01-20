/*
 * powerblade
 *
 * The purpose of this app is to measure power
 *
 * Reported values at 1Hz:
 * 	   PowerBlade ID:	1 byte
 * 	        sequence:	4 bytes		(since power on)
 * 	           scale:	4 bytes		(since data confirmation)
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
#include "uart_types.h"
#include "checksum.h"
#include "uart.h"

//#define NORDICDEBUG
#define SIDEDATA

// Transmission variables
bool ready;

// Delay (used at startup)
uint16_t delay_count;

// Variables for integration
int16_t agg_current;

// Used for data visualizer
uint16_t pwm_duty;
uint16_t voltage_duty;

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
uint16_t uart_len;
uint8_t ad_len = ADLEN;
uint8_t powerblade_id = 1;

// Transmitted values
uint32_t sequence;
uint32_t scale;
uint8_t Vrms;
uint16_t truePower;
uint16_t apparentPower;
uint64_t wattHours;
uint32_t wattHoursSend;
uint8_t flags;

// Scale and offset values (configuration/calibration)
#pragma PERSISTENT(pb_config)
PowerBladeConfig_t pb_config = { .voff = 0x00, .ioff = 0x00, .curoff = 0x0000, .pscale = 0x41F4, .vscale = 0x7B, .whscale = 0x09};

// PowerBlade state (used for downloading data)
int dataIndex;
pb_state_t pb_state;
int txIndex;
bool dataComplete;

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

void transmitTry(void);

/*
 * main.c
 */
int main(void) {
	WDTCTL = WDTPW | WDTHOLD;					// Stop watchdog timer

	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
	TA0CCR0 = 12;								// PWM Period
	TA0CCR1 = 2;                     			// TA0.1 ADC trigger
	TA0CCTL1 = OUTMOD_7 + CCIE;               	// TA0CCR0 toggle
	TA0CTL = TASSEL_1 + MC_1 + TACLR;          	// ACLK, up mode
	delay_count = 1250;
	__bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts
	TA0CTL = 0;

	// Clock Setup
	PJSEL0 |= BIT4 + BIT5;						// XIN, XOUT on PJ4, PJ5 with external crystal
	CSCTL0_H = 0xA5;							// Input CSKEY password to change clock settings
	CSCTL1 = DCOFSEL0 + DCOFSEL1;             	// Set DCO to 8MHz
	CSCTL2 = SELA_0 + SELS_3 + SELM_3;        	// Set ACLK = XT1, SMCLK = MCLK = DCO
	CSCTL3 = DIVA_0 + DIVS_1 + DIVM_1;        	// Set ACLK = XT1/1 (32768Hz), SMCLK = MCLK = DCO/2 (4MHz)
	CSCTL4 |= XT1DRIVE_0;						// Set XT1 LF, lowest current consumption
	CSCTL4 &= ~XT1OFF;							// Turn on XT1
	do {										// Test XT1 for correct initialization
		CSCTL5 &= ~XT1OFFG;					  	// Clear XT1 fault flags
		SFRIFG1 &= ~OFIFG;
	} while (SFRIFG1 & OFIFG);              	// Test oscillator fault flag
	// XT1 test passed

	// Low power in port J
	PJDIR = 0;
	PJOUT = 0;
	PJREN = 0xFF;

	// Low power in port 1
	P1DIR = 0;
	P1OUT = 0;
	P1REN = 0xFF;

	// Low power in port 2
	P2DIR = 0;
	P2OUT = 0;
	P2REN = 0xFF;

	// Initialize system state
	pb_state = pb_normal;

	// Zero all sensing values
	sampleCount = 0;
	measCount = 0;
	acc_p_ave = 0;
	acc_i_rms = 0;
	acc_v_rms = 0;
	wattHours = 0;
	wattHoursToAverage = 0;
	voltAmpsToAverage = 0;

	// Initialize remaining transmitted values
	sequence = 0;
	flags = 0xA5;
	txIndex = 0;

	// Initialize scale value (can be updated later)
	scale = pb_config.pscale;
	scale = (scale<<8)+pb_config.vscale;
	scale = (scale<<8)+pb_config.whscale;

	// Set SEN_EN to output and disable (~200uA)
	SEN_EN_OUT &= ~SEN_EN_PIN;
	SEN_EN_DIR |= SEN_EN_PIN;

	// Set SYS_EN (radio control) to output and disable (PMOS)
	ready = 0;
	SYS_EN_OUT |= SYS_EN_PIN;
	SYS_EN_DIR |= SYS_EN_PIN;

	// Set up UART
	uart_init();

	// Set up ADC
	// Enable ADC for VCC_SENSE, I_SENSE, V_SENSE
	P1SEL1 |= BIT0 + BIT1 + BIT4 + BIT5;		// Set up ADC on A0, A1, A4, & A5
	P1SEL0 |= BIT0 + BIT1 + BIT4 + BIT5;
	P1DIR |= BIT4 + BIT0;						// Not sure what this does
	P1OUT |= BIT4 + BIT0;
	ADC10CTL0 |= ADC10ON;                  		// Turn ADC on (ADC10ON), no multiple sample (ADC10MSC)
	ADC10CTL1 |= ADC10SHS_0 + ADC10SHP;			// ADC10SC source select, sampling timer
	ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
	ADC10MCTL0 = VCCMCTL0; 						// Reference set to VCC & VSS, first input set to VCC_SENSE
	ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
	ADC10IE |= ADC10IE0;                   		// Enable ADC conv complete interrupt

	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
	TA0CCR0 = 12;								// PWM Period
	TA0CCR1 = 2;                     			// TA0.1 ADC trigger
	TA0CCTL1 = OUTMOD_7 + CCIE;               	// TA0CCR0 toggle
	TA0CTL = TASSEL_1 + MC_1 + TACLR;          	// TA0 set to ACLK (32kHz), up mode

	P1DIR |= BIT2 + BIT3;
#if defined (SIDEDATA)
	// Set up PWM for side channel data
//  	P1DIR |= BIT2 + BIT3;						// Set up P1.2 & P1.3 as timer
//  	//P1SEL0 |= BIT2 + BIT3;						// output pins
//  	TA1CCR0 = 1572;								// Period set to 393 us
//  	pwm_duty = 100;								// Initialize both current and voltage to 100
//  	voltage_duty = 100;
//  	TA1CCR1 = pwm_duty;
//  	TA1CCR2 = voltage_duty;
//  	TA1CCTL1 = OUTMOD_7;						// Set current and voltage to RST/SET
//  	TA1CCTL2 = OUTMOD_7;
  	TA1CTL = TASSEL_2 + MC_1 + TAIE + TACLR;	// SMCLK, up to TA1R0, enable overflow int
#endif

	__bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts

	while(1) {
		transmitTry();
		__bis_SR_register(LPM3_bits + GIE);
	}
}

#pragma vector=TIMER0_A1_VECTOR
__interrupt void TIMERA0_ISR(void) {
	TA0CCTL1 &= ~CCIFG;
//	P1OUT |= BIT2;
	if (delay_count > 1) {
		delay_count--;
	} else if (delay_count == 1) {
		delay_count--;
		__bic_SR_register_on_exit(LPM3_bits);
	} else {
		// Start with VCC_SENSE
		ADC10CTL0 &= ~ADC10ENC;
		ADC10MCTL0 = VCCMCTL0;
		ADC10CTL0 |= ADC10ENC;
		ADC10CTL0 += ADC10SC;
	}
//	P1OUT &= ~BIT2;
}

//#pragma vector=TIMER1_A1_VECTOR
//__interrupt void TIMERA1_ISR(void) {
//	TA1CTL &= ~TAIFG;
//	P1OUT |= BIT3;
//	TA1CCR1 = pwm_duty;
//	TA1CCR2 = voltage_duty;
//	P1OUT &= ~BIT3;
//}

void transmitTry(void) {

	// Integrate current
	agg_current += (int16_t) (current + (current >> 1));
	agg_current -= agg_current >> 5;

	// Subtract offset
	 int32_t new_current = agg_current + pb_config.curoff;

	// Perform calculations for I^2, V^2, and P
	acc_i_rms += (new_current * new_current);
	acc_p_ave += (voltage * new_current);
	acc_v_rms += voltage * voltage;

//#if defined (SIDEDATA)
//	// Set side channel output
//	pwm_duty = (agg_current >> 3) + 786;
//	voltage_duty = voltage + 786;
//#endif

	sampleCount++;
	if (sampleCount == SAMCOUNT) { 				// Entire AC wave sampled (60 Hz)
		// Reset sampleCount once per wave
		sampleCount = 0;

		// Increment energy calc and reset accumulator
		// XXX should we be doing this?
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
		if (measCount >= 60) { 					// Another second has passed
			measCount = 0;

			uart_len = ADLEN + UARTOVHD;

			// Process any UART bytes
			if(pb_state == pb_capture) {
				uart_len = UARTBLOCK;
				pb_state = pb_data;
				char data_type = CONT_SAMDATA;
				uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &data_type, sizeof(data_type));
			}
			else if(processMessage() > 0) {
				switch(captureType) {
				case GET_CONF:
				{
					uart_len += 1;	// Add length of data type
					char data_type = GET_CONF;
					uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &data_type, sizeof(data_type));
					uart_len += sizeof(pb_config);
					uart_stuff(1 + OFFSET_DATATYPE+(txIndex*UARTBLOCK), (char*)&pb_config, sizeof(pb_config));
					break;
				}
				case SET_CONF:
					// XXX do we want to do any bounds-checking on this?
					memcpy(&pb_config, captureBuf, sizeof(pb_config));
					break;
				case SET_SEQ:
					sequence = captureBuf[0];
					break;
				default:
					switch(pb_state) {

					case pb_normal:
						switch(captureType) {
						case START_SAMDATA:
						{
							pb_state = pb_capture;
							dataIndex = 0;
							uart_len += 1;
							char data_type = START_SAMDATA;
							uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
							break;
						}
						default:
							break;
						}
						break;

					case pb_data:
						switch(captureType) {
						case CONT_SAMDATA:
							if(dataComplete) {
								uart_len += 1;
								txIndex = 0;
								pb_state = pb_normal;
								dataComplete = 0;
								char data_type = DONE_SAMDATA;
								uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
							}
							else {
								uart_len = UARTBLOCK;
								txIndex++;
								char data_type = CONT_SAMDATA;
								uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &data_type, sizeof(data_type));
								if(txIndex == 9) {
									dataComplete = 1;
								}
							}
							break;
						case UART_NAK:
							uart_len = UARTBLOCK;
							break;
						default:
							break;
						}
						break;

					}
					break;
				}
			}

			// Increment sequence number for transmission
			sequence++;

			truePower = (uint16_t) (wattHoursToAverage / 60);
			wattHours += (uint64_t) truePower;
			apparentPower = (uint16_t) (voltAmpsToAverage / 60);
			wattHoursToAverage = 0;
			voltAmpsToAverage = 0;

#if defined (NORDICDEBUG)
			ready = 1;
#endif
			if (ready == 1) {
				SYS_EN_OUT &= ~SYS_EN_PIN;
				uart_enable(1);
				// XXX do we still need this delay?
				__delay_cycles(80000);

				// Stuff data into txBuf
				int blockOffset = txIndex * UARTBLOCK;
				uart_stuff(blockOffset + OFFSET_UARTLEN, (char*) &uart_len, sizeof(uart_len));
				uart_stuff(blockOffset + OFFSET_ADLEN, (char*) &ad_len, sizeof(ad_len));
				uart_stuff(blockOffset + OFFSET_PBID, (char*) &powerblade_id, sizeof(powerblade_id));
				uart_stuff(blockOffset + OFFSET_SEQ, (char*) &sequence, sizeof(sequence));
				uart_stuff(blockOffset + OFFSET_SCALE, (char*) &scale, sizeof(scale));
				uart_stuff(blockOffset + OFFSET_VRMS, (char*) &Vrms, sizeof(Vrms));
				uart_stuff(blockOffset + OFFSET_TP, (char*) &truePower, sizeof(truePower));
				uart_stuff(blockOffset + OFFSET_AP, (char*) &apparentPower, sizeof(apparentPower));

				wattHoursSend = (uint32_t)(wattHours >> pb_config.whscale);
				uart_stuff(blockOffset + OFFSET_WH, (char*) &wattHoursSend, sizeof(wattHoursSend));

				uart_stuff(blockOffset + OFFSET_FLAGS, (char*) &flags, sizeof(flags));

				uart_send(blockOffset, uart_len);
			}
		}
	}
}

#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR(void) {

	uint8_t ADC_Result;
	unsigned char ADC_Channel;

	switch (__even_in_range(ADC10IV, 12)) {
	case 12:
		ADC_Result = ADC10MEM0;
		ADC_Channel = ADC10MCTL0 & ADC10INCH_7;
		switch (ADC_Channel) {
		case ICASE:								// I_SENSE
		{
			P1OUT |= BIT3;
			// Store current value for future calculations
			//int8_t ioff = -4;
			current = (int8_t) (ADC_Result - I_VCC2);

			if(pb_state == pb_capture) {
				if(dataIndex < 5040) {
					int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1);
					uart_stuff(arrayIndex, (char*) &current, sizeof(current));
					dataIndex++;
				}
			}

			// After its been stored for raw sample transmission, apply offset
			current -= pb_config.ioff;

			// Current is the last measurement, attempt transmission
			//transmitTry();
			__bic_SR_register_on_exit(LPM3_bits);
			break;
		}
		case VCASE:								// V_SENSE
		{
			P1OUT |= BIT3;
			// Store voltage value
			//int8_t voff = -1;
			voltage = (int8_t) (ADC_Result - V_VCC2) * -1;

			if(pb_state == pb_capture) {
				if(dataIndex < 5040) {
					int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1);
					uart_stuff(arrayIndex, (char*) &voltage, sizeof(voltage));
					dataIndex++;
				}
			}

			// After its been stored for raw sample transmission, apply offset
			voltage -= pb_config.voff;

			// Enable next sample
			// After V_SENSE do I_SENSE
			ADC10CTL0 &= ~ADC10ENC;
			ADC10MCTL0 = IMCTL0;
			ADC10CTL0 |= ADC10ENC;
			ADC10CTL0 += ADC10SC;
			break;
		}
		case VCCCASE:	// VCC_SENSE
			P1OUT |= BIT3 + BIT2;
			// Perform Vcap measurements
			if (ADC_Result < ADC_VMIN) {
#if !defined (NORDICDEBUG)
				uart_enable(0);
				SYS_EN_OUT |= SYS_EN_PIN;
				ready = 0;
#endif
			} else if (ready == 0) {
				if (ADC_Result > ADC_VCHG) {
					SEN_EN_OUT |= SEN_EN_PIN;
					agg_current = 0;
					ready = 1;
				}
			}

			// Enable next sample
			// After VCC_SENSE do V_SENSE
			ADC10CTL0 &= ~ADC10ENC;
			ADC10MCTL0 = VMCTL0;
			ADC10CTL0 |= ADC10ENC;
			ADC10CTL0 += ADC10SC;
			break;
		default: // ADC Reset condition
			P1OUT |= BIT2;
			ADC10CTL0 += ADC10SC;
			break;
		}
		break;                          // Clear CPUOFF bit from 0(SR)
	default:
		break;
	}
	P1OUT &= ~(BIT2 + BIT3);
}



