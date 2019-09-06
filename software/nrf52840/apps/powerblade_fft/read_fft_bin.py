#!/usr/bin/env python3

import serial
import struct
import numpy as np
from matplotlib import pyplot as plt

r_fft = {}
c_fft = {}
with serial.Serial('/dev/ttyUSB0', 115200) as s:
    for x in range(12):
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
                    print(int(length/4/2))
                    name = str(int(length/4/2))
                    c_fft[name] = []
                    for x in range(int(length/4)):
                        [y] = struct.unpack('<f', s.read(4))
                        c_fft[name].append(y)
                    print("done")
                    break
for length in sorted(c_fft, key=lambda x: int(x), reverse=True):
    print(length)
    a = np.asarray(c_fft[length])
    #plt.plot(a)
    #plt.show()
    np.savetxt('complex_fft_'+length+'.csv', a)
plt.figure(figsize=(11,8))
for length in sorted(r_fft, key=lambda x: int(x), reverse=True):
    a = np.asarray(r_fft[length])
    np.savetxt('magnitude_fft_'+length+'.csv', a)
    plt.plot([48E3 / float(length) * x for x in range(int(len(r_fft[length])))], r_fft[length], label=length)
plt.title('FFT Frequency Bins')
plt.xlabel('Frequency (Hz)')
plt.legend(title='FFT Size')
plt.savefig('fft_bins.pdf')
