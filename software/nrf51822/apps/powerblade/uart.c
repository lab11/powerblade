/*
 * UART driver
 */

// Standard Libraries
#include <stdint.h>
#include <stdbool.h>

// Nordic Libraries
#include "app_util_platform.h"
#include "ble.h"
#include "nrf_gpio.h"
#include "nrf_uart.h"
#include "nrf_drv_common.h"

// Platform, Peripherals, Devices, & Services
#include "powerblade.h"
#include "uart.h"

// uart state control
static bool uart_rxing = false;
static bool uart_txing = false;

void uart_init (void) {
    // apply config
    nrf_gpio_cfg_input(UART_RX_PIN, NRF_GPIO_PIN_NOPULL);
    nrf_gpio_cfg_output(UART_TX_PIN);
    nrf_gpio_pin_set(UART_TX_PIN);
    nrf_uart_txrx_pins_set(NRF_UART0, UART_TX_PIN, UART_RX_PIN);
    nrf_uart_baudrate_set(NRF_UART0, UART_BAUDRATE_BAUDRATE_Baud230400);
    nrf_uart_configure(NRF_UART0, NRF_UART_PARITY_EXCLUDED, NRF_UART_HWFC_DISABLED);

    // interrupts enable
    //Note: sometimes during a connection the UART is delayed by the softdevice
    // we don't want that to happen and our interrupt handler is short enough
    // that it shouldn't cause problems for the softdevice, so let's elevate
    // our priority to maximum (0)
    NVIC_SetPriority(UART0_IRQn, 0);
    NVIC_ClearPendingIRQ(UART0_IRQn);
    NVIC_EnableIRQ(UART0_IRQn);
}

void uart_rx_enable(void) {
    // clear events, start receiving
    uart_rxing = true;
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_ERROR);
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_RXDRDY);
    nrf_uart_task_trigger(NRF_UART0, NRF_UART_TASK_STARTRX);

    // receive at high-speed UART (232400 baud)
    nrf_uart_baudrate_set(NRF_UART0, UART_BAUDRATE_BAUDRATE_Baud230400);

    // enable interrupts on UART RX
    nrf_uart_int_enable(NRF_UART0, NRF_UART_INT_MASK_RXDRDY);

    // enable module
    nrf_uart_enable(NRF_UART0);
}

void uart_tx_enable(void) {
    // clear events, start transmitting
    uart_txing = true;
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_ERROR);
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_TXDRDY);
    nrf_uart_task_trigger(NRF_UART0, NRF_UART_TASK_STARTTX);

    // send at low-speed UART (9600 baud)
    nrf_uart_baudrate_set(NRF_UART0, UART_BAUDRATE_BAUDRATE_Baud9600);

    // enable interrupts on UART TX
    nrf_uart_int_enable(NRF_UART0, NRF_UART_INT_MASK_TXDRDY);

    // enable module
    nrf_uart_enable(NRF_UART0);
}

void uart_rx_disable(void) {
    // stop receiving, disable module if not still in use
    nrf_uart_task_trigger(NRF_UART0, NRF_UART_TASK_STOPRX);
    uart_rxing = false;

    if (!uart_txing && !uart_rxing) {
        nrf_uart_disable(NRF_UART0);
    }
}

void uart_tx_disable(void) {
    // stop transmitting, disable module if not still in use
    nrf_uart_task_trigger(NRF_UART0, NRF_UART_TASK_STOPTX);
    uart_txing = false;

    // reset to low-speed UART (9600 baud)
    nrf_uart_baudrate_set(NRF_UART0, UART_BAUDRATE_BAUDRATE_Baud9600);

    if (!uart_txing && !uart_rxing) {
        nrf_uart_disable(NRF_UART0);
    }
}

