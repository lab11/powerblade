/*
 *
 */

#ifndef POWERBLADE_TEST_H_
#define POWERBLADE_TEST_H_

/**************************************************************************
   SAMPLE BUFFER SECTION
 **************************************************************************/
#define SAM_BUFSIZE	1000

/**************************************************************************
   SYSTEN ENABLE SECTION
 **************************************************************************/
// SYS_EN = TCK Pins
#define SYS_EN_DIR	PJDIR
#define SYS_EN_OUT	PJOUT
#define SYS_EN_PIN	BIT3

/**************************************************************************
   SENSE ENABLE SECTION
 **************************************************************************/
// SEN_EN = P1.7
#define SYS_EN_DIR	P1DIR
#define SYS_EN_OUT	P1OUT
#define SYS_EN_PIN	BIT7

/**************************************************************************
   ANALOG SECTION
 **************************************************************************/
/* Supply cutoff information
	Rdiv = 1/3
	Vcc = 3.3V

	Vmin = 3.8V
	Vmin,div = 1.266V
	Nadc,min = 255 * (1.266 / 3.3) = 98 (0x62)

	Vmax = 9V
	Vmax,div = 3V
	Nadc,max = 255 * (3 / 3.3) = 231 (0xE7)
*/
#define ADC_VMIN	0x62
#define ADC_VMAX	0xE7

#define ADC_PERUS	500
#define ADC_PERCT	ADC_PERMS*(32768/1E6)	

#endif
