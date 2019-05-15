/*
 * powerblade
 *
 * The purpose of this app is to measure power
 *
 * Reported values at 1Hz:
 * 	   PowerBlade ID:	1 byte
 * 	        sequence:	4 bytes		(since power on)
 * 	           scale:	4 bytes		(since data confirmation)
 * 	            Vrms:	1 byte		(over last 1s)
 * 	      true_power: 	2 bytes		(over last 1s)
 * 	  apparent_power:	2 bytes		(over last 1s)
 * 	      watt_hours:	4 bytes		(since data confirmation)
 * 	           flags:	1 byte
 */

#include <msp430.h>

#include <stdint.h>
#include <stdbool.h>

#include "powerblade_test.h"
#include "uart_types.h"
#include "checksum.h"
#include "uart.h"
#include "DSPLib.h"
#include "highpass.h"

#define FILTER_LENGTH SAMCOUNT
#define FILTER_STAGES (sizeof(highpass)/sizeof(msp_biquad_df1_q15_coeffs))


//#define NORDICDEBUG

// Transmission variables
bool ready;
bool senseEnabled;

// Variable for integration
int16_t agg_current;
int16_t agg_current_local;

// Count each sample and 60Hz measurement
uint8_t sampleCount;
uint8_t measCount;

// Global variables used interrupt-to-interrupt
#define BACKLOG_LEN		42
#if defined (ADC8)
int8_t current[BACKLOG_LEN];
int8_t voltage[BACKLOG_LEN];
int8_t savedCurrent;
int8_t savedVoltage;
#else
int16_t current[BACKLOG_LEN];
int16_t voltage[BACKLOG_LEN];
int16_t savedCurrent;
int16_t savedVoltage;
#endif
msp_fill_q15_params fillParams;
msp_biquad_cascade_df1_q15_params df1Params;
DSPLIB_DATA(filterCoeffs,4)
  msp_biquad_df1_q15_coeffs filterCoeffs[FILTER_STAGES];
DSPLIB_DATA(current_states,4)
  msp_biquad_df1_q15_states current_states[FILTER_STAGES];
DSPLIB_DATA(voltage_states,4)
  msp_biquad_df1_q15_states voltage_states[FILTER_STAGES];
DSPLIB_DATA(filter_in_current,4)
  _q15 filter_in_current[SAMCOUNT] = {0};
DSPLIB_DATA(filter_res_current,4)
  _q15 filter_res_current[SAMCOUNT] = {0};
DSPLIB_DATA(filter_in_voltage,4)
  _q15 filter_in_voltage[SAMCOUNT] = {0};
DSPLIB_DATA(filter_res_voltage,4)
  _q15 filter_res_voltage[SAMCOUNT] = {0};
uint8_t currentWriteCount;
uint8_t currentReadCount;
uint8_t voltageWriteCount;
uint8_t voltageReadCount;
int32_t acc_p_ave;
uint32_t acc_i_rms;
uint32_t acc_v_rms;
int32_t wattHoursToAverage;
uint32_t voltAmpsToAverage;

// Near-constants to be transmitted
uint16_t uart_len;
uint8_t ad_len = ADLEN;
uint8_t powerblade_id = 2;
const char msp_software_version = 3;

// Transmitted values
uint32_t sequence;
uint32_t scale;
uint8_t Vrms;
uint16_t truePower;
uint16_t apparentPower;
#pragma PERSISTENT(wattHours)
uint64_t wattHours = 0;

// Waveform storage
#define WAVEFORM_TRANSMIT_PERIOD 1
int32_t waveform_i[SAMCOUNT];
int16_t waveform_v[SAMCOUNT];

// Local calibration values
int32_t voff_local;
int32_t voff_count;
int32_t ioff_local;
int32_t ioff_count;
int32_t curoff_local;
int32_t curoff_count;
int32_t vscale_local;
int32_t pscale_local;
int16_t vsamp[2400];
int16_t isamp[2400];
uint16_t vSampOffset;
uint16_t iSampOffset;
uint16_t wattageSetpoint;
uint16_t voltageSetpoint;

#pragma PERSISTENT(flags)
uint8_t flags = 0x0F & msp_software_version;	// Lowest four bits of flags is software version

