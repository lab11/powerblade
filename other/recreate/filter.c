#include "filter.h"

int16_t __q15mpy(int16_t a, int16_t b) {
  int32_t store = (int32_t)a * (int32_t)b;
  int16_t result = store >> 15;
  return result;
}

int msp_fill_q15(const msp_fill_q15_params *params, _q15 *dst)
{
    uint16_t length;

    /* Initialize the vector length. */
    length = params->length;
    while(length--) {
        *dst++ = params->value;
    }

    return 0;
}

int msp_biquad_cascade_df1_q15(const msp_biquad_cascade_df1_q15_params *params, const _q15 *src, _q15 *dst)
{
    uint16_t i;
    uint16_t stages;
    const _q15 *srcPtr;
    int status;
    msp_biquad_df1_q15_params df1Params;

    /* Load the number of stages from the parameters. */
    stages = params->stages;

    /* Set initial source pointer. */
    srcPtr = src;

    /* Run the input through all stages of the cascaded biquad. */
    for (i = 0; i < stages; i++) {
        /* Initialize the DF1 biquad parameter structure. */
        df1Params.length = params->length;
        df1Params.coeffs = &params->coeffs[i];
        df1Params.states = &params->states[i];

        /* Invoke the msp_biquad_df1_q15 function and check status flag. */
        status = msp_biquad_df1_q15(&df1Params, srcPtr, dst);
        if (status != 0) {
            /* Something went wrong, return the status of the operation. */
            return status;
        }

        /* Set source pointer to destination for next stage. */
        srcPtr = dst;
    }

    /* Return the status of the operation. */
    return status;
}

int msp_biquad_df1_q15(const msp_biquad_df1_q15_params *params, const _q15 *src, _q15 *dst)
{
    uint16_t i;
    uint16_t length;
    int16_t x2, x1, y2, y1;
    const msp_biquad_df1_q15_coeffs *coeffs;

    /* Initialize local variables and pointers. */
    length = params->length;
    coeffs = params->coeffs;
    x2 = params->states->x2;
    x1 = params->states->x1;
    y2 = params->states->y2;
    y1 = params->states->y1;

#if defined(__MSP430_HAS_MPY32__)
    /* If MPY32 is available save control context and set to fractional mode. */
    uint16_t ui16MPYState = MPY32CTL0;
    MPY32CTL0 = MPYFRAC | MPYDLYWRTEN | MPYSAT;

    /* Calculate filtered output using direct form 1. */
    for (i = 0; i < length; i++) {
        /* Process and update input states. */
        MPYS = x2;      OP2  = coeffs->b2;
        MACS = x1;      OP2  = coeffs->b1By2;
                        OP2  = coeffs->b1By2;
        x2 = x1;        x1 = *src++;
        MACS = x1;      OP2  = coeffs->b0;

        /* Process and update output states and result. */
        MACS = y2;      OP2 =  coeffs->a2;
        MACS = y1;      OP2  = coeffs->a1By2;
                        OP2 =  coeffs->a1By2;
        y2 = y1;        y1 = RESHI;
        *dst++ = y1;
    }

    /* Restore MPY32 control context. */
    MPY32CTL0 = ui16MPYState;
#else
    int32_t temp;
    int32_t result;

    /* Calculate filtered output using direct form 1. */
    for (i = 0; i < length; i++) {
        /* Process and update input states. */
        result  = __q15mpy(x2, coeffs->b2);
        temp    = __q15mpy(x1, coeffs->b1By2);
        result += temp;     result += temp;
        x2 = x1;            x1 = *src++;
        result += __q15mpy(x1, coeffs->b0);

        /* Process and update output states and result. */
        result += __q15mpy(y2, coeffs->a2);
        temp    = __q15mpy(y1, coeffs->a1By2);
        result += temp;     result += temp;
        result = (_q15)__saturate(result, INT16_MIN, INT16_MAX);
        y2 = y1;            y1 = result;
        *dst++ = y1;
    }
#endif

    /* Store the states and return. */
    params->states->x2 = x2;
    params->states->x1 = x1;
    params->states->y2 = y2;
    params->states->y1 = y1;

    return 0;
}
