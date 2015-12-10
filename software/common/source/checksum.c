#include <stdint.h>
#include "checksum.h"

uint8_t additive_checksum(uint8_t const* data, uint16_t len) {
    uint16_t sum = 0;
    uint16_t index = 0;

    while (index < len) {
        sum += data[index];
        index++;
    }

    // roll over carries to compute 1's complement sum
    //  First add in carries from inital summing
    //  Second add in any additional carries that caused
    sum = (sum >> 8) + (sum & 0xFF);
    sum += (sum >> 8);

    // invert the result so that all zero data does not have a zero checksum
    return (uint8_t)((~sum) & 0xFF);
}

