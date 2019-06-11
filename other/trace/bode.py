#!/usr/bin/env python3

from scipy.signal import sosfreqz, iirdesign
import matplotlib.pyplot as plt
from math import pi, acos
import numpy as np

frequency = 2520

sos = iirdesign(50, 10, 1, 20, ftype='butter', output='sos',fs=frequency)
print(sos)

coeffs = np.array([[0.906868893695387, -1.813737787390775, 0.906868893695387, 1, 1.865603346994032, -0.870834579919949],[0.999969481490524, -2.0, 0.999969481490524, 1, 1.938957352652234, -0.944394273400414]])
print(coeffs.shape)

#x = (alpha**2 + 2*alpha - 2) / (2*alpha - 2)
#w_c = acos(x)                          # Calculate the cut-off frequency

w, h = sosfreqz(sos)                     # Calculate the frequency response

plt.subplot(2, 1, 1)                   # Plot the amplitude response
plt.suptitle('Bode Plot')
plt.plot(w*frequency/(2*pi), 20 * np.log10(abs(h)))     # Convert to dB
plt.ylabel('Magnitude [dB]')
#plt.xlim(0, pi)
plt.ylim(-100, 1)
#plt.axvline(w_c, color='red')
#plt.axhline(-3, linewidth=0.8, color='black', linestyle=':')

plt.subplot(2, 1, 2)                   # Plot the phase response
plt.plot(w*frequency/(2*pi), 180 * np.angle(h) / pi)    # Convert argument to degrees
plt.xlabel('Frequency [Hz]')
plt.ylabel('Phase [°]')
#plt.xlim(0, pi)
#plt.ylim(-90, 90)
#plt.yticks([-90, -45, 0, 45, 90])
#plt.axvline(w_c, color='red')
plt.show()
