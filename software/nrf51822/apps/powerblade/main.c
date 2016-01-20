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
#include "nrf_uart.h"
#include "nrf_drv_common.h"

// Platform, Peripherals, Devices, & Services
#include "powerblade_states.h"
#include "uart.h"
#include "uart_types.h"
#include "powerblade.h"
#include "led.h"
#include "simple_ble.h"
#include "simple_adv.h"
#include "eddystone.h"
#include "checksum.h"


/**************************************************
 * Function Protoypes
 **************************************************/
void start_eddystone_adv(void);
void init_adv_data(void);
void start_manufdata_adv(void);

void UART0_IRQHandler(void);
void uart_rx_handler(void);
void process_rx_packet(uint16_t packet_len);
void process_additional_data(uint8_t* buf, uint16_t len);
void uart_tx_handler(void);
void uart_send(uint8_t* data, uint16_t len);
void uart_resend(void);

void services_init(void);
void ble_evt_write (ble_evt_t* p_ble_evt);

void transmit_message(void);
void on_receive_message(uint8_t* buf, uint16_t len);

void timers_init(void);
int main(void);


/**************************************************
 * Define and Globals
 **************************************************/

// simple_ble configuration for advertising and connections
static const simple_ble_config_t ble_config = {
    .platform_id       = PLATFORM_ID_BYTE,  // used as 4th octet in device BLE address
    .device_id         = DEVICE_ID_DEFAULT, // 5th and 6th octet in device BLE address
    .adv_name          = DEVICE_NAME,       // used in advertisements if there is room
    .adv_interval      = MSEC_TO_UNITS(200, UNIT_0_625_MS),
    .min_conn_interval = MSEC_TO_UNITS(50, UNIT_1_25_MS),
    .max_conn_interval = MSEC_TO_UNITS(100, UNIT_1_25_MS),
};
static simple_ble_app_t* simple_ble_app;

// timer configuration
APP_TIMER_DEF(enable_uart_timer);
APP_TIMER_DEF(start_eddystone_timer);
APP_TIMER_DEF(start_manufdata_timer);
#define EDDYSTONE_ADV_DURATION APP_TIMER_TICKS(200, APP_TIMER_PRESCALER)
#define MANUFDATA_ADV_DURATION APP_TIMER_TICKS(800, APP_TIMER_PRESCALER)
#define UART_SLEEP_DURATION    APP_TIMER_TICKS(940, APP_TIMER_PRESCALER)

// advertisement data
#define PHYSWEB_URL "goo.gl/9aD6Wi"
#define UMICH_COMPANY_IDENTIFIER    0x02E0
#define POWERBLADE_SERVICE_IDENTIFIER 0x11
#define ADV_DATA_MAX_LEN 24 // maximum manufacturer specific advertisement data size
static uint8_t powerblade_adv_data[ADV_DATA_MAX_LEN];
static uint8_t powerblade_adv_data_len = 0;

// service for device configuration
static simple_ble_service_t config_service = {
    .uuid128 = {{0x99, 0xf9, 0xac, 0xe5, 0x57, 0xb9, 0x43, 0xec,
                 0x88, 0xf8, 0x88, 0xb9, 0x4d, 0xa1, 0x80, 0x50}}};

    // holds various configuration values which are broken out in characteristics
    static PowerBladeConfig_t powerblade_config = {0};

    // characteristic to display device status
    static simple_ble_char_t config_status_char = {.uuid16 = 0x4DA2};

    // characteristic to access voltage offset
    static simple_ble_char_t config_voff_char = {.uuid16 = 0x4DA3};

    // characteristic to access current offset
    static simple_ble_char_t config_ioff_char = {.uuid16 = 0x4DA4};

    // characteristic to access current offset post-integration
    static simple_ble_char_t config_curoff_char = {.uuid16 = 0x4DA5};

    // characteristic to access power scaling value
    static simple_ble_char_t config_pscale_char = {.uuid16 = 0x4DA6};

    // characteristic to access voltage scaling value
    static simple_ble_char_t config_vscale_char = {.uuid16 = 0x4DA7};

    // characteristic to access watt-hours scaling value
    static simple_ble_char_t config_whscale_char = {.uuid16 = 0x4DA8};

