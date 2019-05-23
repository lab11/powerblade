#! /usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

a = np.loadtxt("recreate_data.txt", dtype=int, delimiter=',')[42:]
raw_v = a[:,1]
raw_i = a[:,2]
og = a[:,3]
v = a[:,4]
c = a[:,5]

plt.plot(raw_v/np.linalg.norm(raw_v), label='raw v')
#plt.plot(raw_i/np.linalg.norm(raw_i), label='raw di/dt')
plt.plot(og/np.linalg.norm(og), label='current')
plt.plot(v/np.linalg.norm(v), label='filtered voltage')
plt.plot(c/np.linalg.norm(c), label='filtered current')
plt.legend()
plt.show()
