/*
 *
 */

#ifndef UART_TYPES_H_
#define UART_TYPES_H_

/**************************************************************************
   UART TYPES SECTION
 **************************************************************************/
#define GET_CONF        0x10
#define SET_CONF        0x11
#define GET_VER         0x12
#define SET_SEQ         0x1C
#define CLR_WH          0x1D
#define START_SAMDATA   0x20
#define CONT_SAMDATA    0x21
#define DONE_SAMDATA    0x22
#define UART_NAK        0xFF


/**************************************************************************
   UART DATA LENGTHS SECTION
 **************************************************************************/
#define SAMDATA_MAX_LEN 504


/**************************************************************************
   POWERBLADE CONFIGURATION STRUCT
 **************************************************************************/
typedef struct {
    int8_t voff;
    int8_t ioff;
    int16_t curoff;
    uint16_t pscale;
    uint8_t vscale;
    uint8_t whscale;
} PowerBladeConfig_t;


#endif
