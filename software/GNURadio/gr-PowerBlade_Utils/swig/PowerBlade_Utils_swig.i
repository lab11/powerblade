/* -*- c++ -*- */

#define POWERBLADE_UTILS_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "PowerBlade_Utils_swig_doc.i"

%{
#include "PowerBlade_Utils/ByteToPseudoUARTi.h"
%}

%include "PowerBlade_Utils/ByteToPseudoUARTi.h"
GR_SWIG_BLOCK_MAGIC2(PowerBlade_Utils, ByteToPseudoUARTi);
