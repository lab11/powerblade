#ifndef __BLE_CONFIG_H
#define __BLE_CONFIG_H

#define APP_COMPANY_IDENTIFIER			0x4908

#include "simple_ble.h"

typedef struct ble_app_s {
    simple_ble_app_t*   simple_ble_app;
    uint16_t            service_handle;
} ble_app_t;

#endif

