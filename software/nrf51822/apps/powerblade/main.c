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
#include "waveforms.h"
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
void process_rx_packet(uint16_t packet_len, bool overrun);
void process_additional_data(uint8_t* buf, uint16_t len);
void uart_tx_handler(void);
void uart_send(uint8_t* data, uint16_t len);
void uart_start_receive(void);

void services_init(void);
void ble_evt_write (ble_evt_t* p_ble_evt);

void transmit_message(void);
void receive_bytes(void);
void process_rx_packet(uint16_t packet_len, bool overrun);
void on_receive_message(uint8_t* buf, uint16_t len, uint8_t* adv_data, uint8_t adv_len);

void timers_init(void);
int main(void);


/**************************************************
 * Define and Globals
 **************************************************/

// override default configuration
const int SLAVE_LATENCY = 4;
const int FIRST_CONN_PARAMS_UPDATE_DELAY = APP_TIMER_TICKS(100, APP_TIMER_PRESCALER);

// simple_ble configuration for advertising and connections
static const simple_ble_config_t ble_config = {
    .platform_id       = PLATFORM_ID_BYTE,  // used as 4th octet in device BLE address
    .device_id         = DEVICE_ID_DEFAULT, // 5th and 6th octet in device BLE address
    .adv_name          = DEVICE_NAME,       // used in advertisements if there is room
    .adv_interval      = MSEC_TO_UNITS(200, UNIT_0_625_MS),
    .min_conn_interval = MSEC_TO_UNITS(20, UNIT_1_25_MS),
    .max_conn_interval = MSEC_TO_UNITS(50, UNIT_1_25_MS),
};
static simple_ble_app_t* simple_ble_app;

// timer configuration
APP_TIMER_DEF(enable_uart_timer);
APP_TIMER_DEF(start_eddystone_timer);
APP_TIMER_DEF(start_manufdata_timer);
APP_TIMER_DEF(restart_advs_timer);
#define EDDYSTONE_ADV_DURATION      APP_TIMER_TICKS(200, APP_TIMER_PRESCALER)
#define MANUFDATA_ADV_DURATION      APP_TIMER_TICKS(800, APP_TIMER_PRESCALER)
// end of uart message to start of next with guard time
#define UART_SLEEP_DURATION         APP_TIMER_TICKS(960, APP_TIMER_PRESCALER)
// start of uart guard time to start of next guard time, determined empirically
#define UART_SKIP_DURATION          APP_TIMER_TICKS(999, APP_TIMER_PRESCALER)
// skip two cycles during a connection start since those take longer
#define CONNECTION_SKIP_DURATION    2*UART_SKIP_DURATION

// advertisement data
// for https://cdn.rawgit.com/lab11/powerblade/030626a2aa748c0b0d7c3a69d9fd005d6d769667/software/summon/index.html
#define PHYSWEB_URL "j2x.us/6EKY8W"
#define UMICH_COMPANY_IDENTIFIER    0x02E0
#define POWERBLADE_SERVICE_IDENTIFIER 0x11
static uint8_t powerblade_adv_data[ADV_DATA_MAX_LEN];
static uint8_t powerblade_adv_data_len = 0;

// service for device configuration
static simple_ble_service_t config_service = {
    .uuid128 = {{0x99, 0xF9, 0xAC, 0xE5, 0x57, 0xB9, 0x43, 0xEC,
                 0x88, 0xF8, 0x88, 0xB9, 0x4D, 0xA1, 0x80, 0x50}}};

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

// service for internal calibration
static simple_ble_service_t calibration_service = {
    .uuid128 = {{0x49, 0x4B, 0x30, 0x70, 0xAA, 0xD5, 0x4E, 0x84,
                 0x9E, 0xD9, 0x61, 0x94, 0xED, 0x0B, 0xC4, 0x57}}};

    // characteristic to hold wattage setpoint
    static simple_ble_char_t calibration_wattage_char = {.uuid16 = 0xED0C};
    static uint16_t calibration_wattage;

    // characteristic to hold voltage setpoint
    static simple_ble_char_t calibration_voltage_char = {.uuid16 = 0xED0D};
    static uint16_t calibration_voltage;

    // characteristic to control internal calibration
    static simple_ble_char_t calibration_control_char = {.uuid16 = 0xED0E};
    static uint8_t calibration_control;

