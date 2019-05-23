#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

#include "data.h"
#include "filter.h"
#include "highpass.h"

#define SAMCOUNT 42
#define NUM_CYCLES 30
#define NUM_SAMPLES (NUM_CYCLES*SAMCOUNT)

#define FILTER_LENGTH SAMCOUNT

static int16_t filter_in_current[SAMCOUNT] = {0};
static int16_t filter_in_voltage[SAMCOUNT] = {0};
static int16_t filter_res_current[SAMCOUNT] = {0};
static int16_t filter_res_voltage[SAMCOUNT] = {0};
static int16_t og_current[NUM_SAMPLES] = {0};

const int16_t Voff= -29;
const int16_t Ioff= -15;
const int16_t Curoff= 0;
const int16_t PScale= 17068;
const int16_t VScale= 58;
const int16_t WHScale= 9;
const uint16_t power_setpoint = 76 * 10;
const uint16_t voltage_setpoint = 120;

int16_t current_result[NUM_SAMPLES];
int16_t voltage_result[NUM_SAMPLES];
float alpha = 0.07203844415598515;

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

void ema_highpass(int16_t* input, int16_t* output, uint16_t len, float* s, float a) {
  for(uint16_t i = 0; i < len; i++) {
    *s = a * input[i] + (1 - a) * *s;
    output[i] = (int16_t) ((float)input[i] - *s);
  }
}

void main() {

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
  printf("pscale: %f\n", pscale);
  printf("pscale mantissa: %u\n", PScale & 0xfff);
  printf("pscale exp: %u\n", (PScale & 0xF000) >> 12);
  printf("pscale actual: %u * %f\n", PScale & 0xfff, powf(10, -1*((PScale & 0xf000) >> 12)));
  printf("vscale: %f\n", vscale);
  printf("iscale: %f\n", pscale/vscale);

  // filter init
  // Initialize filter coefficients.
  float s_current = 0;
  float s_voltage = 0;

  for(uint16_t i = 0; i < NUM_SAMPLES; i++) {
    voff += voltage[i];
    ioff += dcurrent[i];
  }
  voff = voff / NUM_SAMPLES;
  ioff = ioff / NUM_SAMPLES;

  printf("voff: %d\n", voff);
  printf("ioff: %d\n", ioff);

  uint8_t sample_count = 0;
  uint16_t raw_count = 0;
  uint16_t integrate_count = 0;
  uint8_t measurement_count = 0;
  int32_t agg_current = 0;

  while(1) {
    int16_t i = dcurrent[raw_count] - Ioff;
    int16_t v = voltage [raw_count] - Voff;

    agg_current += (int16_t) (i + (i >> 1));
    agg_current -= agg_current >> 5;

    filter_in_voltage[sample_count] = v;
    filter_in_current[sample_count] = agg_current;
    og_current[raw_count++] = (agg_current >> 3) - Curoff;

    sample_count++;
    if (sample_count == SAMCOUNT) {
      sample_count = 0;

      ema_highpass(filter_in_voltage, filter_res_voltage, SAMCOUNT, &s_voltage, alpha);
      ema_highpass(filter_in_current, filter_res_current, SAMCOUNT, &s_current, alpha);

      for(uint8_t i=0; i < SAMCOUNT; i++) {
        int16_t _current = (int16_t)filter_res_current[i];
        int16_t _voltage = (int16_t)filter_res_voltage[i];
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

      //printf("Vrms: %d\n", (int32_t)(vscale*Vrms));
      //printf("acc_i_rms: %d\n", acc_i_rms);
      //printf("Irms: %d\n", Irms);
      acc_i_rms = 0;
      acc_v_rms = 0;

      measurement_count++;
      if (measurement_count > NUM_CYCLES) {
        measurement_count = 0;

        coff = coff/coff_count;
        printf("coff: %d\n", coff);

        // True power cannot be less than zero
        if(wattHoursToAverage > 0) {
          realPower = (uint16_t) ((wattHoursToAverage / 60));
        }
        else {
          realPower = 0;
        }
        //wattHours += (uint64_t) realPower;
        //apparentPower = (uint16_t) ((voltAmpsToAverage / 60));

        printf("Vrms: %d\n", (int32_t)(vscale*Vrms));
        printf("P: %d\n", (int32_t)(pscale*realPower));

        wattHoursToAverage = 0;
        voltAmpsToAverage = 0;

        int32_t pscale_local = 0x4000 + ((uint16_t)((uint32_t)power_setpoint*1000/realPower) & 0x0FFF);
        int32_t vscale_local = 20 * voltage_setpoint / (uint16_t)Vrms;
        printf("new vscale: %d\n", vscale_local);
        printf("new pscale: %d\n", pscale_local);

        break;
      }
    }
  }
  FILE *f = fopen("recreate_data.txt", "w");
  if (f == NULL)
  {
    printf("Error opening file\n");
    exit(1);
  }

  for(uint16_t i = 0; i < NUM_SAMPLES; i++) {
    fprintf(f, "%u, %d, %d, %d, %d, %d\n", i, voltage[i] - voff, dcurrent[i] - ioff, og_current[i], voltage_result[i], current_result[i]);
  }

  fclose(f);
}
