Calibration Curve Generation
============================

Generate a calibration curve for different power/power factors using a Chroma
63802 Load Emulator.

### Installation

Install pyvisa and pyvisa-py:
```
pip3 install pyvisa pyvisa-py
```

Install dependencies for pyvisa-py:
```
pip3 install pyserial
```

Check that the serial interface for pyvisa-py is installed:
```
python3 -m visa info
```
Part of the output should indicate serial is installed:
```
ASRL INSTR: Available via PySerial (3.4)
```

### Usage

```
python3 generate_calibration_curve.py
```