// service for sample data collection
static simple_ble_service_t rawSample_service = {
    .uuid128 = {{0x31, 0x15, 0xD4, 0x39, 0x2A, 0x88, 0x4E, 0x1C,
                 0x8C, 0xCC, 0xF8, 0x7C, 0x01, 0xAF, 0xAD, 0xCE}}};

    // characteristic to start raw sample collection
    static simple_ble_char_t rawSample_char_begin = {.uuid16 = 0x01B0};
    static bool begin_rawSample;

    // characteristic to provide raw samples to users
    static simple_ble_char_t rawSample_char_data = {.uuid16 = 0x01B1};
    static uint8_t raw_sample_data[SAMDATA_MAX_LEN];

    // characteristic to indicate new data is available
    static simple_ble_char_t rawSample_char_status = {.uuid16 = 0x01B2};
    static uint8_t rawSample_status;

// service for continuous waveform collection
static simple_ble_service_t continuous_waveform_service = {
    .uuid128 = {{0x33, 0x3B, 0x60, 0x34, 0x32, 0xA8, 0x1C, 0x93,
                 0x9B, 0x40, 0xDA, 0x6C, 0xE3, 0xF1, 0x71, 0x61}}};

    // characteristic to signal waveform data status
    static simple_ble_char_t continuous_waveform_char_status = {.uuid16 = 0xE3F2};
    static uint8_t continuous_waveform_status;

    // characteristic to hold a waveform to be read
    static simple_ble_char_t continuous_waveform_char_data = {.uuid16 = 0xE3F3};
    static waveform_t continuous_waveform_values;
    static waveform_t* continuous_waveform_data = &continuous_waveform_values;

// service for unique waveform collection
static simple_ble_service_t unique_waveform_service = {
    .uuid128 = {{0xDD, 0x26, 0x13, 0x39, 0xB5, 0x41, 0x15, 0x90,
                 0xC3, 0x42, 0xB2, 0xDA, 0x9B, 0x3D, 0x88, 0x4E}}};

    // characteristic to signal waveform data status
    static simple_ble_char_t unique_waveform_char_status = {.uuid16 = 0x9B3E};
    static uint8_t unique_waveform_status;

    // characteristic to hold an advertisement payload and corresponding waveform to be read
    static simple_ble_char_t unique_waveform_char_data = {.uuid16 = 0x9B3F};
    static waveform_t unique_waveform_values;
    static waveform_t* unique_waveform_data = &unique_waveform_values;


// receiving data items
static bool receiving_bytes = false;
static uint16_t received_len = 0;
static uint16_t rx_index = 0;

// uart buffers
// max length is: total length + adv length + adv data + add type + add data + checksum
#define RX_DATA_MAX_LEN 2+1+ADV_DATA_MAX_LEN+1+SAMDATA_MAX_LEN+1
static uint8_t rx_data[RX_DATA_MAX_LEN];
static uint8_t* tx_data;
static uint16_t tx_data_len = 0;
static uint8_t tx_buffer[4+sizeof(powerblade_config)];
// when receiving long packets, briefly pause advertisements. I've decided that
//  400 bytes is "long" essentially arbitarily
#define LONG_PACKET_THRESHOLD 400

// states for handling transmissions to the MSP
static bool already_transmitted = false;
static NakState_t nak_state = NAK_NONE;
static CalibrationState_t calibration_state = CALIB_NONE;
static RawSampleState_t rawSample_state = RS_NONE;
static ConfigurationState_t config_state = CONF_NONE;
static StartupState_t startup_state = STARTUP_NOP;
static StatusCode_t status_code = STATUS_NONE;
static bool skip_uart_cycle = false;


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
    powerblade_adv_data[12] = 0x02; // Real Power

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

