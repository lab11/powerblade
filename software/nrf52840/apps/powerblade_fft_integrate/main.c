#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include "nrf.h"
#include "nrf_delay.h"
#include "nrf_gpio.h"
#include "nrf_drv_clock.h"
#include "nrf_uarte.h"
#include "nrf_serial.h"
#include "app_timer.h"
#include "nrf_log.h"
#include "nrf_log_ctrl.h"
#include "nrf_log_default_backends.h"

#include "nrf52840dk.h"

#include "arm_math.h"
#include "arm_const_structs.h"

#include "data.h"

#define SAMCOUNT 42
#define NUM_CYCLES 30
#define NUM_SAMPLES (NUM_CYCLES*SAMCOUNT)
#define FREQUENCY (42*60)
#define FFT_SIZE 2048

NRF_SERIAL_DRV_UART_CONFIG_DEF(m_uart0_drv_config,
        NRF_GPIO_PIN_MAP(0,6), NRF_GPIO_PIN_MAP(0,8),
        0, 0,
        NRF_UART_HWFC_DISABLED, NRF_UART_PARITY_EXCLUDED,
        NRF_UART_BAUDRATE_115200,
        UART_DEFAULT_CONFIG_IRQ_PRIORITY);

#define SERIAL_FIFO_TX_SIZE 256
#define SERIAL_FIFO_RX_SIZE 256

NRF_SERIAL_QUEUES_DEF(serial_queues, SERIAL_FIFO_TX_SIZE, SERIAL_FIFO_RX_SIZE);


#define SERIAL_BUFF_TX_SIZE 1
#define SERIAL_BUFF_RX_SIZE 1

NRF_SERIAL_BUFFERS_DEF(serial_buffs, SERIAL_BUFF_TX_SIZE, SERIAL_BUFF_RX_SIZE);

NRF_SERIAL_CONFIG_DEF(serial_config, NRF_SERIAL_MODE_DMA,
        &serial_queues, &serial_buffs, NULL, NULL);

NRF_SERIAL_UART_DEF(serial_uart, 0);

float voltage_result[NUM_SAMPLES];
static float filter_in_current[SAMCOUNT] = {0};
static float filter_in_voltage[SAMCOUNT] = {0};
static float current_mag[1024] = {0};

const int16_t Voff= -29;
const int16_t Ioff= -15;
const int16_t Curoff= 2;
const int16_t PScale= 16920;
const int16_t VScale= 11;
const int16_t WHScale= 9;
const uint16_t power_setpoint = 76 * 10;
const uint16_t voltage_setpoint = 120;

static arm_rfft_fast_instance_f32 fft_instance;

