#!/usr/bin/env python3

import serial
import struct
import numpy as np
from matplotlib import pyplot as plt

r_fft = {}
c_fft = {}
with serial.Serial('/dev/ttyUSB0', 115200) as s:
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
plt.figure(figsize=(11,8))
for length in sorted(r_fft, key=lambda x: int(x), reverse=True):
    a = np.asarray(r_fft[length])
    np.savetxt('magnitude_fft_'+length+'.csv', a)
    plt.plot([42*60 / float(length)/2 * x for x in range(int(len(r_fft[length])))], r_fft[length], label=length)
plt.title('FFT Frequency Bins')
plt.xlim(0,600)
plt.xticks(list(plt.xticks()[0]) + [60])
plt.xlabel('Frequency (Hz)')
plt.legend(title='FFT Size')
plt.savefig('fft_bins.pdf')