void restart_advertisements (void) {
    // if our timers were paused, restart them now. There probably isn't any
    //  new data, so starting eddystone first seems like the right call here
    start_eddystone_adv();
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
    led_toggle(ERROR_LED);
    // move uart data to buffer
    //Note: be very careful in this function. It's got a higher priority than
    // most of the softdevice and can really screw things up if it takes too
    // long to complete
    nrf_uart_event_clear(NRF_UART0, NRF_UART_EVENT_RXDRDY);
    rx_data[rx_index] = nrf_uart_rxd_get(NRF_UART0);
    rx_index++;
    led_toggle(ERROR_LED);
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

void uart_start_receive (void) {
    led_toggle(ERROR_LED);
    if (!skip_uart_cycle) {
        // don't allow transmissions while waiting for a packet
        already_transmitted = true;

        // reset state. If we were still looking for an old packet, it's time
        //  to give up and start over
        received_len = 0;
        rx_index = 0;

        // we are ready to receive, go for it
        receiving_bytes = true;
        uart_rx_enable();
    } else {
        // skip this reception cycle to conserve power while doing heavy
        //  lifting in BLE-land
        app_timer_start(enable_uart_timer, UART_SKIP_DURATION, NULL);
        // only skip a single cycle
        skip_uart_cycle = false;
        // if we haven't already transmitted, don't start now
        //  if we have, we won't move on to the next state for a cycle since
        //  already_transmitted will stay true
        already_transmitted = true;
    }
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


    // Add internal calibration service
    simple_ble_add_service(&calibration_service);

        // Add the characteristic to set calibration load wattage
        calibration_wattage = 0;
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                2, (uint8_t*)&calibration_wattage,
                &calibration_service, &calibration_wattage_char);

        // Add the characteristic to set calibration load voltage
        calibration_voltage = 0x04B0; // 1200 deci-volts
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                2, (uint8_t*)&calibration_voltage,
                &calibration_service, &calibration_voltage_char);

        // Add the characteristic to control and indicate status
        calibration_control = 0;
        simple_ble_add_characteristic(1, 1, 1, 0, // read, write, notify, vlen
                1, (uint8_t*)&calibration_control,
                &calibration_service, &calibration_control_char);

    // Add raw sample download service
    simple_ble_add_service(&rawSample_service);

        // Add the characteristic to signal grab sample data
        begin_rawSample = false;
        simple_ble_add_characteristic(1, 1, 0, 0, // read, write, notify, vlen
                1, (uint8_t*)&begin_rawSample,
                &rawSample_service, &rawSample_char_begin);

        // Add the characteristic to provide raw samples
        //  This characteristic requires read authorizations. This gives us the
        //  opportunity to disable the UART transmissions while before a read
        //  of it starts
        memset(raw_sample_data, 0x00, SAMDATA_MAX_LEN);
        simple_ble_add_auth_characteristic(1, 0, 0, 1, // read, write, notify, vlen
                true, false, // read auth, write auth
                SAMDATA_MAX_LEN, (uint8_t*)raw_sample_data,
                &rawSample_service, &rawSample_char_data);
        // must initialize to maximum valid length. Now reset down to 1
        simple_ble_update_char_len(&rawSample_char_data, 1);

        // Add the characteristic to provide raw samples
        rawSample_status = 2;
        simple_ble_add_characteristic(1, 1, 1, 0, // read, write, notify, vlen
                1, (uint8_t*)&rawSample_status,
                &rawSample_service, &rawSample_char_status);

    // Add continuous waveform collection service
    simple_ble_add_service(&continuous_waveform_service);

        // Add the characteristic to signify if data is valid
        continuous_waveform_status = false;
        simple_ble_add_characteristic(1, 1, 1, 0, // read, write, notify, vlen
                1, (uint8_t*)&continuous_waveform_status,
                &continuous_waveform_service, &continuous_waveform_char_status);

        // Add the characteristic to provide waveforms
        memset(continuous_waveform_data, 0x00, sizeof(waveform_t));
        simple_ble_add_auth_characteristic(1, 0, 0, 0, // read, write, notify, vlen
                true, false, // read auth, write auth
                sizeof(waveform_t), (uint8_t*)continuous_waveform_data,
                &continuous_waveform_service, &continuous_waveform_char_data);

    // Add unique waveform collection service
    simple_ble_add_service(&unique_waveform_service);

        // Add the characteristic to signify if data is valid
        unique_waveform_status = false;
        simple_ble_add_characteristic(1, 1, 1, 0, // read, write, notify, vlen
                1, (uint8_t*)&unique_waveform_status,
                &unique_waveform_service, &unique_waveform_char_status);

        // Add the characteristic to provide waveforms
        memset(unique_waveform_data, 0x00, sizeof(waveform_t));
        simple_ble_add_auth_characteristic(1, 0, 0, 0, // read, write, notify, vlen
                true, false, // read auth, write auth
                sizeof(waveform_t), (uint8_t*)unique_waveform_data,
                &unique_waveform_service, &unique_waveform_char_data);
}

void ble_evt_connected (ble_evt_t* p_ble_evt) {
    // a connection just started, skip the next uart cycle to save power
    skip_uart_cycle = true;

    // stop any running advertisements and don't restart for a single UART cycle
    advertising_stop();
    app_timer_stop(start_eddystone_timer);
    app_timer_stop(start_manufdata_timer);
    app_timer_start(restart_advs_timer, CONNECTION_SKIP_DURATION, NULL);
}

