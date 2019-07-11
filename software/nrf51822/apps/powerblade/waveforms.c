/*
 * Unique waveform collection code
 */

// Standard libraries
#include <stdint.h>
#include <stdbool.h>

// Local libraries
#include "powerblade.h"
#include "waveforms.h"


/**************************************************
 * Advertisement Parsing
 **************************************************/

// parse sequence number from advertisement data
uint32_t parse_sequence_number(uint8_t* adv_data, uint16_t adv_len) {
    if (adv_len > 5) {
        return (((uint32_t)adv_data[2]) << 24) | (((uint32_t)adv_data[3]) << 16) |
               (((uint32_t)adv_data[4]) <<  8) | ((uint32_t)adv_data[5]);
    }

    // not in packet? just return zero
    return 0;
}

// parse real power from advertisement data (uncalibrated)
uint16_t parse_real_power(uint8_t* adv_data, uint16_t adv_len) {
    if (adv_len > 12) {
        return (((uint16_t)adv_data[11]) << 8) | ((uint16_t)adv_data[12]);
    }

    // not in packet? just return zero
    return 0;
}

// parse apparent power from advertisement data (uncalibrated)
uint16_t parse_apparent_power(uint8_t* adv_data, uint16_t adv_len) {
    if (adv_len > 14) {
        return (((uint16_t)adv_data[13]) << 8) | ((uint16_t)adv_data[14]);
    }

    // not in packet? just return zero
    return 0;
}

// parse flags from advertisement data
uint8_t parse_flags(uint8_t* adv_data, uint16_t adv_len) {
    if (adv_len > 19) {
        return adv_data[19];
    }

    // not in packet? just return zero
    return 0;
}

// modify flags to show whether the nRF has recently restarted
void flag_nrf_restart(bool restarted, uint8_t* adv_data, uint16_t adv_len) {
    // only write if it fits in the data buffer
    if (adv_len > 19) {
        if (restarted) {
            // set flag
            adv_data[19] |= 0x20;
        } else {
            // clear flag
            adv_data[19] &= ~(0x20);
        }
    }
}

// modify flags to show whether a waveform is available for download
void flag_waveform_available(bool available, uint8_t* adv_data, uint16_t adv_len) {
    // only write if it fits in the data buffer
    if (adv_len > 19) {
        if (available) {
            // set flag
            adv_data[19] |= 0x10;
        } else {
            // clear flag
            adv_data[19] &= ~(0x10);
        }
    }
}


/**************************************************
 * Waveform State Machine
 **************************************************/


unique_circle_buf unique_waveforms = {0};

void reset_waveforms(unique_circle_buf * buf) {
    buf->head = buf->tail = 0;
    buf->full = false;
}

static bool unique_waveforms_empty(const unique_circle_buf * buf) {
    return (buf->head == buf->tail && !buf->full);
}

static void advance_pointer(unique_circle_buf * buf)
{
    if(buf->full)
    {
        buf->tail = (buf->tail + 1) % UNIQUE_WAVEFORM_MAX;
    }

    buf->head = (buf->head + 1) % UNIQUE_WAVEFORM_MAX;
    buf->full = (buf->head == buf->tail);
}

static void retreat_pointer(unique_circle_buf * buf)
{
    buf->full = false;
    buf->tail = (buf->tail + 1) % UNIQUE_WAVEFORM_MAX;
}

// find the next waveform to be transferred. Also marks the existing waveform
// as collected (if one is in `data`). Returns false if there is none.
bool get_next_waveform(unique_waveform_t* data) {
    if (unique_waveforms_empty(&unique_waveforms)) {
        return false;
    }
    else {
        size_t tail = unique_waveforms.tail;
        memcpy(data, unique_waveforms.data[tail].waveform_payload, unique_waveforms.data[tail].waveform_len);
        retreat_pointer(&unique_waveforms);
        return true;
    }
}

// determine if this waveform should be saved and do so.
void check_and_store_new_waveform(uint8_t* waveform_data, uint16_t waveform_len, uint8_t* adv_data, uint16_t adv_len) {
    bool store = false;
    // if full, ignore it
    if (unique_waveforms.full) return;
    // if empty, store it
    if (unique_waveforms_empty(&unique_waveforms)) {
        store = true;
    // else search and compare other existing waveforms
    // check based on sequence number, real and apparent power, and maybe some similarity metric
    } else {
        size_t i = unique_waveforms.tail;
        store = true;
        while (i != unique_waveforms.head) {
            unique_waveform_t * compare_waveform = &unique_waveforms.data[i];
            uint16_t real_power = parse_real_power(adv_data, adv_len);
            uint16_t apparent_power = parse_real_power(adv_data, adv_len);
            uint16_t compare_real_power = parse_real_power(compare_waveform->adv_payload, compare_waveform->adv_len);
            uint16_t compare_app_power = parse_apparent_power(compare_waveform->adv_payload, compare_waveform->adv_len);
            // approximate 10%
            // is current waveform outside +/- 10% of other waveform?
            uint16_t real_portion = compare_real_power >> 3;
            uint16_t app_portion = compare_app_power >> 3;
            if (real_power > compare_real_power + real_portion ||
                   real_power < compare_real_power - real_portion ||
                   apparent_power > compare_app_power + app_portion ||
                   apparent_power < compare_app_power - app_portion)
            {
                // great, this waveform's power is different!
                // time to look at the next one
                i = (i + 1) % UNIQUE_WAVEFORM_MAX;
                continue;
            }
            else {
                // this waveform is pretty similar, let's not store this one
                store = false;
                break;
            }
        }
    }
    if (store) {
        size_t head = unique_waveforms.head;
        unique_waveforms.data[head].adv_len = adv_len;
        memcpy(unique_waveforms.data[head].adv_payload, adv_data, adv_len);
        unique_waveforms.data[head].waveform_len = waveform_len;
        memcpy(unique_waveforms.data[head].waveform_payload, waveform_data, waveform_len);
        advance_pointer(&unique_waveforms);
    }
}

