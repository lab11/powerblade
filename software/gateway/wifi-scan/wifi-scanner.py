#!/usr/bin/env python

from scapy.all import *
import time
import signal
import sys
import os
from threading import Thread
import Queue
import urllib2
import json
import httplib
import re
import subprocess

if os.geteuid() != 0:
    print('Root privileges needed to run scans.')
    sys.exit(1)

def main():
    
    # create a csv file for writing to
    f = open('/home/nuc/wifi.csv', 'a+')

    scanner = WiFiScanner(f)

    while True:
        # move to next channel down the line
        scanner.hop()
        # collect 10 seconds of data at a time
        scanner.sniff(10)


class WiFiScanner():
    # Possible wifi channels for scanning
    wifi_channels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                    # Sam's nuc doesn't do channel 14
                    #14,
                    ]
                    # Only 1-14 are relevant for BLE conflicts
                    #36, 38, 40, 44, 46, 48,
                    #149, 151, 153, 157, 159, 161, 165]

    def __init__(self, csv_file):
        self.csv_file = csv_file

        self.channel_index = -1
        self.last_packet = time.time()
        self.packet_count = []
        for index in range(len(self.wifi_channels)):
            self.packet_count += [{'duration': 0.0, 'packets': 0.0, 'bytes': 0.0}]

        # need to set wlan0 into monitor mode
        self._reset_wlan0()

    def _reset_wlan0(self):
        self.last_packet = time.time()

        # attempt to configure the wireless card
        print("configuring interface")
        if (os.system("ifconfig wlan0 down") != 0):
            print(cur_datetime() + "Error: Error taking wlan0 down")
            sys.exit(1)
        if (os.system("iwconfig wlan0 mode monitor") != 0):
            print(cur_datetime() + "Error: Error setting wlan0 to monitor mode")
            sys.exit(1)
        if (os.system("ifconfig wlan0 up") != 0):
            print(cur_datetime() + "Error: Error bringing wlan0 up")
            sys.exit(1)
        print("complete\n")

    def _getRSSI(self, pkt):
        return (ord(pkt.notdecoded[-4:-3])-256)

    def PacketHandler(self, pkt):
        if pkt.haslayer(Dot11):
            self.last_packet = time.time()

            # got a packet, count its bytes
            self.packet_count[self.channel_index]['packets'] += 1
            self.packet_count[self.channel_index]['bytes'] += len(str(pkt))

    def completed_channel_cycle(self):
        print("\n***Completed Channel Cycle***")
        for chan_index in range(len(self.wifi_channels)):
            packets = self.packet_count[chan_index]['packets']
            packet_bytes = self.packet_count[chan_index]['bytes']
            duration = self.packet_count[chan_index]['duration']
            bps = 0
            if duration != 0:
                bps = packet_bytes/duration
            print("Channel " + str(self.wifi_channels[chan_index]) + ': ' +
                    "Total Packets=" + str(packets) + '\t' +
                    "Bytes Per Second=" + str(bps))

            # write data to csv file
            self.csv_file.write(str(self.wifi_channels[chan_index]) + ',' + str(bps) + '\n')

            # The data should be periodically zeroed out again
            self.packet_count[chan_index]['packets'] = 0
            self.packet_count[chan_index]['bytes'] = 0
            self.packet_count[chan_index]['duration'] = 0

    def hop(self):
            # hop to the next channel
            self.channel_index += 1
            if self.channel_index >= len(self.wifi_channels):
                self.channel_index = 0
                self.completed_channel_cycle()

            print(cur_datetime() + "Info: Hopping to channel " + str(self.wifi_channels[self.channel_index]))
            if (os.system("iwconfig wlan0 channel " +
                    str(self.wifi_channels[self.channel_index])) != 0):
                print(cur_datetime() + "Error: Failed to change channel! Resetting...")
                self._reset_wlan0()

    def sniff(self, timeout=1):
            # run a time-limited scan on the channel
            print(cur_datetime() + "Info: Sniffing for " + str(timeout) + " seconds")
            sniff(iface="wlan0", prn = self.PacketHandler,
                    lfilter=(lambda x: x.haslayer(Dot11)), timeout=timeout)
            self.packet_count[self.channel_index]['duration'] += timeout

            # check if the wireless device stopped working (defined as 10
            #   minutes without a single packet)
            #   _reset_wlan0 automatically resets last_packet time
            if (time.time() - self.last_packet) > 10*60:
                print(cur_datetime() + "Error: 10 minutes without a new packet. Resetting...")
                self._reset_wlan0()


def cur_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")

def sigint_handler(signum, frame):
    # exit the program if we get a CTRL-C
    print("Exiting...\n")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    main()

