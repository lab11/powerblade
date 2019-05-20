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

// find the next waveform to be transferred. Also marks the existing waveform
// as collected (if one is in `data`). Returns false if there is none.
bool get_next_waveform(unique_waveform_t* data) {
    //XXX implement me!
    return false;
}

// determine if this waveform should be saved and do so.
void check_and_store_new_waveform(uint8_t* waveform_data, uint16_t waveform_len, uint8_t* adv_data, uint16_t adv_len) {
    //XXX implement me!
    //check based on sequence number, real and apparent power, and maybe some similarity metric
}

