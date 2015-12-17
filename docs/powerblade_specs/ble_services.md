PowerBlade BLE Services
=======================

## PowerBlade Configuration

## Calibration


## Raw Samples
0x2A89 - Begin Raw Sample Collection

    Boolean: Write

    Set to true (nonzero) to start raw sample collection
    Set to false (zero) to stop raw sample collection

0x2A8A - Raw Sample Values

    uint8_t buffer: Read

    Contains raw sample values from the MSP430
    Set to length 1 when no data is available
    Set to length from 1 to 504 when data is available
    Nominally, data is passed in 504-byte chunks, with the last chunk of arbitrary size


0x2A8B - Collection Status

    uint8_t: Read, Write, Notify

    Contains current status of raw sample collection
        0 - raw sample collection is pending (waiting for new data from MSP430)
        1 - raw sample collection is running and data is available
        2 - raw sample collection has completed successfully
        255 - raw sample collection has been stopped

    Write any value to request next data chunk

    Notifies whenever new data is available (1) or data collection is complete (2)

### Method of Operation:
Enable notifications on `Collection Status`. Next, write 0x01 to `Begin Raw Sample Collection`. On notification value 0x01, read raw sample chunk from `Raw Sample Values`. Write 0x01 to `Collection Status`. Repeat reading and writing until sent notification value 0x02 at which point all data is collected.
