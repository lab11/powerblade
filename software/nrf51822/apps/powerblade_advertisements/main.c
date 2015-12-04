/*
 * PowerBlade BLE application
 */

// Standard Libraries
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

// Nordic Libraries
#include "ble.h"
#include "ble_advdata.h"
#include "app_timer.h"
#include "app_util_platform.h"
//#include "app_uart.h"
#include "nrf_uart.h"
#include "nrf_drv_common.h"

// Platform, Peripherals, Devices, Services
#include "ble_config.h"
#include "powerblade.h"
#include "led.h"
#include "simple_ble.h"
#include "simple_adv.h"
#include "eddystone.h"

static ble_app_t app;

#define PHYSWEB_URL "goo.gl/jEKPu9"

// timer configuration
#define TIMER_PRESCALER     0
#define TIMER_OP_QUEUE_SIZE 4
APP_TIMER_DEF(enable_uart_timer);
APP_TIMER_DEF(start_eddystone_timer);
APP_TIMER_DEF(start_manufdata_timer);
#define EDDYSTONE_ADV_DURATION APP_TIMER_TICKS(200, TIMER_PRESCALER)
#define MANUFDATA_ADV_DURATION APP_TIMER_TICKS(800, TIMER_PRESCALER)
#define UART_SLEEP_DURATION    APP_TIMER_TICKS(940, TIMER_PRESCALER)

// advertisement data collected from UART
#define POWERBLADE_ADV_DATA_LEN 0x13
#define POWERBLADE_ADV_DATA_MAX_LEN 24 // maximum manufacturer specific advertisement data size
static uint8_t powerblade_adv_data[POWERBLADE_ADV_DATA_MAX_LEN];
static uint8_t powerblade_adv_data_len;

void start_eddystone_adv (void) {
    uint32_t err_code;

    // Advertise physical web address for PowerBlade summon app
    eddystone_adv(PHYSWEB_URL, NULL);

    err_code = app_timer_start(start_manufdata_timer, EDDYSTONE_ADV_DURATION, NULL);
    APP_ERROR_CHECK(err_code);
}

void init_adv_data (void) {
    // Default values, helpful for debugging
    powerblade_adv_data[0] = 0x01; // Version
    
    powerblade_adv_data[1] = 0x00;
    powerblade_adv_data[2] = 0x00;
    powerblade_adv_data[3] = 0x00;
    powerblade_adv_data[4] = 0x01; // Sequence

    powerblade_adv_data[5] = 0x42;
    powerblade_adv_data[6] = 0x4A; // P_Scale

    powerblade_adv_data[7] = 0x7B; // V_Scale

    powerblade_adv_data[8] = 0x09; // WH_Scale

    powerblade_adv_data[9] = 0x31; // V_RMS

    powerblade_adv_data[10] = 0x08;
    powerblade_adv_data[11] = 0x02; // True Power

    powerblade_adv_data[12] = 0x0A;
    powerblade_adv_data[13] = 0x1A; // Apparent Power

    powerblade_adv_data[14] = 0x00;
    powerblade_adv_data[15] = 0x00;
    powerblade_adv_data[16] = 0x01;
    powerblade_adv_data[17] = 0x0D; // Watt Hours

    powerblade_adv_data[18] = 0x00; // Flags
}

void start_manufdata_adv (void) {
    uint32_t err_code;

    // Advertise PowerBlade data payload as manufacturer specific data
    ble_advdata_manuf_data_t manuf_specific_data;
    manuf_specific_data.company_identifier = APP_COMPANY_IDENTIFIER;
    manuf_specific_data.data.p_data = powerblade_adv_data;
    manuf_specific_data.data.size   = powerblade_adv_data_len;
    simple_adv_manuf_data(&manuf_specific_data);

    err_code = app_timer_start(start_eddystone_timer, MANUFDATA_ADV_DURATION, NULL);
    APP_ERROR_CHECK(err_code);
}

