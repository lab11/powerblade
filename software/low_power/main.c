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
#define BACKLOG_LEN		16
int8_t current[BACKLOG_LEN];
int8_t voltage[BACKLOG_LEN];
uint8_t currentWriteCount;
uint8_t currentReadCount;
uint8_t voltageWriteCount;
uint8_t voltageReadCount;
int8_t savedCurrent;
int8_t savedVoltage;
int32_t acc_p_ave;
uint32_t acc_i_rms;
uint32_t acc_v_rms;
int32_t saved_accP;
uint32_t saved_accI;
uint32_t saved_accV;
uint32_t wattHoursToAverage;
uint32_t saved_wattHours;
uint32_t voltAmpsToAverage;
uint32_t saved_voltAmps;

// Near-constants to be transmitted
uint16_t uart_len;
uint8_t ad_len = ADLEN;
uint8_t powerblade_id = 1;

// Transmitted values
uint32_t sequence;
uint32_t scale;
uint8_t Vrms;
uint8_t saved_vrms;
uint16_t truePower;
uint16_t apparentPower;
uint64_t wattHours;
uint32_t wattHoursSend;

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

uint16_t tryCount;
uint16_t sendCount;
void transmitTry(void);
void transmit(void);

/*
 * main.c
 */
int main(void) {
	WDTCTL = WDTPW | WDTHOLD;					// Stop watchdog timer

	// Port J Configuration
	PJSEL0 |= BIT4 + BIT5;						// XIN, XOUT on PJ4, PJ5 with external crystal
	PJSEL0 |= BIT0;								// ZC signal on TDO
	PJSEL1 |= BIT0;
	PJDIR = 0;									// Low power in port J (no IO)
	PJOUT = 0;
	PJREN = 0xFF;

	// Port 1 Configuration
	P1SEL1 |= BIT0 + BIT1 + BIT4 + BIT5;		// Set up ADC on A0, A1, A4, & A5
	P1SEL0 |= BIT0 + BIT1 + BIT4 + BIT5;
	P1OUT = SYS_EN_PIN;							// Low power in port 1 and enable GPIO
	P1DIR = BIT2 + BIT3 + SYS_EN_PIN;
	P1REN = 0xFF;

	// Port 2 Configuration
	P2OUT = 0;									// Low power in port 2
	P2DIR = SEN_EN_PIN;
	P2REN = 0xFF;
	P2SEL0 = 0;

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

	// Initialize system state
	pb_state = pb_normal;
	ready = 0;
	tryCount = 0;
	sendCount = 0;

	// Zero all sensing values
	currentWriteCount = 0;
	currentReadCount = 0;
	voltageWriteCount = 0;
	voltageReadCount = 0;
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
	flags = 0x05;
	txIndex = 0;

	// Initialize scale value (can be updated later)
	scale = pb_config.pscale;
	scale = (scale<<8)+pb_config.vscale;
	scale = (scale<<8)+pb_config.whscale;

	// Set up UART
	uart_init();

	// Set up ADC
	ADC10CTL0 |= ADC10ON;                  		// Turn ADC on (ADC10ON), no multiple sample (ADC10MSC)
	ADC10CTL1 |= ADC10SHS_0 + ADC10SHP;			// ADC10SC source select, sampling timer
	ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
	ADC10MCTL0 = VCCMCTL0; 						// Reference set to VCC & VSS, first input set to VCC_SENSE
	ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
	ADC10IE |= ADC10IE0;                   		// Enable ADC conv complete interrupt

	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
	TA0CCR0 = 13;								// PWM Period
	TA0CCTL0 = CCIE;               				// TA0CCR0 toggle
	TA0CTL = TASSEL_1 + MC_2 + TACLR;          	// TA0 set to ACLK (32kHz), up mode

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
  	TA1CTL = TASSEL_1 + MC_2 + TACLR;	// SMCLK, up to TA1R0, enable overflow int
#endif

	__bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts

	while(1) {
		while(tryCount > 0) {
			tryCount--;
			transmitTry();
		}
		while(sendCount > 0) {
			sendCount--;
			transmit();
		}
		__bis_SR_register(LPM3_bits + GIE);
	}
}

#pragma vector=TIMER0_A0_VECTOR
__interrupt void TIMERA0_ISR(void) {
	TA0CCTL0 &= ~CCIFG;
	TA0CCR0 += 13;
	P1OUT |= BIT2;

	// Start with VCC_SENSE
	ADC10CTL0 &= ~ADC10ENC;
	ADC10MCTL0 = VCCMCTL0;
	ADC10CTL0 |= ADC10ENC;
	ADC10CTL0 += ADC10SC;

	P1OUT &= ~BIT2;
}

