#!/usr/bin/env python3
import argparse
from SoapClient import SoapClient


parser = argparse.ArgumentParser()

parser.add_argument("host")
parser.add_argument("-c", "--clean", action="store_true", required=False)

# define optional option to select the stream between arte_tl, arte, france2_tl, tv5, tv5_tl, if no option value equal to all streams
parser.add_argument(
    "-s",
    "--stream",
    choices=["arte_tl", "arte", "france2_tl", "tv5", "tv5_tl"],
    required=False,
)

# parser.add_argument(
#     "-s",
#     "--stream",
#     action="store_true",
#     choices=["arte_tl", "arte", "france2_tl", "tv5", "tv5_tl"],
# )

parser.add_argument("-n", "--nb_channel", type=int, default=1, required=False)


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

# soap.Set_ott_conf({"chunkDurations": ["2"]})

streams = {}


# Stream Arte
ip_arte = "239.68.0.11"
streams["arte_tl"] = [
    "udp://%s:1234:%s" % (ip_arte, interface),
    "udp://%s:1235:%s" % (ip_arte, interface),
    "udp://%s:1236:%s" % (ip_arte, interface),
    "udp://%s:1237:%s" % (ip_arte, interface),
]

# Stream Arte (rebouclage)
ip_arte_loop = "239.68.0.100"
streams["arte"] = [
    "udp://%s:1234:%s" % (ip_arte_loop, interface),
    "udp://%s:1235:%s" % (ip_arte_loop, interface),
    "udp://%s:1236:%s" % (ip_arte_loop, interface),
    "udp://%s:1237:%s" % (ip_arte_loop, interface),
    "udp://%s:1238:%s" % (ip_arte_loop, interface),
    "udp://%s:1239:%s" % (ip_arte_loop, interface),
    "udp://%s:1240:%s" % (ip_arte_loop, interface),
    "udp://%s:1241:%s" % (ip_arte_loop, interface),
    "udp://%s:1242:%s" % (ip_arte_loop, interface),
    "udp://%s:1243:%s" % (ip_arte_loop, interface),
    "udp://%s:1244:%s" % (ip_arte_loop, interface),
]

# Stream France2
ip_france2 = "239.68.0.12"
streams["france2_tl"] = [
    "udp://%s:1234:%s" % (ip_france2, interface),
    "udp://%s:1235:%s" % (ip_france2, interface),
    "udp://%s:1236:%s" % (ip_france2, interface),
]

# Stream TV5 Monde
ip_tv5_monde = "239.68.0.13"
streams["tv5_tl"] = [
    "udp://%s:1234:%s" % (ip_tv5_monde, interface),
    "udp://%s:1235:%s" % (ip_tv5_monde, interface),
    "udp://%s:1236:%s" % (ip_tv5_monde, interface),
    "udp://%s:1237:%s" % (ip_tv5_monde, interface),
    "udp://%s:1238:%s" % (ip_tv5_monde, interface),
    "udp://%s:1239:%s" % (ip_tv5_monde, interface),
]

# Stream TV5 Monde
ip_tv5_monde_loop = "239.68.0.101"
streams["tv5"] = ["udp://%s:1234:%s" % (ip_tv5_monde_loop, interface)]


def main():

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

        streams_selected = streams
        if args.stream:
            streams_to_delete = [stream for stream in streams if stream != args.stream]
            for stream in streams_to_delete:
                del streams_selected[stream]

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

        sa_name = "sa_cmaf"
        conf = {
            "outputFormat": "cmaf",
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
                    "sa_cmaf",
                ]
            },
        )

        # Channels
        print("Creating channels...")
        for channel_name, sources_ip in streams.items():

            channel_options = {
                "streamAdaptationFamily": SAF,
                "mbtsSources": [
                    {
                        "id": "main",
                        "enable": True,
                        "udp_sources": sources_ip,
                        "group": "default",
                        "multicast_origins": None,
                    }
                ],
                "archiveLifecycle": [
                    {
                        "action": "delete-unused-data",
                        "disk": "disk1",
                        "durationOffset": 600,
                    },
                    {
                        "action": "delete-all-data",
                        "disk": "disk1",
                        "durationOffset": 600,
                    },
                ],
            }

            for i in range(0, args.nb_channel):
                ch_name = f"{channel_name}_{i:03}"
                soap.Create_live_channel(ch_name, disk, _type, channel_options)
                print("    ", f"Add {ch_name}")


if __name__ == "__main__":
    main()
