PowerBlade UART Protocol
========================

UART is used for communication between the MSP430 and nRF51822 chips used on PowerBlade. The MSP430 controls power to subsystems, samples voltage and current waveforms, and sends power data to the nRF. The nRF controls BLE communication including advertisements and services. Control from users is sent from the nRF back to the MSP430.

## MSP to nRF Packet Specification

Packets are sent from the MSP430 to the nRF at 1 Hz. Each packet includes updated advertisement data, and may optionally include additional data, such as updates to BLE service values.

### Packet Format

| **Field** | Total Length | Adv Length | Adv Data | Additional Data (optional) | Checksum| 
|:-------------------:|:---:|:-:|:------------:|:---:|:---------:|
| **Number of Bytes** | 2   | 1 | `Adv Length` | ... | 1         |
| **Byte Index**      | 0-1 | 2 | 3-21+        | ... | Last Byte |

 * **Total Length**: Length of the entire UART transmission, including itself
 * **Adv Length**: Length of advertisement data field, does not include itself
 * **Adv Data**: Advertisement data. This can range from 0 to 24 bytes
 * **Additional Data**: Additional data to send to nRF. Structure defined below
 * **Checksum**: Checksum over entire packet, additive 1s complement checksum

More information on `Adv Data` format can be found in the [BLE Advertisement Protocol Specification](ble_advertisement.md). The checksum implmentation can be found in [checksum.c](https://github.com/lab11/powerblade/blob/master/software/common/source/checksum.c).

#### Example Packet

Example UART packet with advertisement data but no additional data. Advertisement fields are noted following the example from the [BLE Advertisement Protocol Specification](ble_advertisement.md).

| **Field** | Total Length | Adv Length |
|:---------:|:------------:|:----------:|
| **Value** | 0x0017       | 0x13       |

| Version | Sequence   | P_scale | V_scale | WH_scale | V_RMS | Real Power |
|:-------:|:----------:|:-------:|:-------:|:--------:|:-----:|:----------:|
| 0x01    | 0x00000001 | 0x424A  | 0x7B    | 0x09     | 0x31  | 0x0802     |

| Apparent Power | Energy Use | Flags | Checksum |
|:--------------:|:----------:|:-----:|:--------:|
| 0x0A1A         | 0x0000010D | 0x00  | 0x55     |

#### Additional Data

The additional data field can be used to transfer non-advertisement data to the nRF. This can include additional fine-grained power data or information on the device's current state.

| **Field**           | Add Data Type | Add Data Values   |
|:-------------------:|:-------------:|:-----------------:|
| **Number of Bytes** | 1             | `Add Data Length` |
| **Byte Index**      | 0             | 1-                |

 * **Add Data Type**: Type of data. Informs nRF how to interpret the data. See below
 * **Add Data Values**: Data elements. Length and interpretation depend on `Add Data Type`

Each additional data field has only a single `Add Data Type`. If the MSP430 has multiple items to be sent to the nRF, they should be sent in separate transmissions.

##### Additional Data Types

| Value | Name |
|:------|:-----|
| 0x10  | Calibration State |
| 0x20  | Sample Data |

 * **Calibration State**: Current state of device calibration. More details can be found at [Calibration Protocol](calibration.md)
 * **Sample Data**: Individual samples from one second of power sampling


## nRF to MSP Packet Specification

Packets are sent from the nRF to the MSP430 asynchronously based on interactions with the user over BLE, only one nRF to MSP430 packet may be sent per second. Packets include information such as changes to device state (e.g. enter calibration mode) or parameter changes to the device.

### Packet Format

| **Field**           | Total Length | Data Type | Data Values   | Checksum  | 
|:-------------------:|:------------:|:---------:|:-------------:|:---------:|
| **Number of Bytes** | 2            | 1         | `Data Length` | 1         |
| **Byte Index**      | 0-1          | 2         | 3-            | Last Byte |

 * **Total Length**: Length of packet, including itself
 * **Data Type**: Type of data. Informs MSP430 how to interpret the data. See below
 * **Data Values**: Data elements. Length and interpretation depend on `Data Type`
 * **Checksum**: Checksum over entire packet, additive 1s complement checksum

Each packet has only a single `Data Type`. If the nRF has multiple items to be sent to the MSP430, they should be sent in separate transmissions.

##### Additional Data Types

| Value | Name |
|:------|:-----|
| 0x10  | Calibration State |
| 0x11  | Ground Truth Watts |
| 0x12  | Get CUROFF |
| 0x13  | Set CUROFF |
| 0x14  | Get P_scale |
| 0x15  | Set P_scale |
| 0x16  | Get V_scale |
| 0x17  | Set V_scale |
| 0x18  | Get WH_scale |
| 0x19  | Set WH_scale |
| 0x1A	| Set Sequence |
| 0x20  | Start Sample Data Download |
| 0x21	| Continue Sample Data Download |
| 0x22	| Send data done (MSP to nRF) |
| 0xFF	| NAK (Checksum failed) |

 * **Set Sequence**: Set the sequence number to be included in future packets
 * **Calibration State**: Set current state of device calibration. More details can be found at [Calibration Protocol](calibration.md)
 * **Ground Truth Watts**: Active real power that the system should register. Used for calibration. More details can be found at [Calibration Protocol](calibration.md)
 * **Get/Set X**: Getters and Setters for various calibration values
 * **Get Sample Data**: Get individual samples from one second of power sampling
 * **NAK**: nRF indicating checksum of previous message failed

#### Example Packet

Example UART packet with a `Ground Truth Watts` type and a wattage value of 200 Watts. 

| **Field** | Total Length | Data Type | Data Values | Checksum |
|:---------:|:------------:|:---------:|:-----------:|:--------:|
| **Value** | 0x0006       | 0x11      | 0x00C8      | 0x20     |
