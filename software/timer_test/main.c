#include <msp430.h> 

/*
 * This program will initialize timer B0 to run at 6MHz (SMCLK / 4)
 * 	and trigger two timer interrupts:
 * 		TimerB0 R0 will fire every 10us (100kHz)
 * 		TimerB0 R1 will fire every 100us (10kHz)
 *
 * 	Int for R0 toggles P2.0
 * 	INT for R1 toggles P2.1
 *
 * 	Information on Timer B0 can be found on page 356 of the TRM
 * 		(docs/slau272c.pdf or http://www.ti.com/lit/ug/slau272c/slau272c.pdf)
 *
 */
int main(void) {
    WDTCTL = WDTPW | WDTHOLD;					// Stop watchdog timer

    // Set ACLK = MCLK = SMCLK = DCO = 24MHz
    CSCTL0_H = 0xA5;
    CSCTL1 = DCORSEL + DCOFSEL0 + DCOFSEL1;   	// Set max. DCO setting (24 MHz)
    CSCTL2 = SELA_3 + SELS_3 + SELM_3;        	// set ACLK = MCLK = DCO
    CSCTL3 = DIVA_0 + DIVS_0 + DIVM_0;       	// set all dividers to 0
	
    // Pre-load timer registers with count values
    TB0CCR0 = 60;								// 60 counts * 1s/6e6counts = 10us
    TB0CCR1 = 600;								// 600 counts * 1s/6e6counts = 100us

    TB0CCTL0 = CCIE;							// Set TB0.0 to compare, interrupt enabled
    TB0CCTL1 = CCIE;							// Set TB0.1 to compare, interrupt enabled

    TB0CTL = TBSSEL_2 + MC_2 + TBCLR + ID_2;	// TimerB0 set to SMCLK, cont mode, /4

    // Initialize pin outputs
    P2DIR |= (BIT0 + BIT1);
    P2OUT &= ~(BIT0 + BIT1);

    __enable_interrupt();

    while(1);

}

#pragma vector=TIMERB0_VECTOR
__interrupt void TIMER_B0 (void) {

	TB0CCTL0 &= ~CCIFG;

	P2OUT ^= BIT0;

	TB0CCR0 += 60;
}

#pragma vector=TIMERB1_VECTOR
__interrupt void TIMER_B1 (void) {

	TB0CCTL1 &= ~CCIFG;

	P2OUT ^= BIT1;

	TB0CCR1 += 600;
}
