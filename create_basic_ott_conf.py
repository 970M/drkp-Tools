#!/usr/bin/env python3
import argparse
from SoapClient import SoapClient
import importlib.util

MODULE_PATH = "/home/gdaguet/bin/soap-common-2.7.8/SoapClient.py"
MODULE_NAME = "SoapClient"

spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
modulevar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulevar)


parser = argparse.ArgumentParser()

parser.add_argument("host")
parser.add_argument("-c", "--clean", action="store_true", required=False)

args = parser.parse_args()
print(args)

print("Configure host", args.host)

host = args.host  # "gda-1.lab1.anevia.com"
port = "8080"
user = "admin"
pwd = "paris"
service_type = "ott"
soap = SoapClient(f"{host}:{port}", service_type, (user, pwd))


interface = "auto"
disk = "disk1"
_type = "ts-generic"

SAF = "saf"
CHANNEL_NAME_PREFIXE = "generic_channel_"
NB_CHANNEL = 1

# soap.Set_ott_conf({"chunkDurations": ["2"]})

# # Stream
# ip = "239.10.0.1"

# sources_ip = [
#     "udp://%s:20000:%s" % (ip, interface),
#     "udp://%s:20001:%s" % (ip, interface),
#     "udp://%s:20002:%s" % (ip, interface),
#     "udp://%s:20003:%s" % (ip, interface),
#     "udp://%s:20004:%s" % (ip, interface),
#     "udp://%s:20005:%s" % (ip, interface),
#     "udp://%s:20010:%s" % (ip, interface),
#     "udp://%s:20011:%s" % (ip, interface),
#     "udp://%s:20012:%s" % (ip, interface),
# ]

# Stream
ip = "239.2.2.4"

sources_ip = [
    "udp://%s:1234:%s" % (ip, interface),
    "udp://%s:1235:%s" % (ip, interface),
    "udp://%s:1236:%s" % (ip, interface),
    "udp://%s:1237:%s" % (ip, interface),
    "udp://%s:1238:%s" % (ip, interface),
    "udp://%s:1239:%s" % (ip, interface),
    "udp://%s:1240:%s" % (ip, interface),
    "udp://%s:1241:%s" % (ip, interface),
    "udp://%s:1242:%s" % (ip, interface),
    "udp://%s:1243:%s" % (ip, interface),
    "udp://%s:1244:%s" % (ip, interface),
]

# ip = "239.10.1.1"
# sources_ip = ["udp://%s:5009:%s" % (ip, interface)]

if args.clean:
    # Cleaning
    print("Removing channels...")
    listChannel = soap.List_live_channels()
    # while len(listChannel) != 0:
    for c in listChannel:
        print("    ", f"Delete {c}")
        try:
            soap.Delete_live_channel(c)
        except Exception as e:
            print(f"Error during deleting {c}")
        # listChannel = soap.List_live_channels()

    print("Removing CPIX server...")
    latest_server_to_delete = None
    for server_name in soap.List_scrambling_servers():
        props = soap.Get_scrambling_server_props(server_name)
        if props["conf"]["isDefault"]:
            latest_server_to_delete = server_name
        else:
            soap.Delete_scrambling_server_conf(server_name)
    if latest_server_to_delete:
        soap.Delete_scrambling_server_conf(latest_server_to_delete)

    print("Removing SA/SAF...")
    for saf in soap.List_stream_adaptation_families():
        soap.Delete_stream_adaptation_family(saf)
    for sa in soap.List_stream_adaptations():
        soap.Delete_stream_adaptation(sa)


if not args.clean:
    # SA
    print("Creating SA/SAF...")
    sa_name = "sa_dash"
    conf = {
        "outputFormat": "dash",
        "chunkDuration": 10,
        "subtitlesFormat": "ttmlpassthrough",
    }
    soap.Set_stream_adaptation_conf(sa_name, conf)

    sa_name = "sa_hls"
    conf = {
        "outputFormat": "hls",
        "chunkDuration": 10,
        "subtitlesFormat": "webvtt",
    }
    soap.Set_stream_adaptation_conf(sa_name, conf)

    # SAF
    soap.Set_stream_adaptation_family_conf(
        SAF,
        {
            "streamAdaptations": [
                "sa_dash",
                "sa_hls",
            ]
        },
    )

    # Channels

    channel_options = {
        "streamAdaptationFamily": SAF,
        "sourceUris": sources_ip,
    }

    print("Creating channels...")
    for i in range(0, NB_CHANNEL):
        ch_name = f"{CHANNEL_NAME_PREFIXE}{i:03}"
        soap.Create_live_channel(ch_name, disk, _type, channel_options)
        print("    ", f"Add {ch_name}")
