#include <msp430.h> 

#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#include "powerblade_test.h"

#pragma SET_DATA_SECTION(".fram_vars")
//volatile unsigned char vread[SAM_BUFSIZE];
//volatile unsigned char iread[SAM_BUFSIZE];
//volatile unsigned char vccread[SAM_BUFSIZE];
//unsigned int sampleOffset;
//unsigned int lock;

bool ready;

uint8_t sampleCount;
uint8_t measCount;

uint8_t current;
uint16_t acc_p_ave;
uint16_t acc_i_rms;
uint16_t acc_v_rms;

uint32_t tot_power;

#pragma SET_DATA_SECTION()

/*
 * main.c
 */
int main(void) {
    WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

//    if(lock == 1) {
//    	while(1);
//    }
//    lock = 1;

    // XT1 Setup
    PJSEL0 |= BIT4 + BIT5;

    CSCTL0_H = 0xA5;
  	CSCTL1 = DCOFSEL0 + DCOFSEL1;             // Set max. DCO setting
  	CSCTL2 = SELA_0 + SELS_3 + SELM_3;        // set ACLK = XT1; MCLK = DCO
  	CSCTL3 = DIVA_0 + DIVS_3 + DIVM_3;        // set all dividers
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

    // Set SEN_EN to output and disable (~200uA)
    SEN_EN_DIR |= SEN_EN_PIN;
    SEN_EN_OUT &= ~SEN_EN_PIN;

    // Zero all sensing values
    sampleCount = 0;
    measCount = 0;
    acc_p_ave = 0;
    acc_i_rms = 0;
    acc_v_rms = 0;
    tot_power = 0;

    // Set SYS_EN to output and disable
    SYS_EN_DIR |= SYS_EN_PIN;
    SYS_EN_OUT &= ~SYS_EN_PIN;
    ready = 0;

    // Enable ADC for VCC_SENSE, I_SENSE, V_SENSE
    P1SEL1 |= BIT3 + BIT4 + BIT5;
    P1SEL0 |= BIT3 + BIT4 + BIT5;
	ADC10CTL0 |= ADC10ON;// + ADC10MSC;          	// ADC10ON
  	ADC10CTL1 |= ADC10SHS_1 + ADC10SHP + ADC10CONSEQ_3;  	// rpt series of ch; TA0.1 trig sample start
  	ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
  	ADC10MCTL0 |= ADC10INCH_5 + ADC10SREF_0;  	// A3,4,5 ADC input select; Vref=AVCC

  	ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
  	ADC10IE |= ADC10IE0;                       	// Enable ADC conv complete interrupt
  
  	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
  	TA0CCR0 = 2;						// PWM Period
  	TA0CCR1 = 1;                     	// TA0.1 ADC trigger
  	TA0CCTL1 = OUTMOD_7;// + CCIE;                       	// TA0CCR0 toggle
  	TA0CTL = TASSEL_1 + MC_1 + TACLR;          	// ACLK, up mode

  	__bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts

	return 0;
}




#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR(void) {

	unsigned int ADC_Result;
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
    		TA0CCR0 = 2;
    		P1OUT |= BIT2;
    		current = ADC_Result;
    		acc_i_rms += 1;//pow(current, 2);
    		//ADC10CTL0 |= ADC10SC;
    		break;
    	case 3:	// V_SENSE
    	{
    		P1OUT |= BIT2;
    		uint8_t voltage = ADC_Result;
    		acc_p_ave += voltage * current;
    		acc_v_rms += 1;//pow(voltage, 2);
    		break;
    	}
    	case 2:	// VCC_SENSE
//    		vccread[sampleOffset++] = ADC_Result;
//    		if(sampleOffset == 100) {
//    			sampleOffset = 0;
//    		}
//	    	if(ADC_Result > ADC_VMAX) {
//	    		SYS_EN_OUT |= SYS_EN_PIN;
//	    		SEN_EN_OUT |= SEN_EN_PIN;
//	    		active = 1;
//	    	}
//	    	else {
//	    		if(active == 1) {				// Active mode
//	    			if(ADC_Result < ADC_VMIN) {	// Fully discharged
//	    				SYS_EN_OUT &= ~SYS_EN_PIN;
//	    				active = 0;
//	    			}
//	    		}
//	    		else {							// Recharge phase
//	    			if(ADC_Result > ADC_VCHG) {	// Fully recharged
//	    				SYS_EN_OUT |= SYS_EN_PIN;
//	    				SEN_EN_OUT |= SEN_EN_PIN;
//	    				active = 1;
//	    			}
//	    		}
//	    	}
    		P1OUT |= BIT2;
    		if(ADC_Result < ADC_VMIN) {
    			SYS_EN_OUT &= ~SYS_EN_PIN;
    			//P1OUT &= ~BIT2;
    			ready = 0;
    		}
    		else if(ADC_Result > ADC_VCHG) {
    			SEN_EN_OUT |= SEN_EN_PIN;
    			ready = 1;
    		}
    		else {
    			ready = 0;
    			//P1OUT &= ~BIT2;
    		}
	    	break;
    	default: // ADC Reset condition
    	{
    		TA0CCR0 = 18;
    		ADC10CTL1 &= ~ADC10CONSEQ_3;
    		ADC10CTL0 &= ~ADC10ENC;
    		ADC10CTL1 |= ADC10CONSEQ_3;
    		ADC10CTL0 |= ADC10ENC;

    		P1OUT |= BIT6;

    		sampleCount++;
    		if(sampleCount == 21) { // Entire AC wave sampled
    			sampleCount = 0;
    			uint32_t realPower = acc_p_ave / 21;
    			tot_power += realPower;

    			measCount++;
//    			P1OUT |= BIT2;
    			if(measCount == 60) { // Another second has passed
    				measCount = 0;
					uint16_t Irms = 1;//sqrt(acc_i_rms / 21);
					uint16_t Vrms = 1;//sqrt(acc_v_rms / 21);
					uint32_t apparentPower = 1;//Irms * Vrms;

					if(ready == 1) {
						SYS_EN_OUT |= SYS_EN_PIN;
						ready = 0;
						tot_power = 0;
					}
    			}
    		}
//    		else {
//    			P1OUT &= ~BIT2;
//    		}

    		break;
    	}
	    }
        break;                          // Clear CPUOFF bit from 0(SR)
    default: break;
  	}
	P1OUT &= ~(BIT2 + BIT6);
}




