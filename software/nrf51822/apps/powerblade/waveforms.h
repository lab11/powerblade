#ifndef POWERBLADE_WAVEFORMS_H
#define POWERBLADE_WAVEFORMS_H

#include "uart_types.h"
#include "string.h"

#define UNIQUE_WAVEFORM_MAX 8

// data struct
typedef struct {
    uint16_t adv_len;
    uint8_t adv_payload[ADV_DATA_MAX_LEN];
    uint16_t waveform_len;
    uint8_t waveform_payload[WAVEFORM_MAX_LEN];
} waveform_t;

// store unique waveforms in circular buffer
typedef struct {
    waveform_t data[UNIQUE_WAVEFORM_MAX];
    size_t head;
    size_t tail;
    bool full;
} unique_circle_buf;

// function prototypes
uint32_t parse_sequence_number(uint8_t* adv_data, uint16_t adv_len);
uint16_t parse_real_power(uint8_t* adv_data, uint16_t adv_len);
uint16_t parse_apparent_power(uint8_t* adv_data, uint16_t adv_len);
uint8_t parse_flags(uint8_t* adv_data, uint16_t adv_len);

void flag_nrf_restart(bool restarted, uint8_t* adv_data, uint16_t adv_len);
void flag_waveform_available(bool available, uint8_t* adv_data, uint16_t adv_len);

void reset_waveforms(unique_circle_buf *);
bool get_next_waveform(waveform_t* data);
void waveform_collected(waveform_t* data);
void check_and_store_new_waveform(waveform_t* waveform);

#endif //POWERBLADE_WAVEFORMS_H