void ble_evt_write (ble_evt_t* p_ble_evt) {

    if (simple_ble_is_char_event(p_ble_evt, &calibration_control_char)) {
        // start or stop calibration depending on current state
        if (calibration_state == CALIB_NONE) {
            // start internal calibration
            calibration_state = CALIB_START;
        } else {
            // stop internal calibration
            calibration_state = CALIB_STOP;
        }

    } else if (simple_ble_is_char_event(p_ble_evt, &calibration_wattage_char) ||
            simple_ble_is_char_event(p_ble_evt, &calibration_voltage_char)) {
        // user just changed calibration parameters. Stop calibration if in progress
        if (calibration_state != CALIB_NONE) {
            // stop internal calibration
            calibration_state = CALIB_STOP;
        }

    } else if (simple_ble_is_char_event(p_ble_evt, &rawSample_char_begin)) {
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

    } else if (simple_ble_is_char_event(p_ble_evt, &continuous_waveform_char_status)) {
        // clear value on write
        continuous_waveform_status = 0;

    } else if (simple_ble_is_char_event(p_ble_evt, &unique_waveform_char_status)) {
        // clear value on write
        unique_waveform_status = 0;

        // get the next waveform to transfer, if any
        if (get_next_waveform(unique_waveform_data)) {
            // notify that data is available
            unique_waveform_status = 1;
        }
        simple_ble_notify_char(&unique_waveform_char_status);

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

void ble_evt_rw_auth (ble_evt_t* p_ble_evt) {
    if (simple_ble_is_read_auth_event(p_ble_evt, &rawSample_char_data) ||
            simple_ble_is_read_auth_event(p_ble_evt, &continuous_waveform_char_data) ||
            simple_ble_is_read_auth_event(p_ble_evt, &unique_waveform_char_data)) {

        // read request for a data characteristic, disable uart for a cycle and
        //  authorize the read
        skip_uart_cycle = true;
        uint32_t err_code = simple_ble_grant_auth(p_ble_evt);
        APP_ERROR_CHECK(err_code);
    }
}


/**************************************************
 * Initialization
 **************************************************/

void timers_init (void) {
    uint32_t err_code;

    err_code = app_timer_create(&enable_uart_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)uart_start_receive);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&start_eddystone_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)start_eddystone_adv);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&start_manufdata_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)start_manufdata_adv);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&restart_advs_timer, APP_TIMER_MODE_SINGLE_SHOT, (app_timer_timeout_handler_t)restart_advertisements);
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

    led_init(ERROR_LED);
    led_on(ERROR_LED);

    // Initialization complete
    start_manufdata_adv();
    receiving_bytes = true;
    uart_rx_enable();

    while (1) {
        power_manage();

        // handle input bytes
        if (receiving_bytes) {
            receive_bytes();
        }

        // state machine. Only send one message per second
        if (!already_transmitted) {
            transmit_message();
        }
    }
}

/**************************************************
 * Message Transmit State Machine
 **************************************************/

void transmit_message(void) {
    // select message to transmit at this interval
    //  message priority is based on ordering in this function

    if (startup_state == STARTUP_NOP) {
        // skip this first cycle
        already_transmitted = true;
        startup_state = STARTUP_GET_CONFIG;

    } else if (nak_state == NAK_CHECKSUM) {
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

    } else if (calibration_state == CALIB_START) {
        // send start message to MSP
        uint16_t length = 2+1+2+2+1; // length (x2), type, wattage (x2), voltage (x2), checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (START_LOCALC);
        tx_buffer[3] = (calibration_wattage >> 8);
        tx_buffer[4] = (calibration_wattage & 0xFF);
        tx_buffer[5] = (calibration_voltage >> 8);
        tx_buffer[6] = (calibration_voltage & 0xFF);
        tx_buffer[7] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        rawSample_state = CALIB_WAIT_START;

    } else if (calibration_state == CALIB_CONTINUE) {
        // check on the state of the MSP
        uint16_t length = 2+1+1; // length (x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (CONT_LOCALC);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        rawSample_state = CALIB_WAIT_CONTINUE;

    } else if (calibration_state == CALIB_GET_CONFIG) {
        // request new configuration from MSP
        uint16_t length = 2+1+1; // length (x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (GET_CONF);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        rawSample_state = CALIB_WAIT_GET_CONFIG;

    } else if (calibration_state == CALIB_STOP) {
        // send stop message to MSP
        uint16_t length = 2+1+1; // length (x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (DONE_LOCALC);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        rawSample_state = CALIB_WAIT_STOP;

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

    } else if (startup_state == STARTUP_GET_CONFIG) {
        // get MSP configuration to display to user
        uint16_t length = 2+1+1; // length(x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (GET_CONF);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        startup_state = STARTUP_GET_VERSION;

    } else if (startup_state == STARTUP_GET_VERSION) {
        // get MSP software version to display to user
        uint16_t length = 2+1+1; // length(x2), type, checksum
        tx_buffer[0] = (length >> 8);
        tx_buffer[1] = (length & 0xFF);
        tx_buffer[2] = (GET_VER);
        tx_buffer[3] = additive_checksum(tx_buffer, length-1);
        uart_send(tx_buffer, length);
        startup_state = STARTUP_NONE;
    }
}