// Scale and offset values (configuration/calibration)
#pragma PERSISTENT(pb_config)
#if defined (ADC8)
PowerBladeConfig_t pb_config = { .voff = -1, .ioff = -1, .curoff = 0x0000, .pscale = 0x428A, .vscale = 0x7B, .whscale = 0x09};
#else
PowerBladeConfig_t pb_config = { .voff = -1, .ioff = -16, .curoff = 0x0000, .pscale = 0x428A, .vscale = 0x79, .whscale = 0x09};
#endif

// PowerBlade state (used for downloading data)
int dataIndex;
pb_state_t pb_state;
int txIndex;
bool dataComplete;
int pb_toggle;

uint32_t SquareRoot(uint32_t a_nInput) {
  uint32_t op = a_nInput;
  uint32_t res = 0;
  uint32_t one = 1uL << 30; // The second-to-top bit is set: use 1u << 14 for uint16_t type; use 1uL<<30 for uint32_t type

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

// Variables and functions for keeping computation and transmission out of interrupts
uint16_t tryCount;
uint16_t sendCount;
void transmitTry(void);
void transmit(void);

/*
 * main.c
 */
int main(void) {
  // Reset WDT, start WDT at 16s interval on ACLK
  WDTCTL = WDTPW + WDTSSEL_1 + WDTCNTCL + WDTIS_3;

  // Port J Configuration
  PJSEL0 |= BIT4 + BIT5;						// XIN, XOUT on PJ4, PJ5 with external crystal
  PJSEL0 |= BIT0;								// ZC signal on TDO
  PJSEL1 |= BIT0;
  PJDIR = 0;									// Low power in port J (no IO)
  PJOUT = 0;
  PJREN = 0xFF;

  // Port 1 Configuration
  P1SEL1 |= BIT0 + BIT1 + BIT4 + BIT5;		// Set up ADC on A0, A1, A4, & A5
  P1SEL0 |= BIT0 + BIT1 + BIT4 + BIT5;
  P1OUT = SYS_EN_PIN;							// Low power in port 1 and enable GPIO
  P1DIR = BIT2 + BIT3 + SYS_EN_PIN;
  P1REN = 0xFF;

  // Port 2 Configuration
  P2OUT = 0;									// Low power in port 2
  P2DIR = SEN_EN_PIN;
  P2REN = 0xFF;
  P2SEL0 = 0;

  // Initialize system state
  pb_state = pb_normal;
  pb_toggle = 0;
  ready = 0;
  senseEnabled = 0;
  tryCount = 0;
  sendCount = 0;

  // Zero all sensing values
  currentWriteCount = 0;
  currentReadCount = 0;
  voltageWriteCount = 0;
  voltageReadCount = 0;
  //wattHours = 0;
  sampleCount = 0;
  measCount = 0;

  // Initialize remaining transmitted values
  //sequence = 0;
  txIndex = 0;

  // Initialize scale value (can be updated later)
  scale = pb_config.pscale;
  scale = (scale<<8)+pb_config.vscale;
  scale = (scale<<8)+pb_config.whscale;

  // Clock Setup
  CSCTL0_H = 0xA5;							// Input CSKEY password to change clock settings
  CSCTL1 = DCOFSEL0 + DCOFSEL1;             	// Set DCO to 8MHz
  CSCTL2 = SELA_0 + SELS_3 + SELM_3;        	// Set ACLK = XT1, SMCLK = MCLK = DCO
  CSCTL3 = DIVA_0 + DIVS_1 + DIVM_1;        	// Set ACLK = XT1/1 (32768Hz), SMCLK = MCLK = DCO/2 (4MHz)
  CSCTL4 |= XT1DRIVE_0;						// Set XT1 LF, lowest current consumption
  CSCTL4 &= ~XT1OFF;							// Turn on XT1
  do {										// Test XT1 for correct initialization
    CSCTL5 &= ~XT1OFFG;					  	// Clear XT1 fault flags
    SFRIFG1 &= ~OFIFG;
  } while (SFRIFG1 & OFIFG);              	// Test oscillator fault flag
  // XT1 test passed

  // Set up UART
  uart_init();

  // Set up ADC
  ADC10CTL0 |= ADC10ON;                  		// Turn ADC on (ADC10ON), no multiple sample (ADC10MSC)
  ADC10CTL1 |= ADC10SHS_0 + ADC10SHP;			// ADC10SC source select, sampling timer
#if defined (ADC8)
  ADC10CTL2 &= ~ADC10RES;                    	// 8-bit conversion results
#else
  ADC10CTL2 |= ADC10RES;
#endif
  ADC10MCTL0 = VCCMCTL0; 						// Reference set to VCC & VSS, first input set to VCC_SENSE
  ADC10CTL0 |= ADC10ENC;                     	// ADC10 Enable
  ADC10IE |= ADC10IE0;                   		// Enable ADC conv complete interrupt

  // ADC conversion trigger signal - TimerA0.0
  TA0CCR0 = 13;								// Timer Period
  TA0CCTL0 = CCIE;               				// TA0CCR0 interrupt
  TA0CTL = TASSEL_1 + MC_2 + TACLR;          	// TA0 set to ACLK (32kHz), up mode

  // Wait timer for transmissions
  TA1CTL = TASSEL_1 + MC_2 + TACLR;			// ACLK, up mode

  // Initialize filter coefficients.
  memcpy(filterCoeffs, highpass, sizeof(filterCoeffs));

  // Initialize the parameter structure.
  df1Params.length = FILTER_LENGTH;
  df1Params.stages = FILTER_STAGES;
  df1Params.coeffs = filterCoeffs;

  // Zero initialize filter states.
  msp_status status;
  fillParams.length = sizeof(current_states)/sizeof(_q15);
  fillParams.value = 0;
  status = msp_fill_q15(&fillParams, (void *)current_states);
  msp_checkStatus(status);
  status = msp_fill_q15(&fillParams, (void *)voltage_states);
  msp_checkStatus(status);

  __bis_SR_register(LPM3_bits + GIE);        	// Enter LPM3 w/ interrupts

  while(1) {
    while(tryCount > 0) {
      tryCount--;
      transmitTry();
    }
    while(sendCount > 0) {
      sendCount--;
      transmit();
    }
    __bis_SR_register(LPM3_bits + GIE);
  }
}

#pragma vector=TIMER0_A0_VECTOR
__interrupt void TIMERA0_ISR(void) {
  TA0CCTL0 &= ~CCIFG;
  TA0CCR0 += 13;
  //	P1OUT |= BIT2;

  // Start with VCC_SENSE
  ADC10CTL0 &= ~ADC10ENC;
  ADC10MCTL0 = VCCMCTL0;
  ADC10CTL0 |= ADC10ENC;
  ADC10CTL0 += ADC10SC;

  //	P1OUT &= ~BIT2;
}

#pragma vector=TIMER1_A0_VECTOR
__interrupt void TIMERA1_ISR(void) {
  //	P1OUT |= BIT2;
  TA1CCTL0 = 0;
  sendCount++;
  __bic_SR_register_on_exit(LPM3_bits);
  //	P1OUT &= ~BIT2;
}

void transmit(void) {
  //	P1OUT |= BIT2;

  // Stuff data into txBuf
  int blockOffset = txIndex * UARTBLOCK;
  uart_stuff(blockOffset + OFFSET_UARTLEN, (char*) &uart_len, sizeof(uart_len));
  uart_stuff(blockOffset + OFFSET_ADLEN, (char*) &ad_len, sizeof(ad_len));
  uart_stuff(blockOffset + OFFSET_PBID, (char*) &powerblade_id, sizeof(powerblade_id));
  uart_stuff(blockOffset + OFFSET_SEQ, (char*) &sequence, sizeof(sequence));

  uart_stuff(blockOffset + OFFSET_SCALE, (char*) &scale, sizeof(scale));

  uart_stuff(blockOffset + OFFSET_VRMS, (char*) &Vrms, sizeof(Vrms));

  // XXX this is kind of cheating
  if (apparentPower < truePower) {
    apparentPower = truePower;
  }

  uart_stuff(blockOffset + OFFSET_TP, (char*) &truePower, sizeof(truePower));
  uart_stuff(blockOffset + OFFSET_AP, (char*) &apparentPower, sizeof(apparentPower));

  uint32_t wattHoursSend = (uint32_t)(wattHours >> pb_config.whscale);
  uart_stuff(blockOffset + OFFSET_WH, (char*) &wattHoursSend, sizeof(wattHoursSend));

  uart_stuff(blockOffset + OFFSET_FLAGS, (char*) &flags, sizeof(flags));

  // About to transmit, reset the watchdog timer
  WDTCTL = WDTPW + WDTSSEL_1 + WDTCNTCL + WDTIS_3;

  uart_send(blockOffset, uart_len);

  //	P1OUT &= ~BIT2;
}

void transmitTry(void) {
  // keep a counter for when to send waveform data
  static uint8_t waveform_counter = 0;

  P1OUT |= BIT3;

  // Save voltage and current before next interrupt happens
  savedCurrent = current[currentReadCount++];
  if (currentReadCount == BACKLOG_LEN) {
    currentReadCount = 0;
  }
  savedVoltage = voltage[voltageReadCount++];
  if (voltageReadCount == BACKLOG_LEN) {
    voltageReadCount = 0;
  }

  // Integrate current
  agg_current += (int16_t) (savedCurrent + (savedCurrent >> 1));
  agg_current -= agg_current >> 5;

  filter_in_voltage[sampleCount] = (_q15)savedVoltage;
  filter_in_current[sampleCount] = (_q15)agg_current;

  sampleCount++;
  if (sampleCount == SAMCOUNT) { 				// Entire AC wave sampled (60 Hz)

    // Filter on current, 40Hz cut off high-pass
    msp_status status;
    df1Params.states = current_states;
    status = msp_biquad_cascade_df1_q15(&df1Params, filter_in_current, filter_res_current);
    msp_checkStatus(status);
    df1Params.states = voltage_states;
    status = msp_biquad_cascade_df1_q15(&df1Params, filter_in_voltage, filter_res_voltage);
    msp_checkStatus(status);

    uint8_t i;
    // Perform calculations for I^2, V^2, and P
    for(i = 0; i < SAMCOUNT; i++) {
      int32_t _current = (int32_t)filter_res_current[i];
      int16_t _voltage = (int16_t)filter_res_voltage[i];

      // subtract offset
      if(pb_state == pb_local3) {
        _current = (_current >> 3) - curoff_local;
      } else {
        _current = (_current >> 3) - pb_config.curoff;
        if(pb_state == pb_local2) {
          curoff_local += agg_current >> 3;
          curoff_count++;
        }
      }
      if (measCount == 59) {
        waveform_i[i] = (int32_t)_current;
        waveform_v[i] = _voltage;
      }
      acc_i_rms += (uint64_t)(_current * _current);
      acc_p_ave += ((int64_t)_voltage * _current);
      acc_v_rms += (uint64_t)((int32_t)_voltage * (int32_t)_voltage);
    }

    // Reset sampleCount once per wave
    sampleCount = 0;

    // Increment energy calc
    wattHoursToAverage += (int32_t)(acc_p_ave / SAMCOUNT);
    acc_p_ave = 0;

    // Calculate Irms, Vrms, and apparent power
    uint16_t Irms = (uint16_t) SquareRoot64(acc_i_rms / SAMCOUNT);
    Vrms = (uint8_t) SquareRoot64(acc_v_rms / SAMCOUNT);
    voltAmpsToAverage += (uint32_t) (Irms * Vrms);
    acc_i_rms = 0;
    acc_v_rms = 0;

    measCount++;
    if (measCount >= 60) { 					// Another second has passed
      measCount = 0;
      waveform_counter++;

      uart_len = ADLEN + UARTOVHD;

      if (pb_toggle < 1) {
        pb_toggle++;
      } else {
        if (pb_state == pb_local1) {
          voff_local = voff_local / voff_count;
          ioff_local = ioff_local / ioff_count;
          pb_state = pb_local2;
          pb_toggle = 0;
        } else if (pb_state == pb_local2) {
          curoff_local = curoff_local / curoff_count;
          pb_state = pb_local3;
        } else if (pb_state == pb_local3) {
          pscale_local = 0x4000 + ((uint16_t)((uint32_t)wattageSetpoint*1000/truePower) & 0x0FFF);
          vscale_local = 20 * voltageSetpoint / (uint16_t)Vrms;
          pb_state = pb_local_done;
          pb_toggle = 0;
        }
      }

      // Process any UART bytes
      if (pb_state == pb_capture) {
        rxCt = 0;	// Clear any message received in this time
        uart_len = UARTBLOCK;
        pb_state = pb_data;
        char data_type = CONT_SAMDATA;
        uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &data_type, sizeof(data_type));
      } else if (processMessage() > 0) {
        switch(captureType) {
          case GET_CONF:
            uart_len += 1 + sizeof(pb_config);	// Add length of data type AND length of pb_config
            uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &captureType, sizeof(captureType));
            memcpy(txBuf + 1 + OFFSET_DATATYPE+(txIndex*UARTBLOCK), &pb_config, sizeof(pb_config));
            break;
          case SET_CONF:
            // XXX do we want to do any bounds-checking on this?
            memcpy(&pb_config, captureBuf, sizeof(pb_config));
            scale = pb_config.pscale;
            scale = (scale<<8)+pb_config.vscale;
            scale = (scale<<8)+pb_config.whscale;
            flags |= 0x80;
            break;
          case GET_VER:
            uart_len += 2;						// Add length of data type and version
            uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &captureType, sizeof(captureType));
            uart_stuff(1 + OFFSET_DATATYPE+(txIndex*UARTBLOCK), (char*)&msp_software_version, sizeof(msp_software_version));
            break;
          case SET_SEQ:
            {
              //sequence = captureBuf[0];
              uart_len += 1;
              char data_type = UART_NAK;
              uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
              break;
            }
          case CLR_WH:
            {
              //wattHours = 0;
              uart_len += 1;
              char data_type = UART_NAK;
              uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
              break;
            }
          default:
            switch(pb_state) {

              case pb_normal:
                switch(captureType) {
                  case START_SAMDATA:
                    {
                      pb_state = pb_capture;
                      dataIndex = 0;
                      uart_len += 1;
                      char data_type = START_SAMDATA;
                      uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
                      break;
                    }
                  case START_LOCALC:
                    {
                      pb_state = pb_local1;
                      vSampOffset = 0;
                      iSampOffset = 0;
                      dataIndex = 0;
                      memcpy(&wattageSetpoint, captureBuf, sizeof(wattageSetpoint));
                      memcpy(&voltageSetpoint, captureBuf + sizeof(wattageSetpoint), sizeof(voltageSetpoint));
                      uart_len += 1;
                      char data_type = START_LOCALC;
                      uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
                      break;
                    }
                  default:
                    break;
                }
                break;

              case pb_data:
                switch(captureType) {
                  case CONT_SAMDATA:
                    if (dataComplete) {
                      uart_len += 1;
                      txIndex = 0;
                      pb_state = pb_normal;
                      dataComplete = 0;
                      char data_type = DONE_SAMDATA;
                      uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
                    } else {
                      uart_len = UARTBLOCK;
                      txIndex++;
                      char data_type = CONT_SAMDATA;
                      uart_stuff(OFFSET_DATATYPE+(txIndex*UARTBLOCK), &data_type, sizeof(data_type));
                      if (txIndex == 9) {
                        dataComplete = 1;
                      }
                    }
                    break;
                  case UART_NAK:
                    uart_len = UARTBLOCK;
                    break;
                  default:
                    break;
                }
                break;

              case pb_local1:
              case pb_local2:
              case pb_local3:
                switch(captureType) {
                  case CONT_LOCALC:
                    {
                      uart_len += 1;
                      char data_type = CONT_LOCALC;
                      uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
                      break;
                    }
                  default:
                    break;
                }
                break;

              case pb_local_done:
                switch(captureType) {
                  case CONT_LOCALC:
                    {
                      uart_len += 1;
                      char data_type = DONE_LOCALC;
                      uart_stuff(OFFSET_DATATYPE, &data_type, sizeof(data_type));
                      pb_config.voff = voff_local;
                      pb_config.ioff = ioff_local;
                      pb_config.curoff = curoff_local;
                      pb_config.vscale = vscale_local;
                      pb_config.pscale = pscale_local;
                      scale = pb_config.pscale;
                      scale = (scale<<8)+pb_config.vscale;
                      scale = (scale<<8)+pb_config.whscale;
                      flags &= 0x3F;	// Clear any previous calibration
                      flags |= 0x40;
                      break;
                    }
                  default:
                    break;
                }

            }
            break;
        }
      } else {
        if (savedCount > 0) {	// Had partial message for multiple bookends
          rxCt = 0;
        }

        // append a waveform every several cycles
        if (pb_state == pb_normal && waveform_counter >= WAVEFORM_TRANSMIT_PERIOD) {
          waveform_counter = 0;
          uart_len += 1 + sizeof(int32_t)*SAMCOUNT + sizeof(int16_t)*SAMCOUNT;
          char data_type = WAVEFORM;
          int blockOffset = txIndex * UARTBLOCK;
          uart_stuff(blockOffset + OFFSET_DATATYPE, &data_type, sizeof(data_type));
          uart_stuff(blockOffset + OFFSET_WAVEFORM_I, (char*)waveform_i, sizeof(int32_t)*SAMCOUNT);
          uart_stuff(blockOffset + OFFSET_WAVEFORM_V, (char*)waveform_v, sizeof(int16_t)*SAMCOUNT);
        }
      }
      savedCount = rxCt;

      // Increment sequence number for transmission
      sequence++;

      // True power cannot be less than zero
      if (wattHoursToAverage > 0) {
        truePower = (uint16_t) ((wattHoursToAverage / 60));
      } else {
        truePower = 0;
        // The following change makes it so applying PowerBlade backwards does not result in 0 for true power
        // TODO: this isnt a great fix, the original code was in place for a reason
        // truePower = (uint16_t) ((wattHoursToAverage / -60));
      }
      wattHours += (uint64_t) truePower;
      apparentPower = (uint16_t) ((voltAmpsToAverage / 60));

      wattHoursToAverage = 0;
      voltAmpsToAverage = 0;

#if defined (NORDICDEBUG)
      ready = 1;
#endif

      if (ready == 1) {
        // Boot the nordic and enable its UART
        SYS_EN_OUT &= ~SYS_EN_PIN;
        uart_enable(1);

        // Delay for a bit to allow nordic to boot
        // TODO this is only required the first time
        TA1CCR0 = TA1R + 500;
        TA1CCTL0 = CCIE;
      }
    }
  }
  P1OUT &= ~BIT3;
}

