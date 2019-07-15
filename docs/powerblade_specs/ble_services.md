PowerBlade BLE Services
=======================

## Configuration
Device Configuration Service

    Full UUID: 50804da1-b988-f888-ec43-b957e5acf999
    Short UUID: 0x4DA1

    Allows calibration of the scaling values on the device and viewing of the
    device's current status. Used for testing and development as well as
    device-specific calibration at manufacturing time.

0x4DA2 - Device Status

    uint8_t: Read, Notify

    Internal status codes for various states and errors of the PowerBlade

0x4DA3 - Voltage Offset Configuration

    uint8_t: Read, Write

    Offset to apply to each voltage ADC reading. Used for device calibration

0x4DA4 - Current Offset Configuration

    uint8_t: Read, Write

    Offset to apply to each current ADC reading. Used for device calibration

0x4DA5 - Current Offset Post-Integration Configuration

    uint8_t Read, Write

    Offset to apply to each current measurement post-integration. Used for
    device calibration

0x4DA6 - Power Scale Configuration

    uint8_t: Read, Write

    Scaling value used to determine power readings. Used for device calibration.
    Transmitted over advertisements to users

0x4DA7 - Voltage Scale Configuration

    uint8_t: Read, Write

    Scaling value used to determine voltage readings. Used for device
    calibration. Transmitted over advertisements to users

0x4DA8 - Watt-Hours Scale Configuration

    uint8_t: Read, Write

    Scaling value used to determine watt-hours readings. Used for device
    calibration. Transmitted over advertisements to users

## Self Calibration
Calibration Control Service

    Full UUID: 57c4ed0b-9461-d99e-844e-d5aa70304b49
    Short UUID: 0xED0B

    Runs internal calibration of measurements on the MSP430. Used for
    device-specific calibration at manufacturing time

0xED0C - Wattage Setpoint

    uint16_t: Read, Write

    Real power wattage value the PowerBlade is attached to measured in
    tenths of watts

0xED0D - Voltage Setpoint

    uint16_t: Read, Write

    RMS voltage value the PowerBlade is attached to measured in tenths of volts

0xED0E - Calibration Control and Status

    uint8_t: Read, Write, Notify

    Control of and status from calibration.
    When calibration is not running, writing any value begins the process.
    Writing any value while calibration is running cancels the procedure. While
    running, the value is set to 1 after calibration has started and as it
    continues. When complete, the value is set to 2.

### Method of Operation:
Install PowerBlade on a load with known wattage and voltage. Write wattage
value to `Wattage Setpoint` and voltage value to `Voltage Setpoint` both as
tenths of their respective units. Enable notifications on
`Calibration Control and Status`. Write a value of 1 to
`Calibration Control and Status`. Wait until a notification value of 2 arrives
from `Calibration Control and Status`. Calibration is now complete. If desired,
the specific calibration values can be read from the
`Device Configuration Service`.

## Sample Collection
Raw Sample Data Collection Service

    Full UUID: cead01af-7cf8-cc8c-1c4e-882a39d41531
    Short UUID: 0x01AF

    Allows collection of raw voltage and current samples from a PowerBlade. Used
    for testing and development as well as device-specific calibration at
    manufacturing time

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
Enable notifications on `Collection Status`. Next, write 0x01 to
`Begin Sample Collection`. On notification value 0x01, read a raw sample chunk
from `Raw Sample Values`. Write 0x01 to `Collection Status`. Repeat reading and
writing until sent the notification value of 0x02 at which point all data has
been collected and Sample Collection is complete.


## Waveform Collection
Continuous Waveform Collection Service

    Full UUID: 6171e3f1-6cda-409b-931c-a83234603b33
    Short UUID: 0xE3F1

    Allows collection of representative voltage and current 1-cycle waveforms
    every second. Used for visualizing waveforms.

0xE3F2 - Continuous Waveform Status

    uint8_t: Read, Write, Notify
    Indicates if waveform available to be read. Write to clear.

0xE3F2 - Continuous Waveform Data

    uint8_t buffer: Read
    Contains voltage and integrated current waveforms. Data is available if
    status is 1. Data is in the format of a struct waveform_t:

        typedef struct {
            uint16_t adv_len;
            uint8_t adv_payload[24];
            uint16_t waveform_len;
            uint8_t waveform_payload[168];
        } waveform_t;

    The waveform payload consists of 42 uint16_t samples (84 bytes) of current
    waveform, followed by another 42 samples (84 bytes) of voltage waveform
    (total 168 bytes).

    The total size of the struct is 2 + 24 + 2 + 168 = 196 bytes.

Unique Waveform Collection Service

    Full UUID: 4e889b3d-dab2-42c3-9015-41b5391326dd
    Short UUID: 0x9B3D

    Allows collection of representative voltage and current 1-cycle waveforms
    every second. Used for visualizing waveforms.

0xE3F2 - Unique Waveform Status

    uint8_t: Read, Write, Notify
    Indicates if a unique waveform is available to be read. Write to clear.

0xE3F2 - Unique Waveform Data

    uint8_t buffer: Read
    Contains voltage and integrated current waveforms. Data is available if
    status is 1. Data is in the same format as the continuous waveform, a
    struct waveform_t

### Method of Operation:
Enable notifications on `[Continuous/Unique] Waveform Status`.
On notification value 0x01, read a waveform
from `[Continuous/Unique] Waveform Data`. Repeat reading and
writing until sent the notification value of 0 at which point all available
waveforms have been collected and Waveform Collection is complete (in the case
of Unique Waveform Collection). Continuous Waveform Collection will
continue ad infinitum.

