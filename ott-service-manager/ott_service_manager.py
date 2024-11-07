#!/usr/bin/env python3
import os
from urllib.parse import urlparse
import argparse
import subprocess
import datetime
import sys
import json
import logging
import SoapClient
import time

logger = logging.getLogger()


CONF_FILE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/config"
SUT_USER = "admin"
SUT_PWD = "paris"


class OttConfig:
    """
    OttConfig class represents the configuration for the OTT service manager.

    Attributes:
        host_url (str): The URL of the host.
        config_file (str): The path to the configuration file.

    Methods:
        __init__(self, host_url: str = "", config_file: str = ""): Initializes the OttConfig object.
        get_configuration(self, config_path: str) -> dict: Loads the configuration from a file.
       generate_sources_urls(self, streamer_selection: dict = {}) -> list: Generates the source URLs.
        clean_vod(self) -> None: Removes VOD assets and jobs.
        clean_npvr(self) -> None: Removes nPVR assets.
        clean_live(self) -> None: Removes live channels.
        clean_scrambling(self) -> None: Removes CPIX servers.
        clean_sa_saf(self) -> None: Removes Stream Adaptation and Stream Adaptation Family.
        setup_ott(self) -> None: Sets up the OTT configuration.
        setup_scrambling(self) -> None: Sets up the scrambling configuration.
        setup_sa_saf(self) -> None: Sets up the Stream Adaptation and Stream Adaptation Family.
        setup_live(self) -> None: Sets up the live channels.
    """

    def __init__(self, host_url: str = "", config_file: str = ""):
        """
        Initializes the OttConfig object.

        Args:
            host_url (str): The URL of the host.
            config_file (str): The path to the configuration file.
        """
        self.host_url = ""
        self.cfg = {}
        self.user = SUT_USER
        self.pwd = SUT_PWD
        self.sources_uris = []
        if config_file != "":
            self.cfg = self.get_configuration(f"{CONF_FILE_DIR}/{config_file}")
            self.host = self.cfg["sut"]["host"]
            self.port = self.cfg["sut"]["port"]
            self.protocol = "https" if self.port == "8443" else "http"
            self.user = self.cfg["sut"]["user"]
            self.pwd = self.cfg["sut"]["pwd"]
            self.host_url = f"{self.protocol}://{self.host}:{self.port}"

            # self.generate_sources_urls()

        if host_url != "":
            self.protocol, self.host, self.port = host_url.split(":")
            self.host = self.host.replace("//", "")
            self.user = SUT_USER
            self.pwd = SUT_PWD
            self.host_url = host_url

        print(f"Connecting to {self.host_url}")
        self.soap_client = SoapClient.SoapClient(self.host_url, "ott", (self.user, self.pwd))

    def get_configuration(self, config_path: str) -> dict:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_sources_urls(self, streamer_selection: dict = {}) -> list:
        source_uris = []
        for streamer, ports in streamer_selection.items():
            uris = []
            for p in ports:
                ip = self.cfg["sources"][streamer]["ip"]
                port = self.cfg["sources"][streamer]["source_ports"][p - 1]
                interface = self.cfg["sources"][streamer]["interface"]
                uris.append(f"udp://{ip}:{port}:{interface}")
            source_uris.append(uris)
        return source_uris

    def clean_vod(self) -> None:
        print("Removing VOD...")

        canceled_jobs = []
        delete_error = False
        list_jobs = self.soap_client.List_vod_jobs(None, None, None, 1000)
        while len(list_jobs) != 0 and not delete_error:
            for job in list_jobs:
                try:
                    print(f"  Canceling VOD job {job}")
                    self.soap_client.Cancel_vod_job(job)
                except Exception as e:
                    print(f"  Cancel VOD error: {e}")
                finally:
                    if job not in canceled_jobs:
                        canceled_jobs.append(job)
                    else:
                        print(f"Job {job} already canceled !!!")
                        delete_error = True
            list_jobs = self.soap_client.List_vod_jobs(None, None, None, 1000)

        canceled_vods = []
        delete_error = False
        list_vod = self.soap_client.List_vod_assets(None, None, None, 1000)
        while len(list_vod) != 0 and not delete_error:
            for vod in list_vod:
                try:
                    print(f"  Deleting VOD asset {vod}")
                    self.soap_client.Delete_vod_asset(vod)
                except Exception as e:
                    print(f"  Delete VOD error: {e}")
                finally:
                    if vod not in canceled_vods:
                        canceled_vods.append(vod)
                    else:
                        print(f"VOD asset {vod} already canceled !!!")
                        delete_error = True
            list_vod = self.soap_client.List_vod_assets(None, None, None, 1000)

    def clean_npvr(self) -> None:
        print("Removing nPVR...")
        canceled_npvrs = []
        delete_error = False
        list_npvr = self.soap_client.List_npvrs(None, None, None, 1000)
        while len(list_npvr) != 0 and not delete_error:
            for npvr in list_npvr:
                try:
                    print(f"  Deleting nPVR {npvr}")
                    self.soap_client.Delete_npvr(npvr)

                except Exception as e:
                    print(f"  Delete nPVR error: {e}")
                finally:
                    if npvr not in canceled_npvrs:
                        canceled_npvrs.append(npvr)
                    else:
                        print(f"nPVR {npvr} already canceled !!!")
                        delete_error = True
            list_npvr = self.soap_client.List_npvrs(None, None, None, 1000)

    def clean_live(self) -> None:
        print("Removing channels...")
        canceled_channels = []
        delete_error = False
        list_channel = self.soap_client.List_live_channels()
        while len(list_channel) != 0 and not delete_error:
            for ch in list_channel:
                try:
                    print(f"  Deleting channel {ch}")
                    self.soap_client.Delete_live_channel(ch)
                except Exception as e:
                    print(f"  Delete Live error: {e}")
                finally:
                    if ch not in canceled_channels or len(canceled_channels) <= 100:
                        canceled_channels.append(ch)
                    else:
                        print(f"  Channel {ch} already canceled !!!")
                        delete_error = True
            list_channel = self.soap_client.List_live_channels()

    def clean_scrambling(self) -> None:
        print("Removing CPIX server...")
        latest_server_to_delete = None
        for server_name in self.soap_client.List_scrambling_servers():
            props = self.soap_client.Get_scrambling_server_props(server_name)
            if props["conf"]["isDefault"]:
                latest_server_to_delete = server_name
            else:
                self.soap_client.Delete_scrambling_server_conf(server_name)
        if latest_server_to_delete:
            self.soap_client.Delete_scrambling_server_conf(latest_server_to_delete)

    def clean_sa_saf(self) -> None:
        print("Removing SA/SAF...")
        for saf in self.soap_client.List_stream_adaptation_families():
            self.soap_client.Delete_stream_adaptation_family(saf)
        for sa in self.soap_client.List_stream_adaptations():
            self.soap_client.Delete_stream_adaptation(sa)

    def setup_ott(self) -> None:
        # Set up the chunk duration
        self.soap_client.Set_ott_conf({"chunkDurations": self.cfg["ott"]["chunkDurations"]})

    def setup_scrambling(self) -> None:
        # Scrambling if need
        if "scrambling_conf" in self.cfg:
            if "scramblingConf" in self.cfg["scrambling_conf"]:
                server_url = urlparse(self.soap_client.client.options.location).netloc
                server_url_without_port = server_url.split(":")[0]
                cpix_file = self.cfg["scrambling_conf"]["scramblingConf"][0]["value"]["cpix"]["cpixId"]
                print("Put CPIX file scrambling.cpix in the warehouse...")
                subprocess.run(
                    [
                        "scp",
                        f"{CONF_FILE_DIR}/{cpix_file}",
                        f"amaint@{server_url_without_port}:/var/www/warehouse/{cpix_file}",
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
                self.soap_client.Set_scrambling_server_conf(
                    "warehouse",
                    {
                        "type": "cpix",
                        "isDefault": True,
                        "serverUrl": f"https://{server_url}/warehouse",
                    },
                )

    def setup_sa_saf(self) -> None:
        print("Creating Stream Adaptation...")
        for sa, sa_conf in self.cfg["sa"].items():
            for def_param, def_value in self.cfg["sa_default"].items():
                sa_conf[def_param] = def_value
            self.soap_client.Set_stream_adaptation_conf(sa, sa_conf)

        print("Creating Stream Adaptation Familly...")
        for saf, saf_conf in self.cfg["saf"].items():
            self.soap_client.Set_stream_adaptation_family_conf(saf, saf_conf)

    def setup_live(self) -> None:
        print("Creating Channels...")
        for ch_name_prefix, ch_param in self.cfg["live"].items():
            if ch_param["scrambling"]:
                ch_param["options"]["scramblingConf"] = self.cfg["scrambling_conf"]["scramblingConf"]

            if self.cfg["ott"]["database"] == "" or self.cfg["ott"]["database"] == "localDatabase":
                ch_param["options"]["database"] = self.soap_client.Get_ott_conf()["localDatabase"]
            else:
                ch_param["options"]["database"] = self.cfg["ott"]["database"]

            source_uris = self.generate_sources_urls(ch_param["streamers"])

            for index_channel in range(0, ch_param["nb_channel"]):
                try:
                    ch_name = f"{ch_name_prefix}_{index_channel:03}"

                    ch_param["options"]["sourceUris"] = source_uris[index_channel % len(source_uris)]

                    print(f'  Add {ch_name} on {ch_param["options"]["database"]}')
                    self.soap_client.Create_live_channel(
                        ch_name,
                        self.cfg["ott"]["disk"],
                        ch_param["type"],
                        ch_param["options"],
                    )
                except Exception as e:
                    print(f"  Creating channel error: {e}")

        # print("Initializing...")
        # time.sleep(15)

    def setup_npvr(self) -> None:
        class UTC(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(0)

            def tzname(self, dt):
                return "UTC"

            def dst(self, dt):
                return datetime.timedelta(0)

        print("Creating nPVR...")
        if "npvr" in self.cfg:
            for npvr_name_prefix, npvr_param in self.cfg["npvr"].items():
                npvr_conf = {}
                if npvr_param["source_channel"] in self.cfg["live"]:
                    if self.cfg["live"][npvr_param["source_channel"]]["options"]["type"] == "infinite":
                        npvr_conf["useLiveChannelOutputSettings"] = True
                    else:
                        npvr_conf["streamAdaptationFamily"] = self.cfg["live"][npvr_param["source_channel"]]["options"][
                            "streamAdaptationFamily"
                        ]
                        npvr_conf["scramblingConf"] = self.cfg["scrambling_conf"]["scramblingConf"]
                        npvr_conf["persistent"] = True

                    if "channel_restriction" not in npvr_param or npvr_param["channel_restriction"] == "":
                        list_live_channels = self.soap_client.List_live_channels()
                    else:
                        list_live_channels = npvr_param["channel_restriction"]

                    if "start_time" in npvr_param:
                        range_start = datetime.datetime.strptime(
                            f'{npvr_param["start_time"]}+00:00', "%Y-%m-%d %H:%M:%S%z"
                        )
                    else:
                        range_start = datetime.datetime.now(UTC()).replace(microsecond=0)
                        print(f"range_start: {range_start}")
                        # range_start = range_start + datetime.timedelta(seconds=-14400)

                    range_end = range_start + datetime.timedelta(days=npvr_param["npvr_range"])

                    for channel_name in list_live_channels:
                        if npvr_param["source_channel"] in channel_name:
                            ##### Get the start time of the channel archive
                            # archive_start_time = self.soap_client.Get_live_buffer_detailed_status(channel_name)[
                            #     "tracks"
                            # ][0]["timeline"][0]["start"]
                            # range_start = datetime.datetime.strptime(archive_start_time, "%Y-%m-%dT%H:%M:%S%z")

                            # Calculating the duration of the offset to space all the npvrs over the creation period npvr_range
                            # |-----range-----|
                            # |-d-|
                            #      s|-d-|
                            #            s|-d-|
                            time_shift = 0
                            if (npvr_param["nb_npvr_per_channel"] - 1) > 0:
                                time_shift = (npvr_param["npvr_range"] - npvr_param["npvr_duration"]) / (
                                    npvr_param["nb_npvr_per_channel"] - 1
                                ) - npvr_param["npvr_duration"]

                            for rec in range(0, npvr_param["nb_npvr_per_channel"]):
                                npvr_start = range_start + datetime.timedelta(
                                    seconds=rec * (npvr_param["npvr_duration"] + time_shift)
                                )

                                begin = npvr_start.replace(microsecond=0).isoformat()
                                end = (
                                    (npvr_start + datetime.timedelta(seconds=npvr_param["npvr_duration"]))
                                    .replace(microsecond=0)
                                    .isoformat()
                                )
                                date_range = {
                                    "begin": str(begin),
                                    "end": str(end),
                                }
                                npvr_conf["range"] = date_range

                                npvr_name = f"{npvr_name_prefix}_{channel_name}_rec_{rec:003}"
                                try:
                                    print(f"  Add {npvr_name}: {range_start} {str(begin)} {str(range_end)}")
                                    self.soap_client.Create_npvr(npvr_name, channel_name, npvr_conf)
                                except Exception as e:
                                    print(f"  Creating nPVR error: {e}")

    def setup_vod(self) -> None:
        print("Creating VOD...")

        if "vod" in self.cfg:
            for vod_name_prefix, vod_param in self.cfg["vod"].items():
                job_conf = {
                    "streamAdaptationFamily": vod_param["streamAdaptationFamily"],
                    "scramblingConf": self.cfg["scrambling_conf"]["scramblingConf"],
                }

                if "source_uri" not in vod_param or vod_param["source_uri"] == "":
                    nb_vod_inc = 0
                    npvr_list = []
                    npvr_sample = self.soap_client.List_npvrs(None, None, nb_vod_inc, 1000)
                    while len(npvr_sample) > 0:
                        nb_vod_inc += 1000
                        npvr_list.extend(npvr_sample)
                        try:
                            npvr_sample = self.soap_client.List_npvrs(None, None, nb_vod_inc, 1000)
                        except Exception as e:
                            npvr_sample = []

                    source_uri = [f'npvr://{self.cfg["ott"]["disk"]}/{str(npvr)}' for npvr in npvr_list]
                else:
                    source_uri = vod_param["source_uri"]

                n = 0
                nb_created_vod = 0
                while nb_created_vod < vod_param["nb_vod"]:
                    vod_name = f"{vod_name_prefix}_{nb_created_vod:004}"
                    print(f"  Add {vod_name}")
                    try:
                        self.soap_client.Create_vod_job(
                            source_uri[n],
                            f'vod://{self.cfg["ott"]["disk"]}/{vod_name}',
                            job_conf,
                        )
                    except Exception as e:
                        print(f"  Creating VOD error: {e}")

                    finally:
                        n += 1
                        n = n % len(source_uri)
                        nb_created_vod += 1


def main():
    # Initialize an ASOAP object
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Configuration file to use.")
    parser.add_argument(
        "-c",
        "--clean",
        choices=["live", "npvr", "vod", "all"],
        help="Clean the ott configuration",
    )

    parser.add_argument(
        "-s",
        "--setup",
        choices=["live", "npvr", "vod", "all"],
        help="Setup the wanted ott configuration",
    )
    args = parser.parse_args()
    print(args)

    sut = OttConfig(config_file=args.config_file)
    cl = sut.soap_client

    # Clean VOD
    if args.clean == "vod" or args.clean == "all":
        sut.clean_vod()

    # Clean nPVR
    if args.clean == "npvr" or args.clean == "all":
        sut.clean_npvr()

    # Clean live channels
    if args.clean == "live" or args.clean == "all":
        sut.clean_live()

    # Clean SA/SAF and Scrambling
    if args.clean == "all":
        sut.clean_scrambling()
        sut.clean_sa_saf()

    # Setup OTT/SA/SAF
    if args.setup == "all":
        sut.setup_ott()
        sut.setup_scrambling()
        sut.setup_sa_saf()

    # Setup channels
    if args.setup == "live" or args.setup == "all":
        sut.setup_live()

    # Setup nPVR
    if args.setup == "npvr" or args.setup == "all":
        sut.setup_npvr()

    # Setup VOD
    if args.setup == "vod" or args.setup == "all":
        sut.setup_vod()


if __name__ == "__main__":
    main()
