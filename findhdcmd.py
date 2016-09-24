#!/usr/bin/python2

from cmzsh import *
import subprocess
import os
import datetime
import signal


def killtzap():
    try:
        x("killall tzap")
    except subprocess.CalledProcessError:
        pass

def signal_handler(signal, frame):
    killtzap()

signal.signal(signal.SIGINT, signal_handler)

name = "Rai 1 HD"
if len(argv) > 1:
    name = argv[1]
killtzap()
channel = None
FNULL = open(os.devnull, 'w')
subprocess.Popen(["tzap", name], stdout = FNULL, stderr = FNULL)
with open("/home/benji/.tzap/channels.conf") as f:
    for L in f:
        channel, _, _, _, _, _, _, _, _, _, nid, tid, rid = L.strip().split(":")
        if channel == name:
            break

pm_pid = None
if channel:
    rid = int(rid)
    rx = re.compile("Program_number: %d \(0x%04x\)" % (rid, rid))
    rx_pmPID = re.compile("Program_map_PID: (\d+) \(0x(.*)\)")
    found = False
    for L in x("dvbsnoop -n 1 0"):
        if found:
            if not L:
                found = False
            else:
                m = rx_pmPID.search(L)
                if m:
                    pm_pid = int(m.groups()[0])
                    break
        else:
            m = rx.search(L)
            if m:
                found = True
    streams = []
    if pm_pid:
        rx_stream = re.compile("Stream_type: (\d+)")
        rx_epid = re.compile("Elementary_PID: (\d+)")
        stream_type = None
        sstr = ""
        e_pid = None
        for L in x("dvbsnoop -n 1 %d" % pm_pid):
            m = rx_stream.search(L)
            if m:
                stream_type = int(m.groups()[0])
                sstr = L
            elif stream_type:
                m = rx_epid.search(L)
                if m:
                    e_pid = m.groups()[0]
                    if stream_type in (2, 4, 6, 27):
                        streams.append(e_pid)
                    else:
                        print "Ignoro epid %s (%s)" % (e_pid, sstr.strip())
                    stream_type = None
        d = datetime.datetime.now()
        fn = "/home/benji/video/tv/%04d%02d%02d_%02d%02d_%s.ts" % (d.year, d.month, d.day, d.hour, d.minute, name.replace(" ", "_"))
        system("dvbstream -o %s > %s" % (" ".join(streams), fn))
    else:
        print "Program_map_PID non trovato!" % name
        exit(1)
else:
    print "Canale '%s' non trovato!" % name
    exit(1)
