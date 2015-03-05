#include <msp430.h> 

#include "powerblade_test.h"

unsigned char active;

unsigned char sampleBuf[SAM_BUFSIZE];
unsigned int sampleOffset;

/*
 * main.c
 */
int main(void) {
    WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

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
    P1DIR = 0;
    P1OUT = 0;
    P1REN = 0xFF;

    // Low power in port 2
    P2DIR = 0;
    P2OUT = 0;
    P2REN = 0xFF;

    // Set SEN_EN to output and enable (~200uA)
    SEN_EN_DIR |= SEN_EN_PIN;
    SEN_EN_OUT |= SEN_EN_PIN;
    sampleOffset = 0;

    // Set SYS_EN to output and disable
    SYS_EN_DIR |= SYS_EN_PIN;
    SYS_EN_OUT &= ~SYS_EN_PIN;
    active = 0;

    // Enable ADC for VCC_SENSE, I_SENSE, V_SENSE
    P1SEL1 |= BIT3 + BIT4 + BIT5;
    P1SEL0 |= BIT3 + BIT4 + BIT5;
	ADC10CTL0 |= ADC10ON + ADC10MSC;          	// ADC10ON
  	ADC10CTL1 |= ADC10SHS_1 + ADC10CONSEQ_3;  	// rpt series of ch; TA0.1 trig sample start
  	ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
  	ADC10MCTL0 |= ADC10INCH_5 + ADC10SREF_0;  	// A3,4,5 ADC input select; Vref=AVCC

  	ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
  	ADC10IE |= ADC10IE0;                       	// Enable ADC conv complete interrupt
  
  	// ADC conversion trigger signal - TimerA0.0 (32ms ON-period)
  	TA0CCR0 = ADC_PERCT;						// PWM Period
  	TA0CCR1 = TA0CCR0 / 2;                     	// TA0.1 ADC trigger
  	TA0CCTL1 = OUTMOD_7;                       	// TA0CCR0 toggle
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
    	ADC_Channel = ADC10MCTL0 & ADC10INCH_5;
    	switch(ADC_Channel) {
    	case 5:	// I_SENSE
    		break;
    	case 4:	// V_SENSE
    		break;
    	case 3:	// VCC_SENSE
    		sampleBuf[sampleOffset++] = ADC_Result;
	    	if(ADC_Result > ADC_VMAX) {
	    		SYS_EN_OUT |= SYS_EN_PIN;
	    		active = 1;
	    	}
	    	else {
	    		if(active == 1) {				// Active mode
	    			if(ADC_Result < ADC_VMIN) {	// Fully discharged
	    				SYS_EN_OUT &= ~SYS_EN_PIN;
	    				active = 0;
	    			}
	    		}
	    		else {							// Recharge phase
	    			if(ADC_Result > ADC_VCHG) {	// Fully recharged
	    				SYS_EN_OUT |= SYS_EN_PIN;
	    				active = 1;
	    			}
	    		}
	    	}
	    	break;
    	default: // ADC Reset condition
    		ADC10CTL1 &= ~ADC10CONSEQ_3;
    		ADC10CTL0 &= ~ADC10ENC;
    		ADC10CTL1 |= ADC10CONSEQ_3;
    		ADC10CTL0 |= ADC10ENC;
    		break;
	    }
        break;                          // Clear CPUOFF bit from 0(SR)
    default: break;
  	}

  	// Start next sample/conversion
  	//ADC10CTL0 |= ADC10ENC + ADC10SC;
}




