#ifndef POWERBLADE_H
#define POWERBLADE_H

#ifndef DEVICE_NAME
    #define DEVICE_NAME "PowerBlade"
#endif /*DEVICE_NAME*/

#include <stdint.h>

extern uint8_t MAC_ADDR[6];
#define PLATFORM_ID_BYTE 0x70

// GPIO to MSP430
#define MSP430_PIN 5

// UART to MSP430
#define UART_RX_PIN  28
#define UART_TX_PIN  29
#define UART_RTS_PIN 0
#define UART_CTS_PIN 0

// LED for debugging
//  Not actually present on PowerBlade. Exists on squalls
#define ERROR_LED 13

#endif /*POWERBLADE_H*/

