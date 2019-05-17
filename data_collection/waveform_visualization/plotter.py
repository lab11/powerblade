#! /usr/bin/env python3

import matplotlib.pyplot as plt
import sys

# Create a function called "chunks" with two arguments, l and n:
def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]

print("Starting...")
plt.ion()
f, axarr = plt.subplots(2, sharex=True)

axarr[0].set_ylim(-1, 1)
axarr[0].set_title('Voltage')
voltage_plot, = axarr[0].plot([0]*42)

axarr[1].set_ylim(-1, 1)
axarr[1].set_title('Current')
current_plot, = axarr[1].plot([0]*42)
plt.show(block=False)
plt.pause(1E-17)

try:
    for line in sys.stdin:
        data = bytearray.fromhex(line[:-1])

        if len(data) != 2*42+2*42:
            print("Got bad data")
            continue

        # pull out current data
        current_data = []
        for byte_values in chunks(data[:2*42], 2):
            current_data.append(int.from_bytes(byte_values, byteorder='big', signed=True))

        # normalize current data
        current_max = max([abs(item) for item in current_data])
        current_data = [item/current_max for item in current_data]

        # pull out voltage data
        voltage_data = []
        for byte_values in chunks(data[2*42:], 2):
            voltage_data.append(int.from_bytes(byte_values, byteorder='big', signed=True))

        # normalize voltage data
        voltage_max = max([abs(item) for item in voltage_data])
        voltage_data = [item/voltage_max for item in voltage_data]

        # update plot
        print("Updating plot")
        voltage_plot.set_ydata(voltage_data)
        current_plot.set_ydata(current_data)
        plt.draw()
        plt.pause(1E-17)

except Exception as e:
    print(e)
    sys.exit(1)

# keep plot shown when quitting
plt.show()
