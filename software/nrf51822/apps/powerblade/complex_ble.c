/*
 * Functions extending simple BLE interface with PowerBlade needs
 */

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include "complex_ble.h"

void simple_ble_add_auth_characteristic (uint8_t read,
                                    uint8_t write,
                                    uint8_t notify,
                                    uint8_t vlen,
                                    uint16_t len,
                                    uint8_t* buf,
                                    simple_ble_service_t* service_handle,
                                    simple_ble_char_t* char_handle) {
    volatile uint32_t err_code;
    ble_gatts_char_md_t char_md;
    ble_gatts_attr_t    attr_char_value;
    ble_uuid_t          char_uuid;
    ble_gatts_attr_md_t attr_md;

    // set characteristic metadata
    memset(&char_md, 0, sizeof(char_md));
    char_md.char_props.read   = read;
    char_md.char_props.write  = write;
    char_md.char_props.notify = notify;
    char_md.p_char_user_desc  = NULL;
    char_md.p_char_pf         = NULL;
    char_md.p_user_desc_md    = NULL;
    char_md.p_cccd_md         = NULL;
    char_md.p_sccd_md         = NULL;

    // set characteristic uuid
    char_uuid.type = service_handle->uuid_handle.type;
    char_uuid.uuid = char_handle->uuid16;

    // set attribute metadata
    memset(&attr_md, 0, sizeof(attr_md));
    if (read) BLE_GAP_CONN_SEC_MODE_SET_OPEN(&attr_md.read_perm);
    if (write) BLE_GAP_CONN_SEC_MODE_SET_OPEN(&attr_md.write_perm);
    attr_md.vloc    = BLE_GATTS_VLOC_USER;
    attr_md.rd_auth = 1;
    attr_md.wr_auth = 0;
    attr_md.vlen    = vlen;

    // set attribute data
    memset(&attr_char_value, 0, sizeof(attr_char_value));
    attr_char_value.p_uuid    = &char_uuid;
    attr_char_value.p_attr_md = &attr_md;
    attr_char_value.init_len  = len;
    attr_char_value.init_offs = 0;
    attr_char_value.max_len   = len; // max len can be up to BLE_GATTS_FIX_ATTR_LEN_MAX (510)
    attr_char_value.p_value   = buf;

    err_code = sd_ble_gatts_characteristic_add((service_handle->service_handle),
            &char_md, &attr_char_value, &(char_handle->char_handle));
    APP_ERROR_CHECK(err_code);
}

bool simple_ble_is_read_auth_event (ble_evt_t* p_ble_evt, simple_ble_char_t* char_handle) {
    ble_gatts_evt_rw_authorize_request_t* p_auth_req = &(p_ble_evt->evt.gatts_evt.params.authorize_request);

    if (p_auth_req->type == BLE_GATTS_AUTHORIZE_TYPE_READ) {
        // read authorization
        uint16_t read_handle = p_auth_req->request.read.handle;
        if (read_handle == char_handle->char_handle.value_handle) {
            // read request for the matching characteristic
            return true;
        }
    }

    return false;
}

bool simple_ble_is_write_auth_event (ble_evt_t* p_ble_evt, simple_ble_char_t* char_handle) {
    ble_gatts_evt_rw_authorize_request_t* p_auth_req = &(p_ble_evt->evt.gatts_evt.params.authorize_request);

    if (p_auth_req->type == BLE_GATTS_AUTHORIZE_TYPE_WRITE) {
        // write authorization
        uint16_t write_handle = p_auth_req->request.write.handle;
        if (write_handle == char_handle->char_handle.value_handle) {
            // write request for the matching characteristic
            return true;
        }
    }

    return false;
}

/*
uint32_t simple_ble_grant_auth (ble_evt_t* p_ble_evt) {
    ble_gatts_evt_rw_authorize_request_t* p_auth_req = &(p_ble_evt->evt.gatts_evt.params.authorize_request);

    // initialize response
    ble_gatts_rw_authorize_reply_params_t auth_resp;
    memset(&auth_resp, 0, sizeof(auth_resp));
    auth_resp.params.read.gatt_status = BLE_GATT_STATUS_SUCCESS;

    // add proper response type
    if (p_auth_req->type == BLE_GATTS_AUTHORIZE_TYPE_READ) {
        // read request
        auth_resp.type = BLE_GATTS_AUTHORIZE_TYPE_READ;
    } else if (p_auth_req->type == BLE_GATTS_AUTHORIZE_TYPE_WRITE) {
        // write request
        auth_resp.type = BLE_GATTS_AUTHORIZE_TYPE_WRITE;
    } else {
        // type is invalid, why are we here?
        auth_resp.type = BLE_GATTS_AUTHORIZE_TYPE_INVALID;
    }

    return sd_ble_gatts_rw_authorize_reply(app.conn_handle, &auth_resp);
}
*/

