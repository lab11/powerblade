#!/usr/bin/env python3

import serial
import struct
import numpy as np
from matplotlib import pyplot as plt

r_fft = {}
raw = []
with serial.Serial('/dev/ttyUSB0', 115200) as s:
    for x in range(2):
        while(1):
            header = s.read()
            [x] = struct.unpack('B', header)
            if x == 0xAA:
                header = s.read()
                [y] = struct.unpack('B', header)
                if y == 0xBB:
                    print('found')
                    length = s.read(4)
                    [length] = struct.unpack('<I', length)
                    print(int(length/4))
                    name = str(int(length/4))
                    r_fft[name] = []
                    for x in range(int(length/4)):
                        [y] = struct.unpack('<f', s.read(4))
                        r_fft[name].append(y)
                    print("done")
                    break
                if y == 0xCC:
                    print('found')
                    length = s.read(4)
                    [length] = struct.unpack('<I', length)
                    print(int(length/4))
                    for x in range(int(length/4)):
                        [y] = struct.unpack('<f', s.read(4))
                        raw.append(y)
                    print("done")
                    break
plt.figure(figsize=(11,8))
for length in sorted(r_fft, key=lambda x: int(x), reverse=True):
    a = np.asarray(r_fft[length])
    np.savetxt('magnitude_fft_'+length+'.csv', a)
    plt.plot([42*60 / float(length) * x for x in range(int(float(length)/2))], r_fft[length][:int(float(length)/2)], label=length)
plt.title('FFT Frequency Bins')
plt.xticks(list(plt.xticks()[0]) + [60])
plt.xlabel('Frequency (Hz)')
plt.legend(title='FFT Size')
plt.savefig('fft_bins.pdf')

plt.figure(figsize=(11,8))
plt.plot([x/(42*60) for x in range(len(raw))], raw)
plt.title('Integrated Current (Powerblade method)')
plt.xlabel('Time')
plt.savefig('integrated_current.pdf')
