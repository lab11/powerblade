import pyvisa
import time
import argparse
import struct
import numpy as np
from bluepy.btle import ScanEntry, Scanner, DefaultDelegate
from chroma63800 import Chroma63800

COMPANY_ID = 0x2e0

num_pf = 0
num_power = 0
power_factors = np.arange(0, 1.1, .1)
powers = np.logspace(50, 1000, 20)

# Parse args and get Chroma device
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--device", help="VISA device string to connect to")
parser.add_argument('addr', metavar='A', type=str, help='Address of the form XX:XX:XX:XX:XX:XX')
args = parser.parse_args()
addr = args.addr.lower()
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

# Set up BLE scanning
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    # when this python script discovers a BLE broadcast packet from a buckler
    # advertising light measurements, print out the data
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr == addr:
            print("Found advertisement from: ", str(dev.addr))
            print("Name: " + str(dev.getValueText(ScanEntry.COMPLETE_LOCAL_NAME)))
            data = dev.getValue(ScanEntry.MANUFACTURER)
            if data is None: return

            print("Data: " + str(data.hex()))
            [company_id] = struct.unpack('<h', data[:2])
            if company_id != COMPANY_ID:
                print('incorrect company id')
                return
            data = data[3:]
            if len(data) != 19:
                print('Bad powerblade packet')
                return
            [version, seq_no, pscale, vscale, whscale, v_rms, real_power, \
                    apparent_power, watt_hours, flags] = \
            struct.unpack(">BIHBBBHHIB", data)
            print(hex(version))
            print(hex(seq_no))
            print(hex(pscale))
            print(hex(vscale))
            print(hex(whscale))
            print(hex(v_rms))
            print(hex(real_power))
            print(hex(apparent_power))
            print(hex(watt_hours))
            print(hex(flags))

            if (version == 1):
                volt_scale = vscale / 50
            else:
                volt_scale = vscale / 200
            power_scale = (pscale & 0xFFF) * pow(10, -1 * (pscale >> 12))

            v_rms_disp = v_rms * volt_scale
            real_power_disp = real_power * power_scale
            app_power_disp = apparent_power * power_scale
            if(volt_scale > 0):
                watt_hours_disp = watt_hours * pow(2, whscale)*(power_scale/3600);
            else:
                watt_hours_disp = watt_hours

            print("voltage (rms):", v_rms_disp)
            print("real power:", real_power_disp)
            print("apparent power:", app_power_disp)
            print("power factor:", real_power_disp/app_power_disp)
            print("watt hours:", watt_hours_disp)


scanner = Scanner().withDelegate(ScanDelegate())
scanner.start()

measurements = np.zeros((len(power_factors), len(powers), 3))

chroma.set_power(1000)
chroma.set_pf(1)
chroma.load_on()
chroma.load_off()

while(1):
    scanner.process()

