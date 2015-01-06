#!/usr/bin/python2
import sys
import subprocess
import collections
import os
import time
import datetime

N = 10
THRESHOLD = 50000
COUNT_THRESHOLD = 3

last_unc = -1

os.system("killall tzap")
while True:
    tzap = subprocess.Popen(["tzap"] + sys.argv[1:], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    samples = collections.deque([0] * N)
    tot_unc = 0
    count = 0
    while True:
        line = tzap.stderr.readline()
        if not line:
            print "Tzap terminated?"
            break
        print "%s : %s" % (datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y %H:%M:%S'), line.strip())
        sys.stdout.flush()
        if line.startswith("status"):
            count += 1
            if count < 3:
                continue
            idx = line.find("unc") + 4
            unc = int(line[idx:idx+8], 16)
            idx = line.find("status") + 7
            status = int(line[idx:idx+2], 16)
            if last_unc == -1:
                curr_unc = unc
            else:
                curr_unc = unc - last_unc
            if last_unc > 0:
                tot_unc -= samples.pop()
                tot_unc += curr_unc
                samples.appendleft(curr_unc)
            last_unc = unc
            if tot_unc > THRESHOLD or status != 0x1f or len([x for x in samples if x != 0]) >= COUNT_THRESHOLD:
               tzap.terminate()
               tzap.wait()
               break