int main() {
    // Initialize.
    nrf_gpio_cfg_output(LED1);
    nrf_gpio_pin_set(LED1);

    uint32_t err_code;

    err_code = nrf_drv_clock_init();
    if (err_code != NRF_ERROR_MODULE_ALREADY_INITIALIZED){
        APP_ERROR_CHECK(err_code);
    }

    nrf_drv_clock_lfclk_request(NULL);
    err_code = app_timer_init();
    if (err_code != NRF_ERROR_MODULE_ALREADY_INITIALIZED){
        APP_ERROR_CHECK(err_code);
    }

    // initialize RTT library
    err_code = NRF_LOG_INIT(NULL);
    APP_ERROR_CHECK(err_code);
    NRF_LOG_DEFAULT_BACKENDS_INIT();
    printf("Log initialized!\n");

    err_code = nrf_serial_init(&serial_uart, &m_uart0_drv_config, &serial_config);
    printf("err_code = %x\n", err_code);

    arm_rfft_fast_init_f32(&fft_instance, FFT_SIZE);

    float coff = 0;
    float coff_count = 0;
    float acc_i_rms = 0;
    float acc_v_rms = 0;
    float acc_p_ave = 0;
    float Vrms = 0;
    float wattHoursToAverage = 0;
    float realPower = 0;
    float voltAmpsToAverage = 0;

    float vscale = VScale / 20.0;
    float pscale = (PScale & 0xFFF) * powf(10.0,-1*((PScale & 0xF000) >> 12));
    printf("pscale: %f\n", pscale);
    printf("pscale mantissa: %u\n", PScale & 0xfff);
    printf("pscale exp: %u\n", (PScale & 0xF000) >> 12);
    printf("pscale actual: %u * %f\n", PScale & 0xfff, powf(10, -1*((PScale & 0xf000) >> 12)));
    printf("vscale: %f\n", vscale);
    printf("iscale: %f\n", pscale/vscale);

    // calculate voff, ioff
    float voff = 0;
    float ioff = 0;

    for(size_t i = 0; i < NUM_SAMPLES; i++) {
        voff += voltage[i];
        ioff += dcurrent[i];
    }
    voff /= NUM_SAMPLES;
    ioff /= NUM_SAMPLES;

    printf("voff: %f\n", voff);
    printf("ioff: %f\n", ioff);

    float voltage_f[NUM_SAMPLES] = {0};
    float dcurrent_f[NUM_SAMPLES] = {0};

    for(size_t i = 0; i < NUM_SAMPLES; i++) {
        voltage_f[i] = (float)voltage[i] - voff;
        dcurrent_f[i] = (float)dcurrent[i] - ioff;
    }
    printf("original:\n");
    for(size_t i = 0; i < 10; i++) {
        printf("%f ", dcurrent_f[i]);
    }
    printf("\n");

    // zero pad input
    float current_result[FFT_SIZE] = {0};
    float current_result_z[FFT_SIZE] = {0};
    float fft_input[FFT_SIZE] = {0};
    float fft_current[FFT_SIZE] = {0};
    float fft_current_int_z[FFT_SIZE] = {0};
    memcpy(fft_input, dcurrent_f, NUM_SAMPLES*sizeof(float));

    // get fft of dcurrent
    arm_rfft_fast_f32(&fft_instance, fft_input, fft_current, 0);

    // create scaling vector
    float fft_int_scale[FFT_SIZE] = {0};
    for(size_t i = 0; i < FFT_SIZE; i+=2) {
        if (i == 0) continue;
        float frequency = i/2.0 * FREQUENCY / FFT_SIZE;
        fft_int_scale[i+1] = 1 / (2 * M_PI * frequency);
    }

    // scale frequency bins
    float fft_current_int[FFT_SIZE]; //
    arm_cmplx_mult_cmplx_f32(fft_int_scale, fft_current, fft_current_int, FFT_SIZE/2);

    memcpy(fft_current_int_z, fft_current_int, sizeof(fft_current_int));

    // zero out low frequency noise < 40*(42*60)/FFT_SIZE HzJK
    for(size_t i = 0; i < 40*2; i++) {
        fft_current_int_z[i] = 0;
    }

    // inverse fft
    arm_rfft_fast_f32(&fft_instance, fft_current_int, current_result, 1);
    // inverse fft filtered
    arm_rfft_fast_f32(&fft_instance, fft_current_int_z, current_result_z, 1);

    // Send over UART
    uint32_t len = sizeof(dcurrent_f);
    uint8_t buf[4*4096] = {0};
    buf[0] = 0xAA;
    buf[1] = 0xBB;
    memcpy(buf+2, &len, sizeof(len));
    memcpy(buf+6, dcurrent_f, len);
    nrf_serial_write(&serial_uart, buf, len+6, NULL, NRF_SERIAL_MAX_TIMEOUT);

    // Send integrated signal
    len = sizeof(float) * NUM_SAMPLES;
    buf[0] = 0xAA;
    buf[1] = 0xCC;
    memcpy(buf+2, &len, sizeof(len));
    memcpy(buf+6, current_result, len);
    nrf_serial_write(&serial_uart, buf, len+6, NULL, NRF_SERIAL_MAX_TIMEOUT);

    // Send integrated signal
    len = sizeof(float) * NUM_SAMPLES;
    buf[0] = 0xAA;
    buf[1] = 0xDD;
    memcpy(buf+2, &len, sizeof(len));
    memcpy(buf+6, current_result_z, len);
    nrf_serial_write(&serial_uart, buf, len+6, NULL, NRF_SERIAL_MAX_TIMEOUT);

    while(1) {
        NRF_LOG_PROCESS();
    }
}