#pragma vector=TIMER1_A0_VECTOR
__interrupt void TIMERA1_ISR(void) {
	P1OUT |= (BIT2 + BIT3);
	TA1CCTL0 = 0;
	sendCount++;
	__bic_SR_register_on_exit(LPM3_bits);
	P1OUT &= ~(BIT2 + BIT3);
}

void transmit(void) {
	P1OUT |= BIT3;

	// Stuff data into txBuf
	int blockOffset = txIndex * UARTBLOCK;
	uart_stuff(blockOffset + OFFSET_UARTLEN, (char*) &uart_len, sizeof(uart_len));
	uart_stuff(blockOffset + OFFSET_ADLEN, (char*) &ad_len, sizeof(ad_len));
	uart_stuff(blockOffset + OFFSET_PBID, (char*) &powerblade_id, sizeof(powerblade_id));
	uart_stuff(blockOffset + OFFSET_SEQ, (char*) &sequence, sizeof(sequence));
	uart_stuff(blockOffset + OFFSET_SCALE, (char*) &scale, sizeof(scale));
	uart_stuff(blockOffset + OFFSET_VRMS, (char*) &saved_vrms, sizeof(saved_vrms));
	uart_stuff(blockOffset + OFFSET_TP, (char*) &truePower, sizeof(truePower));
	uart_stuff(blockOffset + OFFSET_AP, (char*) &apparentPower, sizeof(apparentPower));

	wattHoursSend = (uint32_t)(wattHours >> pb_config.whscale);
	uart_stuff(blockOffset + OFFSET_WH, (char*) &wattHoursSend, sizeof(wattHoursSend));

	uart_stuff(blockOffset + OFFSET_FLAGS, (char*) &flags, sizeof(flags));

	uart_send(blockOffset, uart_len);

	P1OUT &= ~BIT3;
}

