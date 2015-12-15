/*
 *
 */

#ifndef UART_TYPES_H_
#define UART_TYPES_H_

/**************************************************************************
   UART TYPES SECTION
 **************************************************************************/
#define CALIB_STATE		0x10
#define GT_WATTS		0x11
#define GET_CUROFF		0x12
#define SET_CUROFF		0x13
#define GET_PSCALE		0x14
#define SET_PSCALE		0x15
#define GET_VSCALE		0x16
#define SET_VSCALE		0x17
#define GET_WHSCALE		0x18
#define SET_WHSCALE		0x19
#define SET_SEQ			0x1A
#define START_SAMDATA	0x20
#define CONT_SAMDATA	0x21
#define DONE_SAMDATA	0x22
#define UART_NAK		0xFF

#endif