#pragma vector=ADC10_VECTOR
__interrupt void ADC10_ISR(void) {

#if defined (ADC8)
  uint8_t ADC_Result;
#else
  uint16_t ADC_Result;
#endif

  unsigned char ADC_Channel;

  switch (__even_in_range(ADC10IV, 12)) {
    case 12:
      ADC_Result = ADC10MEM0;
      ADC_Channel = ADC10MCTL0 & ADC10INCH_7;
      switch (ADC_Channel) {
        case ICASE:								// I_SENSE
          {
            //			P1OUT |= BIT2;
            // Store current value for future calculations
#if defined (ADC8)
            int8_t tempCurrent = (int8_t) (ADC_Result - I_VCC2);
#else
            int16_t tempCurrent;
            if (ADC_Result & 0x200) {	// Measurement above VCC/2
              tempCurrent = ADC_Result & 0x1FF;		// Subtract Vcc/2
            } else {
              tempCurrent = 0x200 - ADC_Result - 1;
              tempCurrent = ~tempCurrent;
            }
#endif

            if (pb_state == pb_capture) {
#if defined (ADC8)
              if (dataIndex < 5040) {
                int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1) + (dataIndex/504);
                uart_stuff(arrayIndex, (char*) &tempCurrent, sizeof(tempCurrent));
                dataIndex++;
              }
#else
              if (dataIndex < 2520) {
                //tempCurrent = -50;
                int arrayIndex = (2*dataIndex) + (ADLEN + UARTOVHD)*((dataIndex/252) + 1) + (dataIndex/252);
                uart_stuff(arrayIndex, (char*) &tempCurrent, sizeof(tempCurrent));
                dataIndex++;
              }
#endif
            } else if (pb_state == pb_local1) {
              if (dataIndex >= 60 && dataIndex < 4980) {
                ioff_local += tempCurrent;
                ioff_count++;
              }
              dataIndex++;
            }
            //			else if (pb_state == pb_local2) {
            //				int16_t newCurrent = tempCurrent - ioff_local;
            //				agg_current_local += (newCurrent + (newCurrent >> 1));
            //				agg_current_local -= agg_current_local >> 5;
            //				curoff_local += agg_current_local >> 3;
            //				curoff_count++;
            //			}

            // After its been stored for raw sample transmission, apply offset
            if (pb_state == pb_local2 || pb_state == pb_local3) {
              current[currentWriteCount++] = tempCurrent - ioff_local;
            } else {
              current[currentWriteCount++] = tempCurrent - pb_config.ioff;
            }
            if (currentWriteCount == BACKLOG_LEN) {
              currentWriteCount = 0;
            }

            // Current is the last measurement, attempt transmission
            //transmitTry();
            tryCount++;
            __bic_SR_register_on_exit(LPM3_bits);
            break;
          }
        case VCASE:								// V_SENSE
          {
            //			P1OUT |= BIT2;
            // Store voltage value
#if defined (ADC8)
            int8_t tempVoltage = (int8_t) (ADC_Result - V_VCC2) * -1;
#else
            int16_t tempVoltage;
            if (ADC_Result & 0x200) {	// Measurement above VCC/2
              tempVoltage = ADC_Result & 0x1FF;		// Subtract Vcc/2
              tempVoltage = ~tempVoltage;				// Mult by -1
            } else {
              ADC_Result = ~ADC_Result;
              tempVoltage = ADC_Result + 0x200 + 1;
            }
#endif

            if (pb_state == pb_capture) {
#if defined (ADC8)
              if (dataIndex < 5040) {
                int arrayIndex = dataIndex + (ADLEN + UARTOVHD)*((dataIndex/504) + 1) + (dataIndex/504);
                uart_stuff(arrayIndex, (char*) &tempVoltage, sizeof(tempVoltage));
                dataIndex++;
              }
#else
              if (dataIndex < 2520) {
                //tempVoltage = -194;
                int arrayIndex = (2*dataIndex) + (ADLEN + UARTOVHD)*((dataIndex/252) + 1) + (dataIndex/252);
                uart_stuff(arrayIndex, (char*) &tempVoltage, sizeof(tempVoltage));
                dataIndex++;
              }
#endif
            } else if (pb_state == pb_local1) {
              if (dataIndex >= 60 && dataIndex < 4980) {
                voff_local += tempVoltage;
                voff_count++;
              }
              dataIndex++;
            }

            // After its been stored for raw sample transmission, apply offset
            if (pb_state == pb_local2 || pb_state == pb_local3) {
              voltage[voltageWriteCount++] = tempVoltage - voff_local;
            } else {
              voltage[voltageWriteCount++] = tempVoltage - pb_config.voff;
            }
            if (voltageWriteCount == BACKLOG_LEN) {
              voltageWriteCount = 0;
            }

            // Enable next sample
            // After V_SENSE do I_SENSE
            ADC10CTL0 &= ~ADC10ENC;
            ADC10MCTL0 = IMCTL0;
            ADC10CTL0 |= ADC10ENC;
            ADC10CTL0 += ADC10SC;
            break;
          }
        case VCCCASE:	// VCC_SENSE
          //			P1OUT |= BIT2;
          //XXX: Fake VCap on the nRF dev board
          //ADC_Result = ADC_VCHG+1;

          // Perform Vcap measurements
          if (ADC_Result < ADC_VMIN) {
#if !defined (NORDICDEBUG)
            uart_enable(0);
            SYS_EN_OUT |= SYS_EN_PIN;
            ready = 0;
#endif
          } else if (ready == 0) {
            if (ADC_Result > ADC_VCHG) {
              SEN_EN_OUT |= SEN_EN_PIN;
              senseEnabled = 1;
              acc_p_ave = 0;
              acc_i_rms = 0;
              acc_v_rms = 0;
              wattHoursToAverage = 0;
              voltAmpsToAverage = 0;
              agg_current = 0;
              agg_current_local = 0;
              ready = 1;
            }
          }

#if defined (NORDICDEBUG)
          senseEnabled = 1;
#endif

          // Enable next sample
          // After VCC_SENSE do V_SENSE
          if (senseEnabled == 1) {
            ADC10CTL0 &= ~ADC10ENC;
            ADC10MCTL0 = VMCTL0;
            ADC10CTL0 |= ADC10ENC;
            ADC10CTL0 += ADC10SC;
          }
          break;
        default: // ADC Reset condition
          ADC10CTL0 += ADC10SC;
          break;
      }
      break;                          // Clear CPUOFF bit from 0(SR)
    default:
      break;
  }
  //	P1OUT &= ~(BIT2);
}



