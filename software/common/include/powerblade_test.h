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
	#define ICASE		5
	#define IMCTL0	ADC10INCH_5 + ADC10SREF_0;
#elif defined (VERSION31)
	#define ICASE		0
	#define IMCTL0	ADC10INCH_0 + ADC10SREF_0
#elif defined (VERSION32) | defined (VERSION33)
	#define ICASE		4
	#define IMCTL0		ADC10INCH_4 + ADC10SREF_0
#endif

// Voltage
#if defined (VERSION32) | defined (VERSION33)
	#define VCASE		0
	#define VMCTL0		ADC10INCH_0 + ADC10SREF_0
#else
	#define VCASE		4
	#define VMCTL0		ADC10INCH_4 + ADC10SREF_0
#endif

// VCC Sense
#if defined (VERSION0) | defined (VERSION1)
	#define VCCCASE		3
	#define VCCMCTL0	ADC10INCH_3 + ADC10SREF_0
#else
	#define VCCCASE		5
	#define VCCMCTL0	ADC10INCH_5 + ADC10SREF_0
#endif

/**************************************************************************
   PACKET STRUCTURE SECTION
 **************************************************************************/
#define OFFSET_UARTLEN	0
#define OFFSET_ADLEN	2
#define OFFSET_PBID		3
#define OFFSET_SEQ		4
#define OFFSET_SCALE	8
#define OFFSET_VRMS		12
#define OFFSET_TP		13
#define OFFSET_AP		15
#define OFFSET_WH		17
#define OFFSET_FLAGS	21
#define OFFSET_DATATYPE	22
#define OFFSET_WAVEFORM_I 23
#define OFFSET_WAVEFORM_V 107

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
#if defined (ADC8)
#define ADC_VMIN	0x73
//#define ADC_VCHG	0xDB
#define ADC_VCHG	0xC0
#define ADC_VCC2	0x80
#else
#define ADC_VMIN	0x1CD
//#define ADC_VCHG	0xDB
#define ADC_VCHG	0x302
#define ADC_VCC2	0x200
#endif

#define V_VCC2		ADC_VCC2
#define I_VCC2		ADC_VCC2

/**************************************************************************
   SENSING CONSTANTS SECTION
 **************************************************************************/
#if defined (VERSION32)
#define CUROFF		88
#elif defined (VERSION33)
//#define CUROFF		16
#else
#define CUROFF		27
#endif

#define PHASEOFF	0	// zero for in-phase

/**************************************************************************
   SCALING CONSTANTS SECTION
 **************************************************************************/
//#define PSCALE		0x0001
//#define PSCALE		0x41F4
//#define PSCALE		0x42AC
//#define VSCALE		0x7B
//#define WHSCALE		0x09

/**************************************************************************
   UART CONSTANTS SECTION
 **************************************************************************/
#define UARTLEN		5280
#define UARTBLOCK	528
#define ADLEN		19
#define UARTOVHD	4
#define RXLEN		30

/**************************************************************************
   STATE MACHINE SECTION
 **************************************************************************/
typedef enum {
	pb_normal,
	pb_capture,
	pb_local1,		// Collect raw samples, calculate voff_local and ioff_local
	pb_local2,		// Collect integrate samples, calculate curoff_local
	pb_local3,		// Calculate power, use to calculate pscale_local
	pb_local_done,	// Local calibration done, write values to config
	pb_data
} pb_state_t;



#endif
