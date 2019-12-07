import pyvisa
import time
import argparse
import struct
import enum
import numpy as np
from signal import signal, SIGINT
from bluepy.btle import ScanEntry, Scanner, DefaultDelegate
from chroma63800 import Chroma63800

COMPANY_ID = 0x2e0

num_measure = 0
tot_measure = 3
num_pf = 0
num_power = 0
last_seq_no = 0
power_factors = np.arange(.3, 1.1, .1)
actual_app_powers = np.zeros(power_factors.shape)
powers = np.array([10, 50, 100, 500, 1000, 1500])
actual_powers = np.zeros(powers.shape)

measurements = np.zeros((len(power_factors), len(powers), 2, 2))
measurement_list = []

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
        global num_pf
        global num_power
        global last_seq_no
        global num_measure
        global measurement_list
        global measurements
        global scanner

        if dev.addr == addr:
            print()
            #print("Found advertisement from: ", str(dev.addr))
            #print("Name: " + str(dev.getValueText(ScanEntry.COMPLETE_LOCAL_NAME)))
            data = dev.getValue(ScanEntry.MANUFACTURER)
            if data is None: return

            #print("Data: " + str(data.hex()))
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

            if seq_no == last_seq_no:
                seq_no = last_seq_no
                return

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

            power_factor = real_power_disp/app_power_disp

            #print("\tvoltage (rms):", v_rms_disp)
            #print("\treal power:", real_power_disp)
            #print("\tapparent power:", app_power_disp)
            #print("\tpower factor:", real_power_disp/app_power_disp)
            #print("watt hours:", watt_hours_disp)

            real_measurements = [chroma.measure_real_power(), chroma.measure_apparent_power()]
            pb_measurements = [real_power_disp, app_power_disp]
            print(real_measurements)
            print(pb_measurements)

            if len(measurement_list) < tot_measure:
                measurement_list.append([real_measurements, pb_measurements])
                print(np.array(measurement_list))


def handler(signal_received, frame):
    chroma.load_off()
    exit(-1)

scanner = Scanner().withDelegate(ScanDelegate())

if __name__ == '__main__':
    signal(SIGINT, handler)

    previous_power = 0
    previous_pf = 0

    chroma.set_power(powers[num_power])
    chroma.set_pf(power_factors[num_pf])
    chroma.load_on()

    time.sleep(4)
    scanner.start()

    while(1):
        if len(measurement_list) >= tot_measure:
            #scanner.stop()
            scanner.clear()

            mean = np.mean(np.array(measurement_list), axis=0)
            print('Mean:', mean)
            measurements[num_pf, num_power] = mean
            chroma.load_off()
            exit()

        scanner.process()
