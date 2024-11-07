#!/usr/bin/env python3
import argparse
import importlib.util
from utils.streams.sbrstreamer import SbrStreamer

# MODULE_PATH = "/home/gdaguet/bin/soap-common-2.7.8/SoapClient.py"
# MODULE_NAME = "SoapClient"
# spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
# modulevar = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(modulevar)


### Streamer
# streamer_url = "http://gda-neadvr-streamer-2.lab1.anevia.com:5000"  # Streamer
streamer_url = "http://qas-neadvr-streamer-5.lab1.anevia.com:5000"  # Streamer

### Video TS files

arte = [
    "QAS/Stream_Files/Generic/Arte/arte_1234.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1235.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1236.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1237.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1238.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1239.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1240.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1241.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1242.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1243.ts",
    "QAS/Stream_Files/Generic/Arte/arte_1244.ts",
]

lg = [
    "QAS/Stream_Files/Customers/LG-NonReg/streams20000/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20001/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20002/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20003/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20004/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20005/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20010/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20011/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20012/stream.ts",
    "QAS/Stream_Files/Customers/LG-NonReg/streams20013/stream.ts",
]

bbc_dvb_txt = ["QAS/Stream_Files/DVB-TXT/BBC_TXT_live_same_region.ts"]
tv5_dvb_txt = ["QAS/Manual_Test_Files/C691198-C697532/tv5_monde.ts"]
arte_dvbsub = ["QAS/Manual_Test_Files/C691199/arte_dvbsub_1235.ts"]
charter_cea_x08 = ["QAS/Stream_Files/CEA-x08/Charter/29100.ts"]
encompass_cea_x08 = [
    "QAS/Manual_Test_Files/C691200-C691201/encompass-239.24.100.53-5001.ts"
]

lowlat = [
    "QAS/Stream_Files/Mixed_HEVC_AVC/avatar_mixed_1_AVC_640x480.ts",
    "QAS/Stream_Files/Mixed_HEVC_AVC/avatar_mixed_2_AVC_320x240.ts",
    "QAS/Stream_Files/Mixed_HEVC_AVC/avatar_mixed_3_HEVC_640x480.ts",
    "QAS/Stream_Files/Mixed_HEVC_AVC/avatar_mixed_4_HEVC_320x240.ts",
]


ts_files = arte

parser = argparse.ArgumentParser()

parser.add_argument("-s", "--start", required=False)
parser.add_argument("-e", "--end", required=False)

args = parser.parse_args()
print(args)


if args.end:
    print("Stop stream :", args.end)
    streamer = SbrStreamer(streamer_url)
    streamer.stop_stream(args.end)

else:
    if args.start == "arte":
        ts_files = arte
    elif args.start == "tv5_dvb_txt":
        ts_files = tv5_dvb_txt
    elif args.start == "bbc_dvb_txt":
        ts_files = bbc_dvb_txt
    elif args.start == "arte_dvbsub":
        ts_files = arte_dvbsub
    elif args.start == "encompass_cea_x08":
        ts_files = encompass_cea_x08
    elif args.start == "charter_cea_x08":
        ts_files = charter_cea_x08
    elif args.start == "lg":
        ts_files = lg
    elif args.start == "ll":
        ts_files = lowlat

    streamer = SbrStreamer(streamer_url)
    stream_info = streamer.start_stream(ts_files, loop=True)

    print("Start stream :", stream_info)
    print("UUID :", stream_info["task_id"])
    print("IP :", stream_info["ip"], "Port:", stream_info["ports"])