// service for sample data collection
static simple_ble_service_t rawSample_service = {
    .uuid128 = {{0x31, 0x15, 0xd4, 0x39, 0x2a, 0x88, 0x4e, 0x1c,
                 0x8c, 0xcc, 0xf8, 0x7c, 0x01, 0xaf, 0xad, 0xce}}};

    // characteristic to start raw sample collection
    static simple_ble_char_t rawSample_char_begin = {.uuid16 = 0x01B0};
    static bool begin_rawSample;

    // characteristic to provide raw samples to users
    static simple_ble_char_t rawSample_char_data = {.uuid16 = 0x01B1};
    static uint8_t raw_sample_data[SAMDATA_MAX_LEN];

    // characteristic to indicate new data is available
    static simple_ble_char_t rawSample_char_status = {.uuid16 = 0x01B2};
    static uint8_t rawSample_status;

// uart buffers
// max length is: total length + adv length + adv data + add type + add data + checksum
#define RX_DATA_MAX_LEN 2+1+ADV_DATA_MAX_LEN+1+SAMDATA_MAX_LEN+1
static uint8_t rx_data[RX_DATA_MAX_LEN];
static uint8_t* tx_data;
static uint16_t tx_data_len = 0;
static uint8_t tx_buffer[4+sizeof(powerblade_config)];

// states for handling transmissions to the MSP
static bool already_transmitted = false;
static NakState_t nak_state = NAK_NONE;
static RawSampleState_t rawSample_state = RS_NONE;
static ConfigurationState_t config_state = CONF_NONE;
//static StartupState_t startup_state = STARTUP_GET_CONF;
static StartupState_t startup_state = STARTUP_SET_SEQ;
static StatusCode_t status_code = STATUS_NONE;


/**************************************************
 * Advertisements
 **************************************************/

void start_eddystone_adv (void) {
    uint32_t err_code;

    // Advertise physical web address for PowerBlade summon app
    eddystone_adv(PHYSWEB_URL, NULL);

    err_code = app_timer_start(start_manufdata_timer, EDDYSTONE_ADV_DURATION, NULL);
    APP_ERROR_CHECK(err_code);
}

void init_adv_data (void) {
    // Default values, helpful for debugging
    powerblade_adv_data[0] = POWERBLADE_SERVICE_IDENTIFIER; // Service ID

    powerblade_adv_data[1] = 0x01; // Version
    
    powerblade_adv_data[2] = 0x01;
    powerblade_adv_data[3] = 0x01;
    powerblade_adv_data[4] = 0x01;
    powerblade_adv_data[5] = 0x01; // Sequence

    powerblade_adv_data[6] = 0x42;
    powerblade_adv_data[7] = 0x4A; // P_Scale

    powerblade_adv_data[8] = 0x7B; // V_Scale

    powerblade_adv_data[9] = 0x09; // WH_Scale

    powerblade_adv_data[10] = 0x31; // V_RMS

    powerblade_adv_data[11] = 0x08;
    powerblade_adv_data[12] = 0x02; // True Power

    powerblade_adv_data[13] = 0x0A;
    powerblade_adv_data[14] = 0x1A; // Apparent Power

    powerblade_adv_data[15] = 0x00;
    powerblade_adv_data[16] = 0x00;
    powerblade_adv_data[17] = 0x01;
    powerblade_adv_data[18] = 0x0D; // Watt Hours

    powerblade_adv_data[19] = 0x00; // Flags
    powerblade_adv_data_len = 20;
}

void start_manufdata_adv (void) {
    uint32_t err_code;

    // Advertise PowerBlade data payload as manufacturer specific data
    ble_advdata_manuf_data_t manuf_specific_data;
    manuf_specific_data.company_identifier = UMICH_COMPANY_IDENTIFIER;
    manuf_specific_data.data.p_data = powerblade_adv_data;
    manuf_specific_data.data.size   = powerblade_adv_data_len;
    simple_adv_manuf_data(&manuf_specific_data);

    err_code = app_timer_start(start_eddystone_timer, MANUFDATA_ADV_DURATION, NULL);
    APP_ERROR_CHECK(err_code);
}

/**************************************************
 * UART
 **************************************************/

void UART0_IRQHandler (void) {
    if (nrf_uart_event_check(NRF_UART0, NRF_UART_EVENT_RXDRDY)) {
        uart_rx_handler();
    } else if (nrf_uart_event_check(NRF_UART0, NRF_UART_EVENT_TXDRDY)) {
        uart_tx_handler();
    }
}

