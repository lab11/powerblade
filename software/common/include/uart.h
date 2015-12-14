#ifndef POWERBLADE_UART_H_
#define POWERBLADE_UART_H_

#include "powerblade_test.h"

char captureType;
char captureBuf[RXLEN - 4];

void uart_init(void);
void uart_enable(bool enable);
void uart_stuff(unsigned int offset, char* srcbuf, unsigned int len);
void uart_send(uint16_t uart_len);

int processMessage(void);

#endif // POWERBLADE_UART_H_
