import pyvisa
import time
import argparse
from chroma63800 import Chroma63800

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--device", help="VISA device string to connect to")
args = parser.parse_args()
device = None
if args.device is not None:
    device = args.device
else:
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    print("Select resource:")
    inst = None
    choice = -1
    while not (choice < len(resources) and choice >= 0):
        for i, resource in enumerate(resources):
            print(str(i+1) + '.', resource)
        choice = int(input("Selection: ")) - 1
        if not (choice < len(resources) and choice >= 0): print("Invalid selection")
        else:
            device = resources[choice]

chroma = Chroma63800(device, 15)

chroma.set_power(1000)
chroma.set_pf(1)
chroma.load_on()
time.sleep(5)
print(chroma.measure_all())
time.sleep(10)
chroma.load_off()
#inst.write(':SYST:SET:CFPF:MODE PF')
#inst.write(':LOAD:ABA ON')
#inst.write(':LOAD:CURR:PEAK:MAX 10')
#print(inst.query(':LOAD?'))
#inst.write(':LOAD:MODE POW')
#inst.write(':PFAC .5')
#print(inst.query(':PFAC?'))
#print(inst.query(':LOAD:MODE?'))
#inst.write(':LOAD:POW 75')
#inst.write(':LOAD ON')
#
#time.sleep(5)
#print(inst.query(':MEAS:POW?'))
#print(inst.query(':MEAS:POW:PFAC?'))
#print(inst.query(':MEAS:VOLT?'))
#time.sleep(5)
#
#inst.write(':LOAD OFF')