void uart_rx_handler (void) {
    static uint16_t packet_len = 0;
    static uint16_t rx_index = 0;

    // data is available
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_RXDRDY);
    rx_data[rx_index] = nrf_uart_rxd_get(NRF_UART0);
    rx_index++;

    // check if we have received the entire packet
    //  This can't occur until we have length, adv length, and checksum
    if (rx_index >= 4) {

        // parse out expected packet length
        if (packet_len == 0) {
            packet_len = (rx_data[0] << 8 | rx_data[1]);
        }

        // process packet if we have all of it
        if (rx_index >= packet_len || rx_index >= RX_DATA_MAX_LEN) {
            process_rx_packet(packet_len);
            packet_len = 0;
            rx_index = 0;
        }
    }
}

void process_rx_packet(uint16_t packet_len) {

    // turn off UART until next window
    uart_rx_disable();
    app_timer_start(enable_uart_timer, UART_SLEEP_DURATION, NULL);

    // a new window for transmission to the MSP430 is available
    already_transmitted = false;

    // check CRC
    if (additive_checksum(rx_data, packet_len-1) == rx_data[packet_len-1]) {

        // check validity of advertisement length
        uint8_t adv_len = rx_data[2];
        if (4+adv_len <= packet_len) {

            // limit to valid advertisement length
            if (adv_len > ADV_DATA_MAX_LEN) {
                adv_len = ADV_DATA_MAX_LEN;
            }

            // update advertisement
            //  first byte of adv_data is service_id, skip it
            //NOTE: this is safe to call no matter where in the
            //  Eddystone/Manuf Data we are. If called during Manuf Data,
            //  nothing changes (second call to timer_start does nothing).
            //  If called during Eddystone, timing is screwed up, but it'll fix
            //  itself within one cycle
            powerblade_adv_data_len = 1+adv_len;
            memcpy(&(powerblade_adv_data[1]), &(rx_data[3]), adv_len);
            start_manufdata_adv();

            // handle additional UART data, if any
            uint8_t* additional_data = &(rx_data[3+adv_len]);
            uint16_t additional_data_length = packet_len - (4 + adv_len);
            on_receive_message(additional_data, additional_data_length);
        }
    } else {
        // need to send a nak
        nak_state = NAK_CHECKSUM;
        raw_sample_data[0] = 0xA5;
    }
}

void uart_tx_handler (void) {
    static uint16_t tx_index = 0;

    // clear event
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_TXDRDY);

    // check if there is more data to send
    if (tx_index < tx_data_len) {
        nrf_uart_txd_set(NRF_UART0, tx_data[tx_index]);
        tx_index++;
    } else {
        tx_index = 0;
        uart_tx_disable();
    }
}

void uart_send (uint8_t* data, uint16_t len) {
    // setup data
    tx_data = data;
    tx_data_len = len;

    // begin sending data
    uart_tx_enable();
    uart_tx_handler();

    // transmission sent for this cycle
    already_transmitted = true;
}

/**************************************************
 * Services
 **************************************************/

void services_init (void) {

    // Add configuration service
    simple_ble_add_service(&config_service);

        // Add characteristic to display status codes
        simple_ble_add_characteristic(1, 0, 1, 0, // read, write, notify, vlen
                sizeof(status_code), (uint8_t*)&status_code,
                &config_service, &config_status_char);

        // Add characteristic to access voff
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                sizeof(powerblade_config.voff), (uint8_t*)&powerblade_config.voff,
                &config_service, &config_voff_char);

        // Add characteristic to access ioff
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                sizeof(powerblade_config.ioff), (uint8_t*)&powerblade_config.ioff,
                &config_service, &config_ioff_char);

        // Add characteristic to access curoff
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                sizeof(powerblade_config.curoff), (uint8_t*)&powerblade_config.curoff,
                &config_service, &config_curoff_char);

        // Add characteristic to access pscale
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                sizeof(powerblade_config.pscale), (uint8_t*)&powerblade_config.pscale,
                &config_service, &config_pscale_char);

        // Add characteristic to access vscale
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                sizeof(powerblade_config.vscale), (uint8_t*)&powerblade_config.vscale,
                &config_service, &config_vscale_char);

        // Add characteristic to access whscale
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                sizeof(powerblade_config.whscale), (uint8_t*)&powerblade_config.whscale,
                &config_service, &config_whscale_char);

    // Add raw sample download service
    simple_ble_add_service(&rawSample_service);

        // Add the characteristic to signal grab sample data
        begin_rawSample = false;
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                1, (uint8_t*)&begin_rawSample,
                &rawSample_service, &rawSample_char_begin);

        // Add the characteristic to provide raw samples
        memset(raw_sample_data, 0x00, SAMDATA_MAX_LEN);
        simple_ble_add_characteristic(1, 0, 0, 1, // read, write, notify, vlen
                SAMDATA_MAX_LEN, (uint8_t*)raw_sample_data,
                &rawSample_service, &rawSample_char_data);
        // must initialize to maximum valid length. Now reset down to 1
        simple_ble_update_char_len(&rawSample_char_data, 1);

        // Add the characteristic to provide raw samples
        rawSample_status = 2;
        simple_ble_add_characteristic(1, 1, 1, 0, // read, write, notify, vlen
                1, (uint8_t*)&rawSample_status,
                &rawSample_service, &rawSample_char_status);
}

