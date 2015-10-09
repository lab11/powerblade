/*
 *
 */

#ifndef POWERBLADE_TEST_H_
#define POWERBLADE_TEST_H_

/**************************************************************************
   SYSTEN ENABLE SECTION
 **************************************************************************/
#ifdef VERSION0
   #define SYS_EN_DIR	PJDIR
   #define SYS_EN_OUT	PJOUT
   #define SYS_EN_PIN	BIT3
#endif
#ifdef VERSION1
	#define SYS_EN_DIR	P2DIR
	#define SYS_EN_OUT	P2OUT
	#define SYS_EN_PIN	BIT2
#endif
#if defined (VERSION31) | defined (VERSION32)
	#define SYS_EN_DIR	P1DIR
	#define SYS_EN_OUT	P1OUT
	#define SYS_EN_PIN	BIT6
#endif

/**************************************************************************
   SENSE ENABLE SECTION
 **************************************************************************/
#if defined (VERSION0) | defined (VERSION1)
	#define SEN_EN_DIR	P1DIR
	#define SEN_EN_OUT	P1OUT
	#define SEN_EN_PIN	BIT7
#endif
#if defined (VERSION31) | defined (VERSION32)
	#define SEN_EN_DIR	P2DIR
	#define SEN_EN_OUT	P2OUT
	#define SEN_EN_PIN	BIT2
#endif

/**************************************************************************
   ANALOG SECTION
 **************************************************************************/
/* Supply cutoff information
	Rdiv = 1/3
	Vcc = 3.3V

	Vmin = 3.8V
	Vmin,div = 1.266V
	Nadc,min = 255 * (1.266 / 3.3) = 98 (0x62)

	Vchg = 8.5V
	Vchg,div = 2.833
	Nadc,chg = 255 * (2.833 / 3.3) = 219 (0xDB)

	Vmax = 9.5V
	Vmax,div = 3.17V
	Nadc,max = 255 * (3.17 / 3.3) = 245 (0xF5)
*/
#define ADC_VMIN	0x73
#define ADC_VCHG	0xDB

#define ADC_VCC2	0x80
#define V_VCC2		ADC_VCC2
#define I_VCC2		0x7F

/**************************************************************************
   SENSING CONSTANTS SECTION
 **************************************************************************/
//#define CUROFF		27
#define CUROFF		88
#define PHASEOFF	1	// zero for in-phase
#define SAMCOUNT	42

/**************************************************************************
   SCALING CONSTANTS SECTION
 **************************************************************************/

//#define PSCALE		0x424A
#define PSCALE		0x423E
#define VSCALE		0x7B
#define WHSCALE		0x09

#endif
