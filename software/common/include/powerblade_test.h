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
#if defined (VERSION31) | defined (VERSION32) | defined (VERSION33)
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
#if defined (VERSION31) | defined (VERSION32) | defined (VERSION33)
	#define SEN_EN_DIR	P2DIR
	#define SEN_EN_OUT	P2OUT
	#define SEN_EN_PIN	BIT2
#endif

/**************************************************************************
   ADC ORDERING SECTION
 **************************************************************************/
// Current
#if defined (VERSION0) | defined (VERSION1)
	#define ICASE		4
	#define IMCTL0	ADC10INCH_5 + ADC10SREF_0;
#elif defined (VERSION31)
	#define ICASE		5
	#define IMCTL0	ADC10INCH_0 + ADC10SREF_0
#elif defined (VERSION32) | defined (VERSION33)
	#define ICASE		3
	#define IMCTL0		ADC10INCH_4 + ADC10SREF_0
#endif

// Voltage
#if defined (VERSION32) | defined (VERSION33)
	#define VCASE		5
	#define VMCTL0		ADC10INCH_0 + ADC10SREF_0
#else
	#define VCASE		3
	#define VMCTL0		ADC10INCH_4 + ADC10SREF_0
#endif

// VCC Sense
#if defined (VERSION0) | defined (VERSION1)
	#define VCCCASE		2
	#define VCCMCTL0	ADC10INCH_3 + ADC10SREF_0
#else
	#define VCCCASE		4
	#define VCCMCTL0	ADC10INCH_5 + ADC10SREF_0
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
#if defined (VERSION32)
#define CUROFF		88
#elif defined (VERSION33)
#define CUROFF		108
#else
#define CUROFF		27
#endif

#define PHASEOFF	0	// zero for in-phase
#define SAMCOUNT	42

/**************************************************************************
   SCALING CONSTANTS SECTION
 **************************************************************************/
//#define PSCALE		0x0001
//#define PSCALE		0x41F4
#define PSCALE		0x428F
#define VSCALE		0x7B
#define WHSCALE		0x09

/**************************************************************************
   UART CONSTANTS SECTION
 **************************************************************************/
#define UARTLEN		23
#define RXLEN		30

#endif
