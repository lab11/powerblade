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


#ifndef INCLUDED_POWERBLADE_UTILS_BYTETOPSEUDOUARTI_H
#define INCLUDED_POWERBLADE_UTILS_BYTETOPSEUDOUARTI_H

#include <PowerBlade_Utils/api.h>
#include <gnuradio/sync_interpolator.h>

namespace gr {
  namespace PowerBlade_Utils {

    /*!
     * \brief  Takes bytes being sent in and converts them into a series of
     *         0 and 1 samples that represent the UART encoding of the thing. 
     * \ingroup PowerBlade_Utils
     *
     */
    class POWERBLADE_UTILS_API ByteToPseudoUARTi : virtual public gr::sync_interpolator
    {
     public:
      typedef boost::shared_ptr<ByteToPseudoUARTi> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of PowerBlade_Utils::ByteToPseudoUARTi.
       *
       * To avoid accidental use of raw pointers, PowerBlade_Utils::ByteToPseudoUARTi's
       * constructor is in a private implementation
       * class. PowerBlade_Utils::ByteToPseudoUARTi::make is the public interface for
       * creating new instances.
       */
      static sptr make(int withTimingBit,
                       int rearPaddingBits,
                       int rearPauseBits,
                       int symbolsPerBlock,
                       int blockPause);
    };
  } // namespace PowerBlade_Utils
} // namespace gr

#endif /* INCLUDED_POWERBLADE_UTILS_BYTETOPSEUDOUARTI_H */

