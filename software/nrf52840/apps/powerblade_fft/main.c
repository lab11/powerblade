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

static int16_t filter_in_current[SAMCOUNT] = {0};
static int16_t filter_in_voltage[SAMCOUNT] = {0};
static int16_t filter_res_current[SAMCOUNT] = {0};
static int16_t filter_res_voltage[SAMCOUNT] = {0};
static int16_t og_current[NUM_SAMPLES] = {0};

const int16_t Voff= -29;
const int16_t Ioff= -15;
const int16_t Curoff= 2;
const int16_t PScale= 16915;
const int16_t VScale= 11;
const int16_t WHScale= 9;
const uint16_t power_setpoint = 76 * 10;
const uint16_t voltage_setpoint = 120;

int16_t current_result[NUM_SAMPLES];
int16_t voltage_result[NUM_SAMPLES];

uint32_t SquareRoot64(uint64_t a_nInput) {
  uint64_t op = a_nInput;
  uint64_t res = 0;
  uint64_t one = (uint64_t)1 << 62; // The second-to-top bit is set: use 1u << 14 for uint16_t type; use 1uL<<30 for uint32_t type

  // "one" starts at the highest power of four <= than the argument.
  while (one > op) {
    one >>= 2;
  }

  while (one != 0) {
    if (op >= res + one) {
      op = op - (res + one);
      res = res + 2 * one;
    }
    res >>= 1;
    one >>= 2;
  }
  return res;
}

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
    NRF_LOG_INFO("Log initialized!\n");

    err_code = nrf_serial_init(&serial_uart, &m_uart0_drv_config, &serial_config);
    NRF_LOG_INFO("err_code = %x\n", err_code);

  // calculate voff, ioff
  int32_t voff = 0;
  int32_t ioff = 0;
  int32_t coff = 0;
  int32_t coff_count = 0;
  uint32_t acc_i_rms = 0;
  uint32_t acc_v_rms = 0;
  uint32_t acc_p_ave = 0;
  uint32_t Vrms = 0;
  uint32_t wattHoursToAverage = 0;
  uint16_t realPower = 0;
  uint32_t voltAmpsToAverage = 0;

  float vscale = VScale / 20.0;
  float pscale = (PScale & 0xFFF) * powf(10.0,-1*((PScale & 0xF000) >> 12));
  NRF_LOG_INFO("pscale: %f\n", pscale);
  NRF_LOG_INFO("pscale mantissa: %u\n", PScale & 0xfff);
  NRF_LOG_INFO("pscale exp: %u\n", (PScale & 0xF000) >> 12);
  NRF_LOG_INFO("pscale actual: %u * %f\n", PScale & 0xfff, powf(10, -1*((PScale & 0xf000) >> 12)));
  NRF_LOG_INFO("vscale: %f\n", vscale);
  NRF_LOG_INFO("iscale: %f\n", pscale/vscale);

  // filter init
  // Initialize filter coefficients.
  int16_t s_current = 0;
  int16_t s_voltage = 0;

  for(uint16_t i = 0; i < NUM_SAMPLES; i++) {
    voff += voltage[i];
    ioff += dcurrent[i];
  }
  voff = voff / NUM_SAMPLES;
  ioff = ioff / NUM_SAMPLES;

  NRF_LOG_INFO("voff: %ld\n", voff);
  NRF_LOG_INFO("ioff: %ld\n", ioff);

  uint8_t sample_count = 0;
  uint16_t raw_count = 0;
  uint16_t integrate_count = 0;
  uint8_t measurement_count = 0;
  int32_t agg_current = 0;

  while(1) {
    nrf_delay_ms(10);
    int16_t i = dcurrent[raw_count] - Ioff;
    int16_t v = voltage [raw_count] - Voff;

    agg_current += (int16_t) (i + (i >> 1));
    agg_current -= agg_current >> 5;

    filter_in_voltage[sample_count] = v;
    filter_in_current[sample_count] = agg_current;
    og_current[raw_count++] = (agg_current >> 3) - Curoff;

    sample_count++;
    //NRF_LOG_INFO("sc: %d\n", sample_count);
    if (sample_count >= SAMCOUNT) {
      NRF_LOG_INFO("sc: %d\n", sample_count);
      sample_count = 0;

      //ema_highpass_fixed(filter_in_voltage, filter_res_voltage, SAMCOUNT, &s_voltage);
      //ema_highpass_fixed(filter_in_current, filter_res_current, SAMCOUNT, &s_current);

      for(uint8_t j=0; j < SAMCOUNT; j++) {
        int16_t _current = (int16_t)filter_in_current[j];
        int16_t _voltage = (int16_t)filter_in_voltage[j];
        current_result[integrate_count] = _current;
        voltage_result[integrate_count++] = _voltage;

        coff += (_current >> 3);
        coff_count ++;
        _current = (_current >> 3) - Curoff;

        acc_i_rms += (uint64_t)(_current * _current);
        acc_p_ave += (int64_t)(_voltage * _current);
        acc_v_rms += (uint64_t)((int32_t)_voltage * (int32_t)_voltage);

      }

      // Increment energy calc
      wattHoursToAverage += (int32_t)(acc_p_ave / SAMCOUNT);
      acc_p_ave = 0;

      // Calculate Irms, Vrms, and apparent power
      uint16_t Irms = (uint16_t) SquareRoot64(acc_i_rms / SAMCOUNT);
      Vrms = (uint8_t) SquareRoot64(acc_v_rms / SAMCOUNT);
      voltAmpsToAverage += (uint32_t) (Irms * Vrms);

      //NRF_LOG_INFO("Vrms: %d\n", (int32_t)(vscale*Vrms));
      //NRF_LOG_INFO("acc_i_rms: %d\n", acc_i_rms);
      //NRF_LOG_INFO("Irms: %d\n", Irms);
      acc_i_rms = 0;
      acc_v_rms = 0;

      measurement_count++;
      NRF_LOG_INFO("mc: %d\n", measurement_count);
      if (measurement_count >= NUM_CYCLES) {
        measurement_count = 0;

        coff = coff/coff_count;
        NRF_LOG_INFO("coff: %d\n", coff);
        nrf_delay_ms(10);

        // True power cannot be less than zero
        if(wattHoursToAverage > 0) {
          realPower = (uint16_t) ((wattHoursToAverage / 60));
        }
        else {
          realPower = 0;
        }
        //wattHours += (uint64_t) realPower;
        //apparentPower = (uint16_t) ((voltAmpsToAverage / 60));

        NRF_LOG_INFO("Vrms: %d\n", (int32_t)(vscale*Vrms));
        nrf_delay_ms(10);
        NRF_LOG_INFO("P: %d\n", (int32_t)(pscale*realPower));
        nrf_delay_ms(10);

        wattHoursToAverage = 0;
        voltAmpsToAverage = 0;

        int32_t pscale_local = 0x4000 + ((uint16_t)((uint32_t)power_setpoint*1000/realPower) & 0x0FFF);
        int32_t vscale_local = 20 * voltage_setpoint / (uint16_t)Vrms;
        NRF_LOG_INFO("new vscale: %d\n", vscale_local);
        nrf_delay_ms(10);
        NRF_LOG_INFO("new pscale: %d\n", pscale_local);
        nrf_delay_ms(10);

        break;
      }
    }
    NRF_LOG_PROCESS();
  }
  while(1) {
    NRF_LOG_PROCESS();
  }
}