void transmitTry(void) {

	P1OUT |= BIT3;

	// Save voltage and current before next interrupt happens
	// XXX we could add a overflow check to make sure we havent missed it (unlikely)
	savedCurrent = current[currentReadCount++];
	if(currentReadCount == BACKLOG_LEN) {
		currentReadCount = 0;
	}
	savedVoltage = voltage[voltageReadCount++];
	if(voltageReadCount == BACKLOG_LEN) {
		voltageReadCount = 0;
	}

	// Integrate current
	agg_current += (int16_t) (savedCurrent + (savedCurrent >> 1));
	agg_current -= agg_current >> 5;

	// Subtract offset
	int32_t new_current = agg_current - pb_config.curoff;

	// Perform calculations for I^2, V^2, and P
	acc_i_rms += (new_current * new_current);
	acc_p_ave += (savedVoltage * new_current);
	acc_v_rms += savedVoltage * savedVoltage;

//#if defined (SIDEDATA)
//	// Set side channel output
//	pwm_duty = (agg_current >> 3) + 786;
//	voltage_duty = voltage + 786;
//#endif

	sampleCount++;
	if (sampleCount == SAMCOUNT) { 				// Entire AC wave sampled (60 Hz)
		// Reset sampleCount once per wave
		sampleCount = 0;

		// Save accumulator values before next interrupt happens
		// XXX again could add overflow check (also unlikely, although more likely)
		saved_accI = acc_i_rms;
		acc_i_rms = 0;
		saved_accV = acc_v_rms;
		acc_v_rms = 0;
		saved_accP = acc_p_ave;
		acc_p_ave = 0;

		// Increment energy calc
		wattHoursToAverage += (uint32_t) (saved_accP / SAMCOUNT);

		// Calculate Irms, Vrms, and apparent power
		uint16_t Irms = (uint16_t) SquareRoot(saved_accI / SAMCOUNT);
		Vrms = (uint8_t) SquareRoot(saved_accV / SAMCOUNT);
		voltAmpsToAverage += (uint32_t) (Irms * Vrms);

		measCount++;
		if (measCount >= 60) { 					// Another second has passed
			measCount = 0;

			// Save values to transmit
			saved_wattHours = wattHoursToAverage;
			wattHoursToAverage = 0;
			saved_voltAmps = voltAmpsToAverage;
			voltAmpsToAverage = 0;
			saved_vrms = Vrms;

			uart_len = ADLEN + UARTOVHD;

			flags &= 0x0F;
			flags |= (rxCt << 4);

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
					uart_len += 1 + sizeof(pb_config);	// Add length of data type AND length of pb_config
					char data_type = GET_CONF;
					uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &data_type, sizeof(data_type));
					//uart_stuff(1 + OFFSET_DATATYPE+(txIndex*UARTBLOCK), (char*)&pb_config, sizeof(pb_config));
					memcpy(txBuf + 1 + OFFSET_DATATYPE+(txIndex*UARTBLOCK), &pb_config, sizeof(pb_config));
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

			truePower = (uint16_t) (saved_wattHours / 60);
			wattHours += (uint64_t) truePower;
			apparentPower = (uint16_t) (saved_voltAmps / 60);

#if defined (NORDICDEBUG)
			ready = 1;
#endif
			if (ready == 1) {
				SYS_EN_OUT &= ~SYS_EN_PIN;
				uart_enable(1);
				//TA0CTL = 0;
				// XXX do we still need this delay?
				//__delay_cycles(80000);

				TA1CCR0 = TA1R + 885;
				TA1CCTL0 = CCIE;

//				// Stuff data into txBuf
//				int blockOffset = txIndex * UARTBLOCK;
//				uart_stuff(blockOffset + OFFSET_UARTLEN, (char*) &uart_len, sizeof(uart_len));
//				uart_stuff(blockOffset + OFFSET_ADLEN, (char*) &ad_len, sizeof(ad_len));
//				uart_stuff(blockOffset + OFFSET_PBID, (char*) &powerblade_id, sizeof(powerblade_id));
//				uart_stuff(blockOffset + OFFSET_SEQ, (char*) &sequence, sizeof(sequence));
//				uart_stuff(blockOffset + OFFSET_SCALE, (char*) &scale, sizeof(scale));
//				uart_stuff(blockOffset + OFFSET_VRMS, (char*) &saved_vrms, sizeof(saved_vrms));
//				uart_stuff(blockOffset + OFFSET_TP, (char*) &truePower, sizeof(truePower));
//				uart_stuff(blockOffset + OFFSET_AP, (char*) &apparentPower, sizeof(apparentPower));
//
//				wattHoursSend = (uint32_t)(wattHours >> pb_config.whscale);
//				uart_stuff(blockOffset + OFFSET_WH, (char*) &wattHoursSend, sizeof(wattHoursSend));
//
//				uart_stuff(blockOffset + OFFSET_FLAGS, (char*) &flags, sizeof(flags));
//
//				uart_send(blockOffset, uart_len);
			}
		}
	}
	P1OUT &= ~BIT3;
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
			P1OUT |= BIT2;
			// Store current value for future calculations
			int8_t tempCurrent = (int8_t) (ADC_Result - I_VCC2);

			if(pb_state == pb_capture) {
				if(dataIndex < 5040) {
					int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1) + (dataIndex/504);
					uart_stuff(arrayIndex, (char*) &tempCurrent, sizeof(tempCurrent));
					dataIndex++;
				}
			}

			// After its been stored for raw sample transmission, apply offset
			current[currentWriteCount++] = tempCurrent - pb_config.ioff;
			if(currentWriteCount == BACKLOG_LEN) {
				currentWriteCount = 0;
			}

			// Current is the last measurement, attempt transmission
			//transmitTry();
			tryCount++;
			__bic_SR_register_on_exit(LPM3_bits);
			break;
		}
		case VCASE:								// V_SENSE
		{
			P1OUT |= BIT2;
			// Store voltage value
			int8_t tempVoltage = (int8_t) (ADC_Result - V_VCC2) * -1;

			if(pb_state == pb_capture) {
				if(dataIndex < 5040) {
					int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1) + (dataIndex/504);
					uart_stuff(arrayIndex, (char*) &tempVoltage, sizeof(tempVoltage));
					dataIndex++;
				}
			}

			// After its been stored for raw sample transmission, apply offset
			voltage[voltageWriteCount] = tempVoltage - pb_config.voff;
			if(voltageWriteCount == BACKLOG_LEN) {
				voltageWriteCount = 0;
			}

			// Enable next sample
			// After V_SENSE do I_SENSE
			ADC10CTL0 &= ~ADC10ENC;
			ADC10MCTL0 = IMCTL0;
			ADC10CTL0 |= ADC10ENC;
			ADC10CTL0 += ADC10SC;
			break;
		}
		case VCCCASE:	// VCC_SENSE
			P1OUT |= BIT2;
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
			ADC10CTL0 += ADC10SC;
			break;
		}
		break;                          // Clear CPUOFF bit from 0(SR)
	default:
		break;
	}
	P1OUT &= ~(BIT2);
}



