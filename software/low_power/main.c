#include <msp430.h> 

#include "powerblade_test.h"

unsigned char active;

/*
 * main.c
 */
int main(void) {
    WDTCTL = WDTPW | WDTHOLD;	// Stop watchdog timer

    // Configure 1MHz SMCLK, MCLK, ACLK
    CSCTL0_H = 0xA5;
    CSCTL1 = DCOFSEL0 + DCOFSEL1;   			// Set 8MHz. DCO setting
    CSCTL2 = SELA_3 + SELS_3 + SELM_3;        	// set ACLK = MCLK = DCO
    CSCTL3 = DIVA_3 + DIVS_3 + DIVM_3;        	// set all dividers to /8

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

    // Set SYS_EN to output and disable
    SYS_EN_DIR |= SYS_EN_PIN;
    SYS_EN_OUT &= ~SYS_EN_PIN;
    active = 0;

    // Enable ADC for VCC_SENSE
    P1SEL1 |= BIT3;
    P1SEL0 |= BIT3;
    ADC10CTL0 |= ADC10SHT_2 + ADC10ON;        // ADC10ON, S&H=16 ADC clks
	ADC10CTL1 |= ADC10SHP;                    // ADCCLK = MODOSC; sampling timer
	ADC10CTL2 |= ADC10RES;                    // 10-bit conversion results
	ADC10MCTL0 |= ADC10INCH_3;                // A3 ADC input select; Vref=AVCC
	ADC10IE |= ADC10IE0;                      // Enable ADC conv complete interrupt

	ADC10CTL0 |= ADC10ENC + ADC10SC;        // Sampling and conversion start
	__bis_SR_register(CPUOFF + GIE);        // LPM0, ADC10_ISR will force exit
	
	return 0;
}


#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR(void) {

	unsigned int ADC_Result;

	switch(__even_in_range(ADC10IV,12))
  	{
    	case  0: break;                          // No interrupt
    	case  2: break;                          // conversion result overflow
    	case  4: break;                          // conversion time overflow
    	case  6: break;                          // ADC10HI
    	case  8: break;                          // ADC10LO
    	case 10: break;                          // ADC10IN
    	case 12: ADC_Result = ADC10MEM0;
    		if(ADC_Result > ADC_VMAX) {
    			// Bad news bears
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
        	break;                          // Clear CPUOFF bit from 0(SR)                         
    	default: break; 
  	}

  	// Start next sample/conversion
  	ADC10CTL0 |= ADC10ENC + ADC10SC;
}




