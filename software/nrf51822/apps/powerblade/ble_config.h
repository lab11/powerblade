#ifndef __BLE_CONFIG_H
#define __BLE_CONFIG_H

#define APP_COMPANY_IDENTIFIER			0x4908

#include "simple_ble.h"
#include "uart_types.h"
#include "powerblade.h"

// Intervals for advertising and connections
static const simple_ble_config_t ble_config = {
    .platform_id       = PLATFORM_ID_BYTE,  // used as 4th octet in device BLE address
    .device_id         = DEVICE_ID_DEFAULT, // 5th and 6th octet in device BLE address
    .adv_name          = DEVICE_NAME,       // used in advertisements if there is room
    .adv_interval      = MSEC_TO_UNITS(200, UNIT_0_625_MS),
    .min_conn_interval = MSEC_TO_UNITS(50, UNIT_1_25_MS),
    .max_conn_interval = MSEC_TO_UNITS(100, UNIT_1_25_MS),
};

typedef struct ble_app_s {
    simple_ble_app_t* simple_ble_app;

    // service for powerblade calibration
    uint16_t calibrate_service_handle;

        // characteristic to start calibration mode
        ble_gatts_char_handles_t calibrate_char_begin_handle;
        bool                     begin_calibration;

        // characteristic to specify ground truth wattage for calibration
        ble_gatts_char_handles_t calibrate_char_watts_handle;
        int16_t                  ground_truth_watts;

        // characteristic to inform user to move to next calibration wattage
        ble_gatts_char_handles_t calibrate_char_next_handle;
        bool                     next_wattage;

        // characteristic to inform user calibration is complete
        ble_gatts_char_handles_t calibrate_char_done_handle;
        bool                     done_calibrating;

    // service for sample data collection
    uint16_t rawSample_service_handle;

        // characteristic to start raw sample collection
        ble_gatts_char_handles_t rawSample_char_begin_handle;
        bool                     begin_rawSample;

        // characteristic to provide raw samples to users
        ble_gatts_char_handles_t rawSample_char_data_handle;
        uint8_t                  raw_sample_data[SAMDATA_MAX_LEN];

        // characteristic to indicate new data is available
        ble_gatts_char_handles_t rawSample_char_status_handle;
        uint8_t                  rawSample_status;

} ble_app_t;

#endif

