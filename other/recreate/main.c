#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

#include "data.h"
#include "filter.h"
#include "highpass.h"

#define FILTER_LENGTH SAMCOUNT
#define FILTER_STAGES (sizeof(highpass)/sizeof(msp_biquad_df1_q15_coeffs))
static msp_biquad_df1_q15_coeffs filterCoeffs[FILTER_STAGES];
static msp_fill_q15_params fillParams;
static msp_biquad_cascade_df1_q15_params df1Params;
static msp_biquad_df1_q15_states current_states[FILTER_STAGES];
static msp_biquad_df1_q15_states voltage_states[FILTER_STAGES];

const int16_t Voff= -29;
const int16_t Ioff= -15;
const int16_t Curoff= 2;
const int16_t PScale= 16913;
const int16_t VScale= 126;
const int16_t WHScale= 9;
const uint16_t power_setpoint = 76 * 10;
const uint16_t voltage_setpoint = 120;

#define SAMCOUNT 42
#define NUM_CYCLES 30
#define NUM_SAMPLES (NUM_CYCLES*SAMCOUNT)

int16_t current_result[NUM_SAMPLES];
int16_t voltage_result[NUM_SAMPLES];
uint16_t count = 0;

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
  memcpy(filterCoeffs, highpass, sizeof(filterCoeffs));

  // Initialize the parameter structure.
  df1Params.length = FILTER_LENGTH;
  df1Params.stages = FILTER_STAGES;
  df1Params.coeffs = filterCoeffs;

  // Zero initialize filter states.
  fillParams.length = sizeof(current_states)/sizeof(_q15);
  fillParams.value = 0;
  int status = msp_fill_q15(&fillParams, (void *)current_states);
  status = msp_fill_q15(&fillParams, (void *)voltage_states);

  for(uint16_t i = 0; i < NUM_SAMPLES; i++) {
    voff += voltage[i];
    ioff += dcurrent[i];
  }
  voff = voff / NUM_SAMPLES;
  ioff = ioff / NUM_SAMPLES;

  printf("voff: %d\n", voff);
  printf("ioff: %d\n", ioff);

  uint8_t sample_count = 0;
  uint8_t measurement_count = 0;
  int32_t agg_current = 0;

  while(1) {
    int16_t i = dcurrent[count] - Ioff;
    int16_t v = voltage [count] - Voff;

    //printf("agg_current before: %d\n", agg_current);
    agg_current += (int16_t) (i + (i >> 1));
    agg_current -= agg_current >> 5;
    //printf("agg_current after: %d\n", agg_current);

    coff += (agg_current >> 3);
    coff_count ++;

    int32_t new_current = (agg_current >> 3) - Curoff;
    current_result[count] = new_current;
    voltage_result[count++] = v;

    acc_i_rms += (uint64_t)(new_current * new_current);
    acc_p_ave += ((int64_t)v * new_current);
    acc_v_rms += (uint64_t)((int32_t)v * (int32_t)v);

    sample_count++;
    if (sample_count == SAMCOUNT) {
      sample_count = 0;

      // Increment energy calc
      wattHoursToAverage += (int32_t)(acc_p_ave / SAMCOUNT);
      acc_p_ave = 0;

      // Calculate Irms, Vrms, and apparent power
      uint16_t Irms = (uint16_t) SquareRoot64(acc_i_rms / SAMCOUNT);
      Vrms = (uint8_t) SquareRoot64(acc_v_rms / SAMCOUNT);
      voltAmpsToAverage += (uint32_t) (Irms * Vrms);
      acc_i_rms = 0;
      acc_v_rms = 0;

      //printf("Vrms: %d\n", (int32_t)(vscale*Vrms));
      //printf("Irms: %d\n", Irms);

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
    fprintf(f, "%u, %d, %d, %d, %d\n", i, voltage[i], dcurrent[i], voltage_result[i], current_result[i]);
  }

  fclose(f);
}
