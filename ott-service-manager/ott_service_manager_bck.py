#!/usr/bin/env python3
import os
from urllib.parse import urlparse
import argparse
import subprocess
import datetime
import sys
import json
import logging
import random
import SoapClient
import time

logger = logging.getLogger()


CONF_FILE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/config"


def get_configuration(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)


def generate_source_url(cfg: dict, ports: list) -> list:

    sources_uris = []
    for _, source_param in cfg["sources"].items():
        sources_uri = []
        for port in source_param["source_ports"]:
            sources_uri.append(
                f"udp://{source_param['ip']}:{port}:{source_param['interface']}"
            )
        sources_uris.append(sources_uri)
    return sources_uris


def main():

    # Initialize an ASOAP object
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    # from soap import ASOAP, UTC
    class UTC(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return datetime.timedelta(0)

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Configuration file to use.")
    parser.add_argument(
        "-c",
        "--clean",
        choices=["live", "npvr", "vod", "all"],
        help="Clean the ott configuration",
        # default="all",
    )

    parser.add_argument(
        "-s",
        "--setup",
        choices=["live", "npvr", "vod", "all"],
        help="Setup the wanted ott configuration",
        # default="all",
    )
    args = parser.parse_args()
    print(args)

    cfg = get_configuration(f"{CONF_FILE_DIR}/{args.config_file}")

    cl = SoapClient.SoapClient(
        f'{cfg["sut"]["host"]}:{cfg["sut"]["port"]}',
        cfg["sut"]["service_type"],
        (cfg["sut"]["user"], cfg["sut"]["pwd"]),
    )

    # Clean VOD
    if args.clean == "vod" or args.clean == "all":

        print("Removing VOD...")

        canceled_jobs = []
        delete_error = False
        list_jobs = cl.List_vod_jobs(None, None, None, 1000)
        while len(list_jobs) != 0 and not delete_error:
            for job in list_jobs:
                try:
                    print(f"  Canceling VOD job {job}")
                    cl.Cancel_vod_job(job)
                except Exception as e:
                    print(f"  Cancel VOD error: {e}")
                finally:
                    if job not in canceled_jobs:
                        canceled_jobs.append(job)
                    else:
                        print(f"Job {job} already canceled !!!")
                        delete_error = True
            list_jobs = cl.List_vod_jobs(None, None, None, 1000)

        canceled_vods = []
        delete_error = False
        list_vod = cl.List_vod_assets(None, None, None, 1000)
        while len(list_vod) != 0 and not delete_error:
            for vod in list_vod:
                try:
                    print(f"  Deleting VOD asset {vod}")
                    cl.Delete_vod_asset(vod)
                except Exception as e:
                    print(f"  Delete VOD error: {e}")
                finally:
                    if vod not in canceled_vods:
                        canceled_vods.append(vod)
                    else:
                        print(f"VOD asset {vod} already canceled !!!")
                        delete_error = True
            list_vod = cl.List_vod_assets(None, None, None, 1000)

    # Clean nPVR
    if args.clean == "npvr" or args.clean == "all":
        print("Removing nPVR...")
        canceled_npvrs = []
        delete_error = False
        list_npvr = cl.List_npvrs(None, None, None, 1000)
        while len(list_npvr) != 0 and not delete_error:
            for npvr in list_npvr:
                try:
                    print(f"  Deleting nPVR {npvr}")
                    cl.Delete_npvr(npvr)

                except Exception as e:
                    print(f"  Delete nPVR error: {e}")
                finally:
                    if npvr not in canceled_npvrs:
                        canceled_npvrs.append(npvr)
                    else:
                        print(f"nPVR {npvr} already canceled !!!")
                        delete_error = True
            list_npvr = cl.List_npvrs(None, None, None, 1000)

    # Clean live channels
    if args.clean == "live" or args.clean == "all":
        print("Removing channels...")
        canceled_channels = []
        delete_error = False
        list_channel = cl.List_live_channels()
        while len(list_channel) != 0 and not delete_error:
            for ch in list_channel:
                try:
                    print(f"  Deleting channel {ch}")
                    cl.Delete_live_channel(ch)
                except Exception as e:
                    print(f"  Delete Live error: {e}")
                finally:
                    if ch not in canceled_channels or len(canceled_channels) <= 100:
                        canceled_channels.append(ch)
                    else:
                        print(f"  Channel {ch} already canceled !!!")
                        delete_error = True
            list_channel = cl.List_live_channels()

    # Clean SA/SAF and Scrambling
    if args.clean == "all":
        print("Removing CPIX server...")
        latest_server_to_delete = None
        for server_name in cl.List_scrambling_servers():
            props = cl.Get_scrambling_server_props(server_name)
            if props["conf"]["isDefault"]:
                latest_server_to_delete = server_name
            else:
                cl.Delete_scrambling_server_conf(server_name)
        if latest_server_to_delete:
            cl.Delete_scrambling_server_conf(latest_server_to_delete)

        print("Removing SA/SAF...")
        for saf in cl.List_stream_adaptation_families():
            cl.Delete_stream_adaptation_family(saf)
        for sa in cl.List_stream_adaptations():
            cl.Delete_stream_adaptation(sa)

    # Setup OTT/SA/SAF
    if args.setup == "all":

        # Set up the chunk duration
        cl.Set_ott_conf({"chunkDurations": cfg["ott"]["chunkDurations"]})

        # Scrambling if need
        if cfg["scrambling_conf"]["scrambling"] == True:
            server_url = urlparse(cl.client.options.location).netloc
            server_url_without_port = server_url.split(":")[0]
            print("Put CPIX file scrambling.cpix in the warehouse...")
            subprocess.run(
                [
                    "scp",
                    f'{CONF_FILE_DIR}/{cfg["scrambling_conf"]["cpixFile"]}',
                    f"amaint@{server_url_without_port}:/var/www/warehouse/scrambling.cpix",
                ]
            )
            subprocess.run(
                [
                    "ssh",
                    f"amaint@{server_url_without_port}",
                    "chmod",
                    "o+r",
                    "/var/www/warehouse/scrambling.cpix",
                ]
            )
            print("Creating CPIX server...")
            cl.Set_scrambling_server_conf(
                "warehouse",
                {
                    "type": "cpix",
                    "isDefault": True,
                    "serverUrl": f"https://{server_url}/warehouse",
                },
            )

        print("Creating Stream Adaptation...")
        for sa, sa_conf in cfg["sa"].items():
            for def_param, def_value in cfg["sa_default"].items():
                sa_conf[def_param] = def_value
            cl.Set_stream_adaptation_conf(sa, sa_conf)

        print("Creating Stream Adaptation Familly...")
        for saf, saf_conf in cfg["saf"].items():
            cl.Set_stream_adaptation_family_conf(saf, saf_conf)

    # Setup channels
    if args.setup == "live" or args.setup == "all":
        print("Creating Channels...")
        for ch_name_prefix, ch_param in cfg["live"].items():

            if ch_param["scrambling"]:
                ch_param["options"]["scramblingConf"] = cfg["scrambling_conf"][
                    "scramblingConf"
                ]

            ch_param["options"]["sourceUris"] = generate_source_url(
                cfg, ch_param["options"]["sourceUris"]
            )

            source_uris = generate_source_url(cfg, ch_param["options"]["sourceUris"])

            if (
                cfg["ott"]["database"] == ""
                or cfg["ott"]["database"] == "localDatabase"
            ):
                ch_param["options"]["database"] = cl.Get_ott_conf()["localDatabase"]
            else:
                ch_param["options"]["database"] = cfg["ott"]["database"]

            for index_channel in range(0, ch_param["nb_channel"]):

                try:
                    ch_name = f"{ch_name_prefix}_{index_channel:03}"

                    ch_param["options"]["sourceUris"] = source_uris[
                        index_channel % len(source_uris)
                    ]

                    print(f'  Add {ch_name} on {cfg["ott"]["database"]}')
                    cl.Create_live_channel(
                        ch_name,
                        cfg["ott"]["disk"],
                        ch_param["type"],
                        ch_param["options"],
                    )
                except Exception as e:
                    print(f"  Creating channel error: {e}")

        time.sleep(15)

    if args.setup == "npvr" or args.setup == "all":

        def rand_time(start, end, time_format, prop):

            stime = time.mktime(time.strptime(start, time_format))
            etime = time.mktime(time.strptime(end, time_format))
            ptime = stime + prop * (etime - stime)

            return time.strftime(time_format, time.localtime(ptime))

        print("Creating nPVR...")

        for npvr_name_prefix, npvr_param in cfg["npvr"].items():

            npvr_conf = {}
            if npvr_param["source_channel"] in cfg["live"]:

                print(f'From {npvr_param["source_channel"]}')

                if (
                    cfg["live"][npvr_param["source_channel"]]["options"]["type"]
                    == "infinite"
                ):
                    npvr_conf["useLiveChannelOutputSettings"] = True
                else:
                    npvr_conf["streamAdaptationFamily"] = cfg["live"][
                        npvr_param["source_channel"]
                    ]["options"]["streamAdaptationFamily"]
                    npvr_conf["scramblingConf"] = cfg["scrambling_conf"][
                        "scramblingConf"
                    ]
                    npvr_conf["persistent"] = True

                if (
                    "channel_restriction" not in npvr_param
                    or npvr_param["channel_restriction"] == ""
                ):
                    list_live_channels = cl.List_live_channels()
                else:
                    list_live_channels = npvr_param["channel_restriction"]

                for channel_name in list_live_channels:

                    if npvr_param["source_channel"] in channel_name:

                        # Get the start time of the archive
                        archive_start_time = cl.Get_live_buffer_detailed_status(
                            channel_name
                        )["tracks"][0]["timeline"][0]["start"]

                        range_start = datetime.datetime.strptime(
                            archive_start_time, "%Y-%m-%dT%H:%M:%S%z"
                        )

                        range_stop = range_start + datetime.timedelta(
                            seconds=npvr_param["npvr_range"]
                        )

                        for rec in range(0, npvr_param["nb_npvr_per_channel"]):

                            #### nPVR aléatoire
                            # npvr_start = rand_time(
                            #     range_start.strftime("%Y-%m-%d %H:%M:%S%z"),
                            #     range_stop.strftime("%Y-%m-%d %H:%M:%S%z"),
                            #     "%Y-%m-%d %H:%M:%S%z",
                            #     random.random(),
                            # )

                            # npvr_start = datetime.datetime.strptime(
                            #     npvr_start, "%Y-%m-%d %H:%M:%S%z"
                            # )

                            # npvr_exp_duration = (
                            #     npvr_param["npvr_duration"]
                            #     + (1 - random.random() * 2)
                            #     * npvr_param["npvr_duration_variation"]
                            # )

                            #### nPVR alignés

                            npvr_start = datetime.datetime.now(UTC()).replace(
                                microsecond=0
                            )

                            begin = npvr_start.replace(microsecond=0).isoformat()
                            end = (
                                (
                                    npvr_start
                                    + datetime.timedelta(
                                        seconds=npvr_param["npvr_duration"]
                                    )
                                )
                                .replace(microsecond=0)
                                .isoformat()
                            )
                            date_range = {
                                "begin": str(begin),
                                "end": str(end),
                            }
                            npvr_conf["range"] = date_range

                            npvr_name = (
                                f"{npvr_name_prefix}_{channel_name}_rec_{rec:003}"
                            )
                            try:
                                print(f"  Add {npvr_name}: {str(begin)}")
                                cl.Create_npvr(npvr_name, channel_name, npvr_conf)
                            except Exception as e:
                                print(f"  Creating nPVR error: {e}")
                    # else:

                    #     print(
                    #         f"No substring {npvr_param['source_channel']} in {channel_name}"
                    #     )

    if args.setup == "vod" or args.setup == "all":

        print("Creating VOD...")

        for vod_name_prefix, vod_param in cfg["vod"].items():

            job_conf = {
                "streamAdaptationFamily": vod_param["streamAdaptationFamily"],
                "scramblingConf": cfg["scrambling_conf"]["scramblingConf"],
            }

            if "source_uri" not in vod_param or vod_param["source_uri"] == "":

                nb_vod_inc = 0
                npvr_list = []
                npvr_sample = cl.List_npvrs(None, None, nb_vod_inc, 1000)
                while len(npvr_sample) > 0:
                    nb_vod_inc += 1000
                    npvr_list.extend(npvr_sample)
                    try:
                        npvr_sample = cl.List_npvrs(None, None, nb_vod_inc, 1000)
                    except Exception as e:
                        npvr_sample = []

                source_uri = [
                    f'npvr://{cfg["ott"]["disk"]}/{str(npvr)}' for npvr in npvr_list
                ]
                # saf = cfg["live"][cfg["npvr"][vod_param["source_npvr"]]["source_channel"]["options"]["streamAdaptationFamily"]
            else:
                source_uri = vod_param["source_uri"]

            n = 0
            nb_created_vod = 0
            while nb_created_vod < vod_param["nb_vod"]:

                vod_name = f"{vod_name_prefix}_{nb_created_vod:004}"
                print(f"  Add {vod_name}")
                try:
                    cl.Create_vod_job(
                        source_uri[n],
                        f'vod://{cfg["ott"]["disk"]}/{vod_name}',
                        job_conf,
                    )
                except Exception as e:
                    print(f"  Creating VOD error: {e}")

                finally:
                    n += 1
                    n = n % len(source_uri)
                    nb_created_vod += 1


if __name__ == "__main__":
    main()
