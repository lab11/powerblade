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

#include "powerblade_test.h"
#include "uart_types.h"
#include "checksum.h"
#include "uart.h"

//#define NORDICDEBUG

// Transmission variables
bool ready;
bool senseEnabled;

// Variable for integration
int16_t agg_current;

// Count each sample and 60Hz measurement
uint8_t sampleCount;
uint8_t measCount;

// Global variables used interrupt-to-interrupt
#define BACKLOG_LEN		16
#if defined (ADC8)
int8_t current[BACKLOG_LEN];
int8_t voltage[BACKLOG_LEN];
int8_t savedCurrent;
int8_t savedVoltage;
#else
int16_t current[BACKLOG_LEN];
int16_t voltage[BACKLOG_LEN];
int16_t savedCurrent;
int16_t savedVoltage;
#endif
uint8_t currentWriteCount;
uint8_t currentReadCount;
uint8_t voltageWriteCount;
uint8_t voltageReadCount;
int32_t acc_p_ave;
uint32_t acc_i_rms;
uint32_t acc_v_rms;
int32_t wattHoursToAverage;
uint32_t voltAmpsToAverage;

// Near-constants to be transmitted
uint16_t uart_len;
uint8_t ad_len = ADLEN;
uint8_t powerblade_id = 2;

// Transmitted values
uint32_t sequence;
uint32_t scale;
uint8_t Vrms;
uint16_t truePower;
uint16_t apparentPower;
uint64_t wattHours;
uint32_t wattHoursSend;

#pragma PERSISTENT(flags)
uint8_t flags = 0x05;

// Scale and offset values (configuration/calibration)
#pragma PERSISTENT(pb_config)
#if defined (ADC8)
PowerBladeConfig_t pb_config = { .voff = -1, .ioff = -1, .curoff = 0x0000, .pscale = 0x428A, .vscale = 0x7B, .whscale = 0x09};
#else
PowerBladeConfig_t pb_config = { .voff = -1, .ioff = -16, .curoff = 0x0000, .pscale = 0x428A, .vscale = 0x79, .whscale = 0x09};
#endif

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

uint32_t SquareRoot64(uint64_t a_nInput) {
	uint64_t op = a_nInput;
	uint64_t res = 0;
	uint64_t one = (uint64_t)1 << 62; // The second-to-top bit is set: use 1u << 14 for uint16_t type; use 1uL<<30 for uint32_t type

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

// Variables and functions for keeping computation and transmission out of interrupts
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

	// Initialize system state
	pb_state = pb_normal;
	ready = 0;
	senseEnabled = 0;
	tryCount = 0;
	sendCount = 0;

	// Zero all sensing values
	currentWriteCount = 0;
	currentReadCount = 0;
	voltageWriteCount = 0;
	voltageReadCount = 0;
	wattHours = 0;
	sampleCount = 0;
	measCount = 0;

	// Initialize remaining transmitted values
	sequence = 0;
	txIndex = 0;

	// Initialize scale value (can be updated later)
	scale = pb_config.pscale;
	scale = (scale<<8)+pb_config.vscale;
	scale = (scale<<8)+pb_config.whscale;

	// Clock Setup
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

	// Set up UART
	uart_init();

	// Set up ADC
	ADC10CTL0 |= ADC10ON;                  		// Turn ADC on (ADC10ON), no multiple sample (ADC10MSC)
	ADC10CTL1 |= ADC10SHS_0 + ADC10SHP;			// ADC10SC source select, sampling timer
#if defined (ADC8)
	ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
#else
	ADC10CTL2 |= ADC10RES;
#endif
	ADC10MCTL0 = VCCMCTL0; 						// Reference set to VCC & VSS, first input set to VCC_SENSE
	ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
	ADC10IE |= ADC10IE0;                   		// Enable ADC conv complete interrupt

	// ADC conversion trigger signal - TimerA0.0
	TA0CCR0 = 13;								// Timer Period
	TA0CCTL0 = CCIE;               				// TA0CCR0 interrupt
	TA0CTL = TASSEL_1 + MC_2 + TACLR;          	// TA0 set to ACLK (32kHz), up mode

	// Wait timer for transmissions
  	TA1CTL = TASSEL_1 + MC_2 + TACLR;			// ACLK, up mode


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
	uart_stuff(blockOffset + OFFSET_VRMS, (char*) &Vrms, sizeof(Vrms));
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
	int32_t new_current = (agg_current >> 3) - pb_config.curoff;

	// Perform calculations for I^2, V^2, and P
	acc_i_rms += (uint64_t)(new_current * new_current);
	acc_p_ave += ((int64_t)savedVoltage * new_current);
	acc_v_rms += (uint64_t)((int32_t)savedVoltage * (int32_t)savedVoltage);

	sampleCount++;
	if (sampleCount == SAMCOUNT) { 				// Entire AC wave sampled (60 Hz)
		// Reset sampleCount once per wave
		sampleCount = 0;

		// Increment energy calc
		wattHoursToAverage += (int32_t)(acc_p_ave / SAMCOUNT);
		acc_p_ave = 0;

		// Calculate Irms, Vrms, and apparent power
		uint16_t Irms = (uint16_t) SquareRoot64(acc_i_rms / SAMCOUNT);
		Vrms = (uint8_t) SquareRoot64(acc_v_rms / SAMCOUNT);
		voltAmpsToAverage += (uint32_t) (Irms * Vrms);
		acc_i_rms = 0;
		acc_v_rms = 0;

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
					scale = pb_config.pscale;
					scale = (scale<<8)+pb_config.vscale;
					scale = (scale<<8)+pb_config.whscale;
					flags |= 0x80;
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

			// True power cannot be less than zero
			if(wattHoursToAverage > 0) {
				truePower = (uint16_t) ((wattHoursToAverage / 60));
			}
			else {
				truePower = 0;
			}
			wattHours += (uint64_t) truePower;
			apparentPower = (uint16_t) ((voltAmpsToAverage / 60));

			wattHoursToAverage = 0;
			voltAmpsToAverage = 0;

#if defined (NORDICDEBUG)
			ready = 1;
#endif
			if (ready == 1) {
				// Boot the nordic and enable its UART
				SYS_EN_OUT &= ~SYS_EN_PIN;
				uart_enable(1);

				// Delay for a bit to allow nordic to boot
				// TODO this is only required the first time
				TA1CCR0 = TA1R + 500;
				TA1CCTL0 = CCIE;
			}
		}
	}
	P1OUT &= ~BIT3;
}