/**************************************************
 * Message Receive State Machine
 **************************************************/

void receive_bytes(void) {
    // check if we have received the entire packet
    //  This can't occur until we have length, adv length, and checksum
    if (rx_index >= 4) {

        // parse out expected packet length
        if (received_len == 0) {
            received_len = (rx_data[0] << 8 | rx_data[1]);

            // we are receiving a packet, restart the sleep timer
            app_timer_start(enable_uart_timer, UART_SLEEP_DURATION, NULL);

            // if we are receiving a long packet, pause advertisements until it's done
            if (received_len > LONG_PACKET_THRESHOLD) {
                advertising_stop();
                app_timer_stop(start_eddystone_timer);
                app_timer_stop(start_manufdata_timer);
                // no need to set a timer to restart them, process_rx_packet
                //  will do so. Unless the CRC is bad, in which case the next
                //  uart transmission will
            }
        }

        if (nrf_uart_errorsrc_get_and_clear(NRF_UART0) == NRF_UART_ERROR_OVERRUN_MASK) {
            // overrun. This data is invalid

            if (received_len == 0) {
                // if the timer wasn't already restarted, do so now
                app_timer_start(enable_uart_timer, UART_SLEEP_DURATION, NULL);
            }

            // if there was an overrun, we'll fail the packet immediately
            receiving_bytes = false;
            process_rx_packet(rx_index, true);
            received_len = 0;
            rx_index = 0;
        } else if (rx_index >= received_len || rx_index >= RX_DATA_MAX_LEN) {
            // process packet if we have all of it
            //NOTE: we aren't doing any kind of check here to ensure that we
            //  aren't waiting forever for an eronously large packet. That'
            //  okay though, because it will reset from zero at next timer
            //  start if it goes longer than the bytes that were actually sent
            //  in the packet. Also, since the current draw when UART is on is
            //  unsustainable, the nRF will just reboot if this occurs and get
            //  back to a good state in any case.
            receiving_bytes = false;
            process_rx_packet(received_len, false);
            received_len = 0;
            rx_index = 0;
        }
    }
}

void process_rx_packet(uint16_t packet_len, bool overrun) {
    static bool first_packet = true;
    static uint32_t first_seqno = 0;

    // turn off UART until next window
    uart_rx_disable();

    // a new window for transmission to the MSP430 is available
    already_transmitted = false;

    // check CRC
    if (!overrun && additive_checksum(rx_data, packet_len-1) == rx_data[packet_len-1]) {

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

            // determine if powerblade restarted
            uint32_t curr_seqno = parse_sequence_number(powerblade_adv_data, powerblade_adv_data_len);
            if (first_packet) {
                first_packet = false;
                first_seqno = curr_seqno;
            }
            flag_nrf_restart(((curr_seqno-first_seqno) < 60), powerblade_adv_data, powerblade_adv_data_len);

            // include available waveform
            flag_waveform_available((unique_waveform_status == 1), powerblade_adv_data, powerblade_adv_data_len);

            // actually copy over advertisement data and begin advertisement
            start_manufdata_adv();

            // handle additional UART data, if any
            uint8_t* additional_data = &(rx_data[3+adv_len]);
            uint16_t additional_data_length = packet_len - (4 + adv_len);
            on_receive_message(additional_data, additional_data_length, &(rx_data[3]), adv_len);
        }
    } else {
        // need to send a nak
        nak_state = NAK_CHECKSUM;
        status_code = STATUS_BAD_CHECKSUM;
        simple_ble_notify_char(&config_status_char);
    }
}

