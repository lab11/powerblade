BLE Advertisement Protocol
==========================

PowerBlade broadcasts data over Bluetooth Low Energy advertisements. Advertisements are sent five times per second, with varying content. Four are data packets, and one is an eddystone URL packet. Data packets include real-time power measurements, total energy consumption, and calibration scaling values, and are updated with new measurements once per second. Eddystone URL packets point to a [Summon](https://github.com/lab11/summon) UI for reading data from the PowerBlade via a smartphone.


## Data Packet Format
*Protocol Version 1*

| **Field**      | Version | Sequence | P_scale | V_scale | WH_scale | V_RMS |
|:--------------:|:-------:|:--------:|:-------:|:-------:|:--------:|:-----:|
| **Byte Index** | 0       | 1-4      | 5-6     | 7       | 8        | 9     |

| Real Power | Apparent Power | Energy Use | Flags |
|:----------:|:--------------:|:----------:|:-----:|
| 10-11      | 12-13          | 14-17      | 18    |

Data packets are sent four times per second (at 200 ms intervals, with a gap for the Eddystone URL packet). Data values are updated once per second. The redundancy in data packets allows for a better probability of receiving the measurement.

Data fields are as follows:
 * **Version**: Protocol version number
 * **Sequence**: Sequence number incremented each packet. Used to detect duplicate data
 * **P_scale**: Power scaling value, see below
 * **V_scale**: Voltage scaling value, see below
 * **WH_scale**: Watt Hour scaling value, see below
 * **V_RMS**: RMS line voltage (typically 120 V in the United States), unscaled
 * **Real Power**: Real power measurement in Watts, unscaled
 * **Apparent Power**: Apparent power measurement in Volt Amps, unscaled
 * **Energy Use**: Energy use measurement in Watt Hours, unscaled
 * **Flags**: Additional flags set by the system (currently unused)

### Scaling Values
In order to simplify computation required on the MSP430, some scaling is pushed off to the receiver. `V_RMS`, `Real Power`, `Apparent Power`, and `Energy Use` must all be scaled.

`P_scale` is broken down into a 12-bit `P_scale_base` and a 4-bit `P_scale_exponent`.

    `P_scale_base` = (`P_scale` & 0x0FFF)
    `P_scale_exponent` = (`P_scale` >> 12)

The scaling factors are:

    `Voltage Scale` = `V_scale` / 50

    `Power Scale` = `P_scale_base` * pow(10, (-1 * `P_scale_exponent`))
                                    [10 to the (-1 * `P_scale_exponent`) power]

    `WattHours Scale` = `Power_scale` * (2 << `WH_scale`) / 3600
                                        [2 to the `WH_scale` power]


To calculate scaled `V_RMS`:

    `V_RMS Final` = `V_RMS` * `Voltage Scale`

To calculate scaled `Real Power`:

    `Real Power Final` = `Real Power` * `Power Scale`

To calculate scaled `Apparent Power`:

    `Apparent Power Final` = `Apparent Power` * `Power Scale`

To calculate scaled `Energy Use`:

    `Energy Use Final` = `Energy Use` * `WattHours Scale`

Power factor is not transmitted as it can be determined from the already transmitted values.
To calculate `Power Factor`:

    `Power Factor Final` = `Real Power` / `Apparent Power`

### Example Packet
| **Field** | Version | Sequence   | P_scale | V_scale | WH_scale | V_RMS |
|:---------:|:-------:|:----------:|:-------:|:-------:|:--------:|:-----:|
| **Value** | 0x01    | 0x00000001 | 0x424A  | 0x7B    | 0x09     | 0x31  |

| Real Power | Apparent Power | Energy Use | Flags |
|:----------:|:--------------:|:----------:|:-----:|
| 0x0802     | 0x0A1A         | 0x0000010D | 0x00  |

Protocol is version 1.

In this example:
 * `V_scale` is 123 (0x7B). `Voltage Scale` is 123 / 50 = 2.46
 * `P_scale` is 0x424A. `P_scale_base` is 0x24A and `P_scale_exponent` is 0x4.
     * `Power Scale` is 586 * 0.0001 = 0.0586
 * `WH_scale` is 0x09. `WattHours Scale` is 0.0586 * 512 / 3600 = 0.008334
 * `Voltage` is 49 * 2.46 = 120.54 Volts
 * `Real Power` is 2050 * 0.0586 = 120.130 Watts
 * `Apparent Power` is 2586 * 0.0586 = 151.540 Volt Amps
 * `Energy Use` is 269 * 0.008334 = 2.242 Watt Hours
 * `Power Factor` is 210.130 / 151.540 = 0.79


## Eddystone Packet Format