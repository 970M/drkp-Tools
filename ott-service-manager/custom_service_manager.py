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
SUT_USER = "admin"
SUT_PWD = "paris"


class OttConfig:
    """ """

    def __init__(self, host_url: str = "", config_file: str = ""):
        """ """

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

            self.generate_source_url()

        if host_url != "":
            self.protocol, self.host, self.port = host_url.split(":")
            self.host = self.host.replace("//", "")
            self.user = SUT_USER
            self.pwd = SUT_PWD
            self.host_url = host_url

        print(f"Connecting to {self.host_url}")
        self.soap_client = SoapClient.SoapClient(
            self.host_url, "ott", (self.user, self.pwd)
        )

    def get_configuration(self, config_path: str) -> dict:
        with open(config_path, "r") as f:
            return json.load(f)

    def generate_source_url(self, streamer_selection: dict = {}) -> list:
        source_uris = []
        for streamer, ports in streamer_selection.items():
            uris = []
            for p in ports:
                ip = self.cfg["sources"][streamer]["ip"]
                port = self.cfg["sources"][streamer]["source_ports"][p - 1]
                interface = self.cfg["sources"][streamer]["interface"]
                uris.append(f"udp://{ip}:{port}/{interface}")
            source_uris.append(uris)
        return source_uris

    def exec_proc(self) -> None:

        print("Update Channels...")
        for ch_name_prefix, ch_param in self.cfg["live"].items():

            list_channel = self.soap_client.List_live_channels()
            options = {
                "archiveLifecycle": [
                    {
                        "action": "delete-unused-data",
                        "disk": "eds",
                        "durationOffset": 172800,
                    },
                    {
                        "action": "delete-all-data",
                        "disk": "eds",
                        "durationOffset": 32140800,
                    },
                ]
            }
            for ch in list_channel:
                try:
                    print(f"Updating channel {ch}")

                    self.soap_client.Modify_live_channel(ch, options)
                except Exception as e:
                    print(f"  Update Live error: {e}")

        time.sleep(15)


def main():

    # Initialize an ASOAP object
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="Configuration file to use.")

    args = parser.parse_args()
    print(args)

    sut = OttConfig(config_file=args.config_file)

    sut.exec_proc()


if __name__ == "__main__":
    main()
