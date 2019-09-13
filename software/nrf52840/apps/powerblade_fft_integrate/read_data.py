#!/usr/bin/env python3

import serial
import struct
import numpy as np
from matplotlib import pyplot as plt

raw = []
integrated = []
integrated_z = []
with serial.Serial('/dev/ttyUSB0', 115200) as s:
    for x in range(3):
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
                    for x in range(int(length/4)):
                        [y] = struct.unpack('<f', s.read(4))
                        raw.append(y)
                    print("done")
                    break
                if y == 0xCC:
                    print('found')
                    length = s.read(4)
                    [length] = struct.unpack('<I', length)
                    print(int(length/4))
                    for x in range(int(length/4)):
                        [y] = struct.unpack('<f', s.read(4))
                        integrated.append(y)
                    print("done")
                    break
                if y == 0xDD:
                    print('found')
                    length = s.read(4)
                    [length] = struct.unpack('<I', length)
                    print(int(length/4))
                    for x in range(int(length/4)):
                        [y] = struct.unpack('<f', s.read(4))
                        integrated_z.append(y)
                    print("done")
                    break
#plt.figure(figsize=(11,8))
#for length in sorted(r_fft, key=lambda x: int(x), reverse=True):
#    a = np.asarray(r_fft[length])
#    np.savetxt('magnitude_fft_'+length+'.csv', a)
#    plt.plot([42*60 / float(length) * x for x in range(int(float(length)/2))], r_fft[length][:int(float(length)/2)], label=length)
#plt.title('FFT Frequency Bins')
#plt.xticks(list(plt.xticks()[0]) + [60])
#plt.xlabel('Frequency (Hz)')
#plt.savefig('fft_bins.pdf')
raw = raw / np.mean(np.abs(raw))
integrated = integrated / np.mean(np.abs(integrated))
integrated_z = integrated_z / np.mean(np.abs(integrated_z))
plt.figure(figsize=(11,8))
plt.plot([x/(42*60) for x in range(len(raw))], raw, label='raw')
plt.plot([x/(42*60) for x in range(len(integrated))], integrated, label='integrated')
plt.plot([x/(42*60) for x in range(len(integrated_z))], integrated_z, label='integrated_filtered')
plt.title('Integration in frequency domain')
plt.xlabel('Time')
plt.xlim((0, 10/60))
plt.legend()
plt.savefig('current.pdf')

#plt.figure(figsize=(11,8))
#plt.plot([x/(42*60) for x in range(len(integrated))], integrated)
#plt.title('Integrated Current (fft method)')
#plt.xlabel('Time')
#plt.savefig('integrated_current.pdf')
