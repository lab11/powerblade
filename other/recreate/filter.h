
#ifndef __DSPLIB_FILTER_H__
#define __DSPLIB_FILTER_H__

#include <stdint.h>

#define __saturate(x, min, max) (((x)>(max))?(max):(((x)<(min))?(min):(x)))


#define _Q15(A)                 ((_q15)((((uint32_t)1 << 15) * \
                                __saturate(A,-1.0,32767.0/32768.0))))

typedef int16_t _q15;

typedef struct msp_fill_q15_params {
    //! Length of the source data, must be a multiple of two.
    uint16_t length;
    //! Scalar constant to fill the destination vector with.
    _q15 value;
} msp_fill_q15_params;

typedef struct msp_biquad_df1_q15_coeffs {
    //! \details
    //! Coefficient b2
    _q15 b2;
    //! \details
    //! Coefficient b1 divided by two
    _q15 b1By2;
    //! \details
    //! Coefficient b0
    _q15 b0;
    //! \details
    //! Reserved, do not remove
    uint16_t reserved1;
    //! \details
    //! Coefficient a2
    _q15 a2;
    //! \details
    //! Coefficient a1 divided by two
    _q15 a1By2;
} msp_biquad_df1_q15_coeffs;

typedef struct msp_biquad_df1_q15_states {
    //! \details
    //! Input x[n-2]
    _q15 x2;
    //! \details
    //! Input x[n-1]
    _q15 x1;
    //! \details
    //! Output y[n-2]
    _q15 y2;
    //! \details
    //! Output y[n-1]
    _q15 y1;
} msp_biquad_df1_q15_states;

typedef struct msp_biquad_df1_q15_params {
    //! \details
    //! Length of the source data, must be a multiple of two.
    uint16_t length;
    //! \details
    //! Pointer to DF1 filter coefficients. This data block must be allocated in
    //! shared RAM when using LEA.
    const msp_biquad_df1_q15_coeffs *coeffs;
    //! \details
    //! Pointer to an array of length four used to store the state of the
    //! operation. When continuous operation is desired the previous state
    //! needs to be passed to the next biquad operation. This data block must be
    //! allocated in shared RAM when using LEA.
    msp_biquad_df1_q15_states *states;
} msp_biquad_df1_q15_params;

typedef struct msp_biquad_cascade_df1_q15_params {
    //! \details
    //! Length of the source data, must be a multiple of two.
    uint16_t length;
    //! \details
    //! Number of cascaded biquad filters, typically the filter order divided by
    //! two.
    uint16_t stages;
    //! \details
    //! Pointer to an array of DF1 filter coefficients of length stages. This
    //! data block must be allocated in shared RAM when using LEA.
    const msp_biquad_df1_q15_coeffs *coeffs;
    //! \details
    //! Pointer to an array of DF1 filter states of length stages. When
    //! continuous operation is desired the previous states must be passed to
    //! the next cascaded biquad operation. This data block must be allocated in
    //! shared RAM when using LEA.
    msp_biquad_df1_q15_states *states;
} msp_biquad_cascade_df1_q15_params;


int msp_fill_q15(const msp_fill_q15_params *params, _q15 *dst);
int msp_biquad_df1_q15(const msp_biquad_df1_q15_params *params, const _q15 *src, _q15 *dst);
int msp_biquad_cascade_df1_q15(const msp_biquad_cascade_df1_q15_params *params, const _q15 *src, _q15 *dst);

#endif //__DSPLIB_FILTER_H__
