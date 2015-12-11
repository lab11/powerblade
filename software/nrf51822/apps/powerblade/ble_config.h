#ifndef __BLE_CONFIG_H
#define __BLE_CONFIG_H

#define APP_COMPANY_IDENTIFIER			0x4908

#include "simple_ble.h"
#include "powerblade.h"

// Intervals for advertising and connections
static const simple_ble_config_t ble_config = {
    .platform_id       = PLATFORM_ID_BYTE,  // used as 4th octet in device BLE address
    .device_id         = DEVICE_ID_DEFAULT, // 5th and 6th octet in device BLE address
    .adv_name          = DEVICE_NAME,       // used in advertisements if there is room
    .adv_interval      = MSEC_TO_UNITS(200, UNIT_0_625_MS),
    .min_conn_interval = 6,                 // units 1.250 ms = 7.5
    .max_conn_interval = MSEC_TO_UNITS(20, UNIT_1_25_MS),
};

typedef struct ble_app_s {
    simple_ble_app_t*           simple_ble_app;

    // service for powerblade calibration
    uint16_t                    calibrate_service_handle;

        // characteristic to start calibration mode
        ble_gatts_char_handles_t    calibrate_char_begin_handle;
        bool                        begin_calibration;

        // characteristic to specify ground truth wattage for calibration
        ble_gatts_char_handles_t    calibrate_char_watts_handle;
        int16_t                     ground_truth_watts;

        // characteristic to inform user to move to next calibration wattage
        ble_gatts_char_handles_t    calibrate_char_next_handle;
        bool                        next_wattage;

        // characteristic to inform user calibration is complete
        ble_gatts_char_handles_t    calibrate_char_done_handle;
        bool                        done_calibrating;
} ble_app_t;

#endif

