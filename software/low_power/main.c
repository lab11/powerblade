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

bool ready;
uint8_t data;

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

// Transmitted values
uint8_t powerblade_id;
uint32_t sequence;
uint32_t time;
uint8_t Vrms;
uint16_t truePower;
uint16_t apparentPower;
uint32_t wattHours;
uint8_t flags;

// Variables used to center both waveforms at Vcc/2-ish
uint8_t isense_vmax;
uint8_t isense_vmin;
uint8_t vsense_vmax;
uint8_t vsense_vmin;
uint8_t isense_vmid;
uint8_t vsense_vmid;

// Buffer to hold old voltage measurements
// This is used to account for a phase delay between current and voltage
int8_t vbuff[SAMCOUNT];
uint8_t vbuff_head;
uint8_t getVoltageForPhase(uint8_t head);

void uart_send(char* buf, unsigned int len);
char *txBuf;
unsigned int txLen;
unsigned int txCt;

uint32_t SquareRoot(uint32_t a_nInput)
{
    uint32_t op  = a_nInput;
    uint32_t res = 0;
    uint32_t one = 1uL << 30; // The second-to-top bit is set: use 1u << 14 for uint16_t type; use 1uL<<30 for uint32_t type


    // "one" starts at the highest power of four <= than the argument.
    while (one > op)
    {
        one >>= 2;
    }

    while (one != 0)
    {
        if (op >= res + one)
        {
            op = op - (res + one);
            res = res +  2 * one;
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

//    PJOUT = 0;                                // output ACLK
//    PJDIR |= BIT2;
//    PJSEL1 &= ~BIT2;
//    PJSEL0 |= BIT2;

    // Low power in port 1
    P1DIR = BIT2 + BIT6;
    P1OUT = 0;
    P1REN = 0xFF;

    // Low power in port 2
    P2DIR = 0;
    P2OUT = 0;
    P2REN = 0xFF;

    __delay_cycles(4000);                      // ref delay

    // Set SEN_EN to output and disable (~200uA)
    SEN_EN_DIR |= SEN_EN_PIN;
    SEN_EN_OUT &= ~SEN_EN_PIN;

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
    powerblade_id = 0;
    flags = 0;

    // Vmid values are initally set to defaults, adjusted during run
//    vsense_vmax = 0;
//    vsense_vmin = 255;
    vsense_vmid = V_VCC2;
//    isense_vmax = 0;
//    isense_vmin  = 255;
    isense_vmid = I_VCC2;
    vbuff_head = 0;

    // Set SYS_EN to output and disable
    SYS_EN_DIR |= SYS_EN_PIN;
    SYS_EN_OUT &= ~SYS_EN_PIN;
    ready = 0;

    // Set up UART
    P2SEL0 &= ~(BIT0);// + BIT1);
    P2SEL1 |= BIT0;// + BIT1;
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

    // Enable pin interrupt from nrf
    P2DIR &= ~BIT1;
    P2IES &= ~BIT1;	// Low-to-high


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

#pragma vector=PORT2_VECTOR
__interrupt void Port_2(void) {
	P2IFG &= ~BIT1;
	P2IE &= ~BIT1;
	uart_send((char*)&sequence, sizeof(sequence));
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

    		// Vi * G = Vo - Vcc/2
//    		if(ADC_Result > isense_vmid) {
//    			current = (int8_t)(ADC_Result - isense_vmid);// - CUROFF);
//    		}
//    		else {
//    			current = (int8_t)(0 - isense_vmid - ADC_Result);// - CUROFF);
//    		}
    		current = (int8_t)(ADC_Result - isense_vmid);
    		acc_i_rms += current * current;
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

    		// Vi = (RI/RF)(Vcc/2 - Vo)
//    		if(ADC_Result > vsense_vmid) {
//    			voltage = (uint32_t)(ADC_Result - vsense_vmid);
//    		}
//    		else {
//    			voltage = (uint32_t)(vsense_vmid - ADC_Result);
//    		}
    		voltage = (int8_t)(ADC_Result - vsense_vmid);

    		// Store and account for phase offset
    		vbuff[vbuff_head++] = voltage;
    		voltage = vbuff[getVoltageForPhase(vbuff_head)];
    		if(vbuff_head == SAMCOUNT) {
    			vbuff_head = 0;
    		}

    		acc_p_ave += voltage * current;
    		acc_v_rms += voltage * voltage;
    		break;
    	}
    	case 2:	// VCC_SENSE
    		P1OUT |= BIT2;
    		if(ADC_Result < ADC_VMIN) {
    			SYS_EN_OUT &= ~SYS_EN_PIN;
    			ready = 0;
    		}
    		else if(ADC_Result > ADC_VCHG) {
    			SEN_EN_OUT |= SEN_EN_PIN;
    			ready = 1;
    		}
    		else {
    			ready = 0;
    		}
	    	break;
    	default: // ADC Reset condition
    	{
    		TA0CCR0 = 9;
    		ADC10CTL1 &= ~ADC10CONSEQ_3;
    		ADC10CTL0 &= ~ADC10ENC;
    		ADC10CTL1 |= ADC10CONSEQ_3;
    		ADC10CTL0 |= ADC10ENC;

    		P1OUT |= BIT6;

    		sampleCount++;
    		if(sampleCount == SAMCOUNT) { // Entire AC wave sampled (60 Hz)
    			// Reset sampleCount once per wave
    			sampleCount = 0;

    			// Increment energy calc and reset accumulator
    			// TODO: do I need to divide by 60 to get actual watt hours?
    			// Is watt hours the right unit of total energy?
    			//truePower = (uint16_t)(acc_p_ave / SAMCOUNT);
    			wattHoursToAverage += (uint32_t)(acc_p_ave / SAMCOUNT);
    			acc_p_ave = 0;

    			// Calculate Irms, Vrms, and apparent power
    			uint8_t Irms = (uint8_t)SquareRoot(acc_i_rms / SAMCOUNT);
				Vrms = (uint8_t)SquareRoot(acc_v_rms / SAMCOUNT);
				acc_i_rms = 0;
				acc_v_rms = 0;
				//apparentPower = (uint16_t)(Irms * Vrms);
                voltAmpsToAverage += (uint32_t)(Irms * Vrms);

				// Calculate V_SENSE & I_SENSE mid values
				// TODO: maybe dont reset vmin and vmax all the way
				// TODO: maybe just pull them in slightly
				vsense_vmid = (vsense_vmax >> 1) + (vsense_vmin >> 1);
				vsense_vmax = 0;
				vsense_vmin = 255;
				isense_vmid = (isense_vmax >> 1) + (isense_vmin >> 1);
				isense_vmax = 0;
				isense_vmin = 255;

    			measCount++;
    			if(measCount >= 60) { // Another second has passed
    				measCount = 0;

    				sequence++;
    				time++;

                    truePower = (uint16_t)(wattHoursToAverage / 60);
    				wattHours += (uint32_t)truePower;
                    apparentPower = (uint16_t)(voltAmpsToAverage / 60);
    				wattHoursToAverage = 0;
                    voltAmpsToAverage = 0;

					ready = 1;
					if(ready == 1) {
						SYS_EN_OUT |= SYS_EN_PIN;
						__delay_cycles(40000);
						uart_send((char*)&powerblade_id, sizeof(powerblade_id));
						data = 8;
						ready = 0;
					}
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
		// Reset the incrementing variables if we've gotten a confirm
		wattHours = 0;
		time = 0;
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
		case 7:
			uart_send((char*)&sequence, sizeof(sequence));
		case 6:
			uart_send((char*)&time, sizeof(time));
			break;
		case 5:
			uart_send((char*)&Vrms, sizeof(Vrms));
			break;
		case 4:
			uart_send((char*)&truePower, sizeof(truePower));
			break;
		case 3:
			uart_send((char*)&apparentPower, sizeof(apparentPower));
			break;
		case 2:
			uart_send((char*)&wattHours, sizeof(wattHours));
			break;
		case 1:
			uart_send((char*)&flags, sizeof(flags));
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