void ble_evt_write (ble_evt_t* p_ble_evt) {

    if (simple_ble_is_char_event(p_ble_evt, &rawSample_char_begin)) {
        // start or stop collection and transfer of raw samples as appropriate
        if (rawSample_state == RS_NONE && begin_rawSample) {
            // start raw sample collection
            rawSample_state = RS_START;
            rawSample_status = 0;
        } else if (rawSample_state != RS_NONE && !begin_rawSample) {
            rawSample_state = RS_QUIT;
            rawSample_status = 255;
        }

    } else if (simple_ble_is_char_event(p_ble_evt, &rawSample_char_status)) {
        // clear value on write
        rawSample_status = 0;

        // request next data from MSP430
        if (rawSample_state == RS_IDLE) {
            rawSample_state = RS_NEXT;
        }

    } else if (simple_ble_is_char_event(p_ble_evt, &config_voff_char) ||
               simple_ble_is_char_event(p_ble_evt, &config_ioff_char) ||
               simple_ble_is_char_event(p_ble_evt, &config_curoff_char) ||
               simple_ble_is_char_event(p_ble_evt, &config_pscale_char) ||
               simple_ble_is_char_event(p_ble_evt, &config_vscale_char) ||
               simple_ble_is_char_event(p_ble_evt, &config_whscale_char)) {
        // send updated value to MSP
        config_state = CONF_SET_VALUES;
    }
}


/**************************************************
 * Initialization
 **************************************************/

void timers_init (void) {
    uint32_t err_code;

    err_code = app_timer_create(&enable_uart_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)uart_rx_enable);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&start_eddystone_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)start_eddystone_adv);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&start_manufdata_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)start_manufdata_adv);
    APP_ERROR_CHECK(err_code);
}

void ble_error(uint32_t error_code) {
    // display error when developing on the squall platform
    //  Has no effect on production PowerBlades
    led_init(ERROR_LED);
    led_on(ERROR_LED);
}

int main(void) {
    // Initialization
    simple_ble_app = simple_ble_init(&ble_config);
    timers_init();
    conn_params_init();
    uart_init();
    init_adv_data();

    // Initialization complete
    start_manufdata_adv();
    uart_rx_enable();

    while (1) {
        power_manage();

        // state machine. Only send one message per second
        if (!already_transmitted) {
            transmit_message();
        }
    }
}

