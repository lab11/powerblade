#!/usr/bin/env python3

import math
import numpy as np
import scipy.fftpack as fft
import matplotlib.pyplot as plt

samples_sec = 2520

# load powerblade trace
pb = np.loadtxt('realSamples.dat', float,)
pb[:,0] = pb[:,0]/samples_sec

# load ground truth trace
gt = np.loadtxt('scope_1.csv', float, delimiter=',', skiprows=2)

# get zero crossings
pb_zero = np.where(np.diff(np.sign(pb[:,-1])))[0]
gt_zero = np.where(np.diff(np.sign(gt[:,-1])))[0]

gt_start = gt[0,0]
pb = pb[pb_zero[0]:]
gt = gt[gt_zero[0]:]
#plt.plot(pb[:,0], pb[:,-1])
#plt.plot(gt[:,0] - gt_start, gt[:,-1])
#plt.show()

def ema_calculate_alpha(fs, fc):
    a = math.sqrt(math.cos(2*math.pi*fc/fs)**2 - 4*math.cos(2*math.pi*fc/fs) + 3) + math.cos(2*math.pi*fc/fs) - 1
    return(a)

def ema_highpass(samples, a):
    s = 0
    h = []
    for x in samples:
        s = a*x + (1-a)*s
        h.append(x - s)
    return h

alpha = ema_calculate_alpha(42*60, 30)
print(alpha)

#plt.plot(pb[:,0], pb[:,-1])
filtered = ema_highpass(pb[:,-1], alpha)
filtered.reverse()
filtered = ema_highpass(filtered, alpha)
filtered.reverse()
plt.plot(gt[:,0] - gt_start, gt[:,-1], color='C2', linewidth=0.5)
plt.plot(pb[:,0], 1.5*np.array(filtered), color='C0')
plt.plot(pb[:,0], pb[:,-1], color='C1')
plt.show()


def perfect():
    yf = fft.fft(pb[:,-1])/pb.shape[0]
    xf = np.linspace(0, samples_sec, yf.shape[0])

    #plt.plot(xf, np.abs(yf))
    #plt.show()

    cut_index = int(58 * pb.shape[0] / samples_sec)
    blow_out = yf
    blow_out[:cut_index] = 0
    blow_out[pb.shape[0] - cut_index :] = 0
    y = pb.shape[0]*fft.ifft(blow_out)

    plt.plot(gt[:,0] - gt_start, gt[:,-1], color='C2', linewidth=0.5)
    plt.plot(pb[:,0],y, color='C0')
    plt.plot(pb[:,0],pb[:,-1], color='C1')
    plt.show()