static void uart_disable(void) {
    // stop receiving, disable module
    nrf_uart_task_trigger(NRF_UART0, NRF_UART_TASK_STOPRX);
    nrf_uart_disable(NRF_UART0);
}

static void uart_enable(void) {
    // enable module, clear events, start receiving
    nrf_uart_enable(NRF_UART0);
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_ERROR);
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_RXDRDY);
    nrf_uart_task_trigger(NRF_UART0, NRF_UART_TASK_STARTRX);

    // enable interrupts on UART RX
    nrf_uart_int_enable(NRF_UART0, NRF_UART_INT_MASK_RXDRDY);
}   

void uart_init (void) {
    // apply config
    nrf_gpio_cfg_input(UART_RX_PIN, NRF_GPIO_PIN_NOPULL);
    nrf_uart_txrx_pins_set(NRF_UART0, 0, UART_RX_PIN);
    nrf_uart_baudrate_set(NRF_UART0, UART_BAUDRATE_BAUDRATE_Baud38400);
    nrf_uart_configure(NRF_UART0, NRF_UART_PARITY_EXCLUDED, NRF_UART_HWFC_DISABLED);

    // interrupts enable
    nrf_drv_common_irq_enable(UART0_IRQn, APP_IRQ_PRIORITY_LOW);
}

void UART0_IRQHandler (void) {
    static uint16_t uart_len = 0;
    static uint16_t uart_index = 0;
    static uint8_t adv_len = 0;

    // data is available
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_RXDRDY);
    uint8_t uart_data = nrf_uart_rxd_get(NRF_UART0);

    // parse data from MSP430 based on index
    if (uart_index == 0) {
        // UART len MSB
        uart_len = (uart_data << 8 | 0x00);

    } else if (uart_index == 1) {
        // UART len LSB
        uart_len |= uart_data;

    } else if (uart_index == 2) {
        // ADV len
        adv_len = uart_data;
        powerblade_adv_data_len = adv_len;

    } else if (adv_len > 0 && (uart_index-3) < adv_len) {
        // Advertisement data
        uint8_t adv_index = uart_index-3;
        if (adv_index < POWERBLADE_ADV_DATA_MAX_LEN) {
            // only record the data that fits
            powerblade_adv_data[adv_index] = uart_data;
        }

    } else if ((uart_len-1-adv_len) > 0 && uart_index < (uart_len+2)) {
        // Additional UART data
        // Do nothing with data for now
    }

    uart_index++;
    if (uart_index >= 3 && uart_index >= (uart_len+2)) {
        // UART data is finished when we have received the whole header, plus
        //  whatever Advertisement and Additional data exists

        // turn off UART until next window
        uart_disable();
        app_timer_start(enable_uart_timer, UART_SLEEP_DURATION, NULL);

        // update advertisement
        //NOTE: this is safe to call no matter where in the
        //  Eddystone/Manuf Data we are. If called during Manuf Data,
        //  nothing changes (second call to timer_start does nothing).
        //  If called during Eddystone, timing is screwed up, but it'll fix
        //  itself within one cycle
        start_manufdata_adv();

        uart_len = 0;
        uart_index = 0;
        adv_len = 0;
    }
}

void timers_init (void) {
    uint32_t err_code;

    APP_TIMER_INIT(TIMER_PRESCALER, TIMER_OP_QUEUE_SIZE, false);

    err_code = app_timer_create(&enable_uart_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)uart_enable);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&start_eddystone_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)start_eddystone_adv);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&start_manufdata_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)start_manufdata_adv);
    APP_ERROR_CHECK(err_code);
}

int main(void) {
    // Initialization
    app.simple_ble_app = simple_ble_init(&ble_config);
    uart_init();
    timers_init();
    init_adv_data();

    // Initialization complete
    start_manufdata_adv();
    uart_enable();

    while (1) {
        power_manage();
    }
}

