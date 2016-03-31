#! /usr/bin/env python3
# model percentage of packet collisions in a group of advertising BLE devices

import functools
import math
import fractions
import random
random.seed("Seed string")

####################
## configuration
####################

# debug mode gives more information on causes of collisions
debug = False

# list of BLE devices specified by
#   (count, advertising interval in ms, advertisement length in ms, new data interval in ms, number of eddystone per data interval)
devices = [
        ( 17, 1000, 1, 2000, 1),
        ( 19,  200, 1, 1000, 1),
        ]

# start all devices at the same moment or at a random time in their interval
synchronized_start = False

# random jitter introduced into actual advertisement time
#   This slowly causes the interval to slip over time
#   The current assumption is that jitter is continuous from 0
adv_jitter = 10

# duration of testing, in ms
duration = 10*60*1000


####################
## code
####################

# globals
times = []
intervals = []
lengths = []

# figure out unique data successes
data_times = []
data_intervals = []
count_per_datas = []
eddystones = []
in_eddystones = []

# iteration step
#   GCD of advertising intervals in ms
iter_step = 1

# initialization
for (count, interval, length, data_interval, eddystone) in devices:
    for i in range(count):
        if synchronized_start:
            times += [0]
        else:
            times += [random.uniform(0,interval)]
        intervals += [interval]
        lengths += [length]

        data_times += [times[-1]]
        data_intervals += [data_interval]
        count_per_datas += [0]
        eddystones += [eddystone]
        in_eddystones += [0]

# calculate actual GCD of advertising intervals
iter_step = functools.reduce(fractions.gcd, intervals)

# iterate for duration
curr_time = 0
transmissions = 0
successes = 0
unique_transmissions = 0
unique_successes = 0
while curr_time < duration:

    # increment advertisements
    updated_indices = []
    for index in range(len(times)):
        # generate new advertisements
        if curr_time > (times[index]+intervals[index]):
            times[index] += intervals[index] + random.uniform(0,adv_jitter)
            updated_indices += [index]
        # determine if advertisements have new data
        if curr_time > (data_times[index]+data_intervals[index]):
            data_times[index] += data_intervals[index]
            unique_transmissions += 1
            if count_per_datas[index] > 0:
                unique_successes += 1
            count_per_datas[index] = 0
            # we'll say that the first packets of each data are the eddystones
            in_eddystones[index] = eddystones[index]
        elif in_eddystones[index] > 0:
            # eddystone packet was transmitted
            in_eddystones[index] -= 1

    if debug:
        print(str(times) + str(count_per_datas) + '('+str(len(updated_indices))+')')

    # check for collisions
    collisions = 0
    transmissions += len(updated_indices)
    successes += len(updated_indices)
    for tx_index in updated_indices:
        if in_eddystones[index] == 0:
            count_per_datas[tx_index] += 1
        for other_index in range(len(times)):
            # don't test against yourself
            if tx_index == other_index:
                continue

            # get start and end times
            tx_start_time = times[tx_index]
            tx_end_time = tx_start_time + lengths[tx_index]
            ot_start_time = times[other_index]
            ot_end_time = ot_start_time + lengths[other_index]

            # test for packet collisions
            if ((tx_start_time < ot_start_time and tx_end_time > ot_start_time) or
                    (tx_start_time < ot_end_time and tx_end_time > ot_end_time) or
                    (tx_start_time > ot_start_time and tx_end_time < ot_end_time)):
                # packet collision
                collisions += 1
                successes -= 1
                if in_eddystones[index] == 0:
                    count_per_datas[tx_index] -= 1
                if debug:
                    print("Packet 1: " + str(tx_start_time) + '-' + str(tx_end_time))
                    print("Packet 2: " + str(ot_start_time) + '-' + str(ot_end_time))
                    print("")
                break

    # status
    if not debug and collisions != 0:
        print("Time: " + str(curr_time) + '\tCollisions: ' + str(collisions))

    # iterate
    curr_time += iter_step

# print results
print("Successful Transmissions: " + str(successes))
print("Total Transmissions: " + str(transmissions))
print("PRR: " + str(successes/transmissions))
print("")
print("Successful Unique Data: " + str(unique_successes))
print("Total Unique Data: " + str(unique_transmissions))
print("DRR: " + str(unique_successes/unique_transmissions))