void on_receive_message(uint8_t* buf, uint16_t len, uint8_t* adv_data, uint8_t adv_len) {
    if (len > 0) {
        // switch on add data type
        uint8_t data_type = buf[0];
        static waveform_t new_waveform;
        switch (data_type) {
            case WAVEFORM:
                new_waveform.adv_len = adv_len;
                memcpy(new_waveform.adv_payload, adv_data, adv_len);
                new_waveform.waveform_len = len-1;
                memcpy(new_waveform.waveform_payload, &(buf[1]), len-1);

                // save waveform to continuous waveform service if space is available
                if (continuous_waveform_status == 0) {
                    if ((len-1) == WAVEFORM_MAX_LEN) {
                        memcpy(continuous_waveform_data, &new_waveform, sizeof(waveform_t));
                    }

                    // notify that data is available
                    continuous_waveform_status = 1;
                    simple_ble_notify_char(&continuous_waveform_char_status);
                }

                // check if unique waveform service should save data and do so
                check_and_store_new_waveform(&new_waveform);

                // update unique waveform service data if waveform available
                if (unique_waveform_status == 0 && get_next_waveform(unique_waveform_data)) {
                    // notify that data is available
                    unique_waveform_status = 1;
                    simple_ble_notify_char(&unique_waveform_char_status);
                }
                break;

            case UART_NAK:
                status_code = STATUS_GOT_NAK;
                simple_ble_notify_char(&config_status_char);
                nak_state = NAK_RESEND;
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

                // check if we are waiting on configuration to complete calibration
                if (calibration_state != CALIB_NONE) {
                    calibration_state = CALIB_NONE;
                }
                break;

            case GET_VER:
                // updated configuration from the MSP
                //TODO: copy over version number into some characteristic
                break;

            case START_LOCALC:
                // write status to characteristic
                calibration_control = 1;
                simple_ble_notify_char(&calibration_control_char);

                // MSP has begun interal calibration
                if (calibration_state != CALIB_STOP) {
                    calibration_state = CALIB_CONTINUE;
                }
                break;

            case CONT_LOCALC:
                // MSP is still running internal calibration
                if (calibration_state != CALIB_STOP) {
                    calibration_state = CALIB_CONTINUE;
                }
                break;

            case DONE_LOCALC:
                // write status to characteristic
                calibration_control = 2;
                simple_ble_notify_char(&calibration_control_char);

                // MSP has stopped internal calibration
                calibration_state = CALIB_GET_CONFIG;
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

            default:
                // unhandled uart type. Don't handle it
                break;
        }
    } else {
        // expected a message but didn't receive one. Signal error status over
        //  status characteristic and try to stop whatever state we're in
        if (calibration_state == CALIB_WAIT_START) {
            status_code = STATUS_NO_CALIB_START;
            simple_ble_notify_char(&config_status_char);
            // return to default state
            calibration_state = CALIB_STOP;
        } else if (calibration_state == CALIB_WAIT_CONTINUE) {
            status_code = STATUS_NO_CALIB_CONTINUE;
            simple_ble_notify_char(&config_status_char);
            // return to default state
            calibration_state = CALIB_STOP;
        } else if (calibration_state == CALIB_WAIT_GET_CONFIG) {
            status_code = STATUS_NO_CALIB_GET_CONFIG;
            simple_ble_notify_char(&config_status_char);
            // return to default state
            calibration_state = CALIB_STOP;
        } else if (calibration_state == CALIB_WAIT_STOP) {
            status_code = STATUS_NO_CALIB_STOP;
            simple_ble_notify_char(&config_status_char);
            // return to default state
            calibration_state = CALIB_NONE;
        } else if (rawSample_state == RS_WAIT_START) {
            status_code = STATUS_NO_RS_START;
            simple_ble_notify_char(&config_status_char);
            // return to default state
            rawSample_state = RS_QUIT;
        } else if (rawSample_state == RS_WAIT_DATA) {
            status_code = STATUS_NO_RS_DATA;
            simple_ble_notify_char(&config_status_char);
            // return to default state
            rawSample_state = RS_QUIT;
        } else if (rawSample_state == RS_WAIT_QUIT) {
            status_code = STATUS_NO_RS_QUIT;
            simple_ble_notify_char(&config_status_char);
            // return to default state
            rawSample_state = RS_NONE;
        }
    }
}

