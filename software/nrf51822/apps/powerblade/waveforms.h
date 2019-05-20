#ifndef POWERBLADE_WAVEFORMS_H
#define POWERBLADE_WAVEFORMS_H

#include "uart_types.h"

// data struct
typedef struct {
    uint8_t adv_payload[ADV_DATA_MAX_LEN];
	uint8_t waveform_payload[WAVEFORM_MAX_LEN];
} unique_waveform_t;

// function prototypes
uint32_t parse_sequence_number(uint8_t* adv_data, uint16_t adv_len);
uint16_t parse_real_power(uint8_t* adv_data, uint16_t adv_len);
uint16_t parse_apparent_power(uint8_t* adv_data, uint16_t adv_len);
uint8_t parse_flags(uint8_t* adv_data, uint16_t adv_len);

void flag_nrf_restart(bool restarted, uint8_t* adv_data, uint16_t adv_len);
void flag_waveform_available(bool available, uint8_t* adv_data, uint16_t adv_len);

bool get_next_waveform(unique_waveform_t* data);
void waveform_collected(unique_waveform_t* data);
void check_and_store_new_waveform(uint8_t* waveform_data, uint16_t waveform_len, uint8_t* adv_data, uint16_t adv_len);

#endif //POWERBLADE_WAVEFORMS_H

