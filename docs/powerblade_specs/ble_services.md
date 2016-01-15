PowerBlade BLE Services
=======================

## PowerBlade Configuration

## Configuration
Device Configuration Service
    Full UUID: 50804da1-b988-f888-ec43-b957e5acf999
    Short UUID: 0x4DA1

    Allows calibration of the scaling values on the device and viewing of the device's
    current status. Used for testing and development as well as device-specific
    calibration at manufacturing time.

0x4DA2 - Device Status

    uint8_t: Read, Notify

    Internal status codes for various states and errors of the PowerBlade

0x4DA3 - Voltage Offset Configuration

    uint8_t: Read, Write

    Offset to apply to each voltage ADC reading. Used for device calibration

0x4DA4 - Current Offset Configuration

    uint8_t: Read, Write

    Offset to apply to each current ADC reading. Used for device calibration

0x4DA5 - Power Scale Configuration

    uint8_t: Read, Write

    Scaling value used to determine power readings. Used for device calibration. Transmitted over advertisements to users

0x4DA6 - Voltage Scale Configuration

    uint8_t: Read, Write

    Scaling value used to determine voltage readings. Used for device calibration. Transmitted over advertisements to users

0x4DA7 - Watt-Hours Scale Configuration

    uint8_t: Read, Write

    Scaling value used to determine watt-hours readings. Used for device calibration. Transmitted over advertisements to users

## Sample Collection
Raw Sample Data Collection Service
    Full UUID: cead01af-7cf8-cc8c-1c4e-882a39d41531
    Short UUID: 0x01AF

    Allows collection of raw voltage and current samples from a PowerBlade. Used for
    testing and development as well as device-specific calibration at manufacturing time

0x01B0 - Begin Sample Collection

    Boolean: Write

    Set to true (nonzero) to start raw sample collection
    Set to false (zero) to stop raw sample collection

0x01B1 - Raw Sample Values

    uint8_t buffer: Read

    Contains raw sample values from the MSP430
    Set to length 1 when no data is available
    Set to length from 1 to 504 when data is available
    Nominally, data is passed in 504-byte chunks, with the last chunk of arbitrary size


0x01B2 - Collection Status

    uint8_t: Read, Write, Notify

    Contains current status of raw sample collection
        0 - raw sample collection is pending (waiting for new data from MSP430)
        1 - raw sample collection is running and data is available
        2 - raw sample collection has completed successfully
        255 - raw sample collection has been stopped

    Write any value to request next data chunk

    Notifies whenever new data is available (1) or data collection is complete (2)

### Method of Operation:
Enable notifications on `Collection Status`. Next, write 0x01 to `Begin Sample Collection`. On notification value 0x01, read a raw sample chunk from `Raw Sample Values`. Write 0x01 to `Collection Status`. Repeat reading and writing until sent the notification value of 0x02 at which point all data has been collected and Sample Collection is complete.
