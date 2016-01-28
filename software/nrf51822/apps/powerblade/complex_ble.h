#ifndef __COMPLEX_BLE_H
#define __COMPLEX_BLE_H

#include <stdint.h>
#include "simple_ble.h"

void simple_ble_add_auth_characteristic (uint8_t read,
                                        uint8_t write,
                                        uint8_t notify,
                                        uint8_t vlen,
                                        uint16_t len,
                                        uint8_t* buf,
                                        simple_ble_service_t* service_handle,
                                        simple_ble_char_t* char_handle);

bool simple_ble_is_read_auth_event (ble_evt_t* p_ble_evt, simple_ble_char_t* char_handle);
bool simple_ble_is_write_auth_event (ble_evt_t* p_ble_evt, simple_ble_char_t* char_handle);
uint32_t simple_ble_grant_auth (ble_evt_t* p_ble_evt);

#endif //__COMPLEX_BLE_H