void transmit_message(void) {
    // select message to transmit at this interval
    //  message priority is based on ordering in this function

    if (nak_state == NAK_CHECKSUM) {
        // send NAK to MSP
        uint16_t length = 2+1+1; // length (x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (UART_NAK);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        nak_state = NAK_NONE;

    } else if (nak_state == NAK_RESEND) {
        // resend most recent message to MSP
        uart_send(tx_data, tx_data_len);
        nak_state = NAK_NONE;

    } else if (rawSample_state == RS_START) {
        // send start message to MSP
        uint16_t length = 2+1+1; // length (x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (START_SAMDATA);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        rawSample_state = RS_WAIT_START;

    } else if (rawSample_state == RS_NEXT) {
        // send next data message to MSP
        uint16_t length = 2+1+1; // length (x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (CONT_SAMDATA);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        rawSample_state = RS_WAIT_DATA;

    } else if (rawSample_state == RS_QUIT) {
        // send quit message to MSP
        uint16_t length = 2+1+1; // length (x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (DONE_SAMDATA);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        rawSample_state = RS_WAIT_QUIT;

    } else if (config_state == CONF_SET_VALUES) {
        // set configuration values
        uint16_t length = 2+1+sizeof(powerblade_config)+1; // length(x2), type, configuration struct, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (SET_CONF);
        memcpy(&(tx_buffer[3]), (uint8_t*)(&powerblade_config), sizeof(powerblade_config));
        tx_buffer[3+sizeof(powerblade_config)] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        config_state = CONF_NONE;

    } else if (startup_state == STARTUP_GET_CONF) {
        // get MSP configuration to display to user
        uint16_t length = 2+1+1; // length(x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (GET_CONF);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        startup_state = STARTUP_SET_SEQ;

    } else if (startup_state == STARTUP_SET_SEQ) {
        // update sequence number on startup for debugging
        // set sequence number. Used as a test message
        uint16_t length = 2+1+1+1; // length (x2), type, value, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (SET_SEQ);
        tx_buffer[3] = 150; // randomly selected sequence number
        tx_buffer[4] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        startup_state = STARTUP_NONE;
    }
}

void on_receive_message(uint8_t* buf, uint16_t len) {
    if (len > 0) {
        // switch on add data type
        uint8_t data_type = buf[0];
        switch (data_type) {
            case UART_NAK:
                nak_state = NAK_RESEND;
                break;
            case START_SAMDATA:
                // MSP acknowledges, wait for data
                if (rawSample_state != RS_QUIT) {
                    rawSample_state = RS_WAIT_DATA;
                }
                break;
            case CONT_SAMDATA:
                // update data
                memcpy(raw_sample_data, &(buf[1]), len-1);
                simple_ble_update_char_len(&rawSample_char_data, len-1);

                // notify user of new data
                rawSample_status = 1;
                simple_ble_notify_char(&rawSample_char_status);
                if (rawSample_state != RS_QUIT) {
                    rawSample_state = RS_IDLE;
                }
                break;
            case DONE_SAMDATA:
                // notify user samples are done
                begin_rawSample = false;
                rawSample_status = 2;
                simple_ble_notify_char(&rawSample_char_status);

                // reset data
                memset(raw_sample_data, 0x00, SAMDATA_MAX_LEN);
                simple_ble_update_char_len(&rawSample_char_data, 1);

                rawSample_state = RS_NONE;
                break;
            case GET_CONF:
                // updated configuration from the MSP
                if ((len-1) == sizeof(powerblade_config)) {
                    memcpy((uint8_t*)&powerblade_config, &(buf[1]), len-1);
                } else {
                    // data was the wrong size. Report error
                    status_code = STATUS_BAD_CONFIG_SIZE;
                    simple_ble_notify_char(&config_status_char);
                }

            default:
                // unhandled uart type. Don't handle it
                break;
        }
    } else {
        //if (rawSample_state != RS_NONE && rawSample_state != RS_IDLE) {
        //    raw_sample_data[0] = 0xFF;
        //}
        if (rawSample_state == RS_WAIT_START) {
            status_code = STATUS_NO_RS_START;
            simple_ble_notify_char(&config_status_char);
        } else if (rawSample_state == RS_WAIT_DATA) {
            status_code = STATUS_NO_RS_DATA;
            simple_ble_notify_char(&config_status_char);
        } else if (rawSample_state == RS_WAIT_QUIT) {
            status_code = STATUS_NO_RS_QUIT;
            simple_ble_notify_char(&config_status_char);
        }
        /*
        // no message received. Handle that
        if (rawSample_state == RS_WAIT_START) {
            // should have gotten an acknowledgement. Send again
            if (rawSample_state != RS_QUIT) {
                rawSample_state = RS_START;
            }
        } else if (rawSample_state == RS_WAIT_DATA) {
            // should have gotten data. Request again
            if (rawSample_state != RS_QUIT) {
                rawSample_state = RS_NEXT;
            }
        } else if (rawSample_state == RS_WAIT_QUIT) {
            // should have gotten a done message. Send again
            rawSample_state = RS_QUIT;
        }
        */
    }
}