#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR(void) {

#if defined (ADC8)
	uint8_t ADC_Result;
#else
	uint16_t ADC_Result;
#endif

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
#if defined (ADC8)
			int8_t tempCurrent = (int8_t) (ADC_Result - I_VCC2);
#else
			int16_t tempCurrent;
			if(ADC_Result & 0x200) {	// Measurement above VCC/2
				tempCurrent = ADC_Result & 0x1FF;		// Subtract Vcc/2
			}
			else {
				tempCurrent = 0x200 - ADC_Result - 1;
				tempCurrent = ~tempCurrent;
			}
#endif

			if(pb_state == pb_capture) {
#if defined (ADC8)
				if(dataIndex < 5040) {
					int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1) + (dataIndex/504);
					uart_stuff(arrayIndex, (char*) &tempCurrent, sizeof(tempCurrent));
					dataIndex++;
				}
#else
				if(dataIndex < 2520) {
					//tempCurrent = -50;
					int arrayIndex = (2*dataIndex) + (ADLEN + UARTOVHD)*((dataIndex/252) + 1) + (dataIndex/252);
					uart_stuff(arrayIndex, (char*) &tempCurrent, sizeof(tempCurrent));
					dataIndex++;
				}
#endif
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
#if defined (ADC8)
			int8_t tempVoltage = (int8_t) (ADC_Result - V_VCC2) * -1;
#else
			int16_t tempVoltage;
			if(ADC_Result & 0x200) {	// Measurement above VCC/2
				tempVoltage = ADC_Result & 0x1FF;		// Subtract Vcc/2
				tempVoltage = ~tempVoltage;				// Mult by -1
			}
			else {
				ADC_Result = ~ADC_Result;
				tempVoltage = ADC_Result + 0x200 + 1;
			}
#endif

			if(pb_state == pb_capture) {
#if defined (ADC8)
				if(dataIndex < 5040) {
					int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1) + (dataIndex/504);
					uart_stuff(arrayIndex, (char*) &tempVoltage, sizeof(tempVoltage));
					dataIndex++;
				}
#else
				if(dataIndex < 2520) {
					//tempVoltage = -194;
					int arrayIndex = (2*dataIndex) + (ADLEN + UARTOVHD)*((dataIndex/252) + 1) + (dataIndex/252);
					uart_stuff(arrayIndex, (char*) &tempVoltage, sizeof(tempVoltage));
					dataIndex++;
				}
#endif
			}

			// After its been stored for raw sample transmission, apply offset
			voltage[voltageWriteCount++] = tempVoltage - pb_config.voff;
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
					senseEnabled = 1;
					acc_p_ave = 0;
					acc_i_rms = 0;
					acc_v_rms = 0;
					wattHoursToAverage = 0;
					voltAmpsToAverage = 0;
					agg_current = 0;
					ready = 1;
				}
			}

#if defined (NORDICDEBUG)
			senseEnabled = 1;
#endif

			// Enable next sample
			// After VCC_SENSE do V_SENSE
			if(senseEnabled == 1) {
				ADC10CTL0 &= ~ADC10ENC;
				ADC10MCTL0 = VMCTL0;
				ADC10CTL0 |= ADC10ENC;
				ADC10CTL0 += ADC10SC;
			}
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



