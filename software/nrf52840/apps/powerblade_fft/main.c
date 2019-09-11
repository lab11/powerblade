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

#define FILTER_LENGTH SAMCOUNT

#define TEST_LENGTH_SAMPLES 8192

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

static float filter_in_current[SAMCOUNT] = {0};
static float filter_in_voltage[SAMCOUNT] = {0};
static float filter_res_current[1024] = {0};
static float filter_res_voltage[1024] = {0};

const int16_t Voff= -29;
const int16_t Ioff= -15;
const int16_t Curoff= 2;
const int16_t PScale= 16920;
const int16_t VScale= 11;
const int16_t WHScale= 9;
const uint16_t power_setpoint = 76 * 10;
const uint16_t voltage_setpoint = 120;

float current_result[NUM_SAMPLES];
float voltage_result[NUM_SAMPLES];

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

    arm_rfft_fast_init_f32(&fft_instance, 1024);

  // calculate voff, ioff
  float voff = 0;
  float ioff = 0;
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

  for(uint16_t i = 0; i < NUM_SAMPLES; i++) {
    voff += voltage[i];
    ioff += dcurrent[i];
  }
  voff = voff / NUM_SAMPLES;
  ioff = ioff / NUM_SAMPLES;

  printf("voff: %f\n", voff);
  printf("ioff: %f\n", ioff);

  uint8_t sample_count = 0;
  uint16_t raw_count = 0;
  uint16_t integrate_count = 0;
  uint8_t measurement_count = 0;
  float agg_current = 0;

  while(1) {
    float i = dcurrent[raw_count] - Ioff;
    float v = voltage [raw_count++] - Voff;

    agg_current += i*1.5;
    agg_current -= agg_current / 32.0;

    filter_in_voltage[sample_count] = v;
    filter_in_current[sample_count] = agg_current;

    sample_count++;
    if (sample_count >= SAMCOUNT) {
      sample_count = 0;

      for(uint8_t j=0; j < SAMCOUNT; j++) {
        float _current = filter_in_current[j];
        float _voltage = filter_in_voltage[j];

        coff += _current/8.0;
        coff_count ++;
        _current = _current/8.0 - Curoff;

        current_result[integrate_count] = _current;
        voltage_result[integrate_count++] = _voltage;

        acc_i_rms += _current * _current;
        acc_p_ave += _voltage * _current;
        acc_v_rms += _voltage * _voltage;

      }

      // Increment energy calc
      wattHoursToAverage += acc_p_ave / SAMCOUNT;
      acc_p_ave = 0;

      // Calculate Irms, Vrms, and apparent power
      float Irms = sqrt(acc_i_rms / SAMCOUNT);
      Vrms = sqrt(acc_v_rms / SAMCOUNT);
      voltAmpsToAverage += (Irms * Vrms);

      //printf("Vrms: %d\n", (int32_t)(vscale*Vrms));
      //printf("acc_i_rms: %d\n", acc_i_rms);
      //printf("Irms: %d\n", Irms);
      acc_i_rms = 0;
      acc_v_rms = 0;

      measurement_count++;
      if (measurement_count >= NUM_CYCLES) {
        measurement_count = 0;

        coff = coff/coff_count;
        printf("coff: %f\n", coff);

        // True power cannot be less than zero
        if(wattHoursToAverage > 0) {
          realPower = (uint16_t) ((wattHoursToAverage / 60));
        }
        else {
          realPower = 0;
        }
        //wattHours += (uint64_t) realPower;
        //apparentPower = (uint16_t) ((voltAmpsToAverage / 60));

        printf("Vrms: %f\n", (vscale*Vrms));
        printf("P: %f\n", (pscale*realPower));

        wattHoursToAverage = 0;
        voltAmpsToAverage = 0;

        int32_t pscale_local = 0x4000 + ((uint16_t)((uint32_t)power_setpoint*1000/realPower) & 0x0FFF);
        int32_t vscale_local = 20 * voltage_setpoint / (uint16_t)Vrms;
        printf("new vscale: %d\n", vscale_local);
        printf("new pscale: %d\n", pscale_local);

        break;
      }
    }
    NRF_LOG_PROCESS();
  }

  arm_rfft_fast_f32(&fft_instance, current_result, filter_res_current, 0);
  for(size_t i = 0; i < 1024; i++) {
    filter_res_current[i] = abs(filter_res_current[i]);
  }
  printf("original:\n");
  for(size_t i = 0; i < 10; i++) {
    printf("%2x", current_result[i]);
  }
  printf("\n");
  printf("fft:\n");
  for(size_t i = 0; i < 10; i++) {
    printf("%2x", filter_res_current[i]);
  }
  printf("\n");

  // Send over UART
  uint32_t len = sizeof(float) * 1024;
  uint8_t *buf = malloc(len+6);
  //[sizeof(float)*TEST_LENGTH_SAMPLES/2] = {0};
  buf[0] = 0xAA;
  buf[1] = 0xBB;
  memcpy(buf+2, &len, sizeof(len));
  memcpy(buf+6, filter_res_current, len);
  nrf_serial_write(&serial_uart, buf, len+6, NULL, NRF_SERIAL_MAX_TIMEOUT);
  free(buf);

  while(1) {
    NRF_LOG_PROCESS();
  }
}
