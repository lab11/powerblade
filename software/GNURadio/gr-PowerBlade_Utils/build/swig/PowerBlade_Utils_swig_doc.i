
/*
 * This file was automatically generated using swig_doc.py.
 *
 * Any changes to it will be lost next time it is regenerated.
 */




%feature("docstring") gr::PowerBlade_Utils::ByteToPseudoUARTi "Takes bytes being sent in and converts them into a series of 0 and 1 samples that represent the UART encoding of the thing."

%feature("docstring") gr::PowerBlade_Utils::ByteToPseudoUARTi::make "Return a shared_ptr to a new instance of PowerBlade_Utils::ByteToPseudoUARTi.

To avoid accidental use of raw pointers, PowerBlade_Utils::ByteToPseudoUARTi's constructor is in a private implementation class. PowerBlade_Utils::ByteToPseudoUARTi::make is the public interface for creating new instances.

Params: (withTimingBit, rearPaddingBits, rearPauseBits, symbolsPerBlock, blockPause)"