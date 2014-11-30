/* -*- c++ -*- */
/* 
 * Copyright 2014 <+YOU OR YOUR COMPANY+>.
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "ByteToPseudoUARTi_impl.h"

namespace gr {
  namespace PowerBlade_Utils {

    ByteToPseudoUARTi::sptr
    ByteToPseudoUARTi::make(int withTimingBit,
                            int rearPaddingBits,
                            int rearPauseBits,
                            int symbolsPerBlock,
                            int blockPause)
    {
      return gnuradio::get_initial_sptr
        (new ByteToPseudoUARTi_impl(withTimingBit,rearPaddingBits,rearPauseBits,
                                    symbolsPerBlock,blockPause));
    }

    /*
     * The private constructor
     */
    ByteToPseudoUARTi_impl::ByteToPseudoUARTi_impl(int withTimingBit,
                                                   int rearPaddingBits,
                                                   int rearPauseBits,
                                                   int symbolsPerBlock,
                                                   int blockPause)
      : gr::sync_interpolator("ByteToPseudoUARTi",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
                1 + (withTimingBit ? 1 : 0) + 8 + rearPaddingBits + rearPauseBits)
    {
      timingBit = (withTimingBit ? 1 : 0); 
      rearPadding = rearPaddingBits; 
      rearPause = rearPauseBits;
      totalLength = 1 + timingBit + 8 + rearPadding + rearPause;
   }

    /*
     * Our virtual destructor.
     */
    ByteToPseudoUARTi_impl::~ByteToPseudoUARTi_impl()
    {
    }

    int
    ByteToPseudoUARTi_impl::work(int noutput_items,
			  gr_vector_const_void_star &input_items,
			  gr_vector_void_star &output_items)
    {
        const uint8_t *in = (const uint8_t *) input_items[0];
        uint8_t *out = (uint8_t *) output_items[0];

        // Do
        int ninput_items = noutput_items / totalLength;
  
        for(int i = 0;i < ninput_items;i++){
           int start_ind = i * totalLength;
           int c = 0;
           out[start_ind + c++] = 0; 
           if(timingBit){
              out[start_ind + c++] = 1;
           } 
           for(int j = 0;j < 8;j++){
              out[start_ind + c++] = 1 & (in[i] >> j);
           } 
           for(int j = 0;j < rearPadding;j++){
              out[start_ind + c++] = 0;
           }
           for(int j = 0;j < rearPause;j++){
              out[start_ind + c++] = 1;
           }  
        }

        // Tell runtime system how many output items we produced.
        return noutput_items;
    }

  } /* namespace PowerBlade_Utils */
} /* namespace gr */

