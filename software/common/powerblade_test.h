/*
 *
 */

#ifndef POWERBLADE_TEST_H_
#define POWERBLADE_TEST_H_

/**************************************************************************
   SYSTEN ENABLE SECTION
 **************************************************************************/
// SYS_EN = TCK Pins
#define SYS_EN_DIR	PJDIR
#define SYS_EN_OUT	PJOUT
#define SYS_EN_PIN	BIT3

/**************************************************************************
   ANALOG SECTION
 **************************************************************************/
/* Supply cutoff information
	Rdiv = 1/3
	Vcc = 3.3V

	Vmin = 3.8V
	Vmin,div = 1.266V
	Nadc,min = 1023 * (1.266 / 3.3) = 392 (0x188)

	Vmax = 8.9V
	Vmax,div = 2.966V
	Nadc,max = 2013 * (2.966 / 3.3) = 919 (0x397)
*/
#define ADC_VMIN	0x188
#define ADC_VMAX	0x397

#endif