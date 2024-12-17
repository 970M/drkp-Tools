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

logger = logging.getLogger()

HOST = "https://dvr2.gen10.lab1.anevia.com:8443"
# HOST = "https://nea-live-ref.lab1.anevia.com:8443"
SUT_USER = "admin"
SUT_PWD = "paris"
SOURCE_URI_PREFIXE = "udp://239.68"


# Update the sourceUri of all live channels
def update_sourceUri(soap_client, channel_prop):

    mbtsSources = channel_prop["conf"]["options"]["mbtsSources"]
    udp_sources = mbtsSources[0]["udp_sources"]
    new_udp_sources = []
    for udp_source in udp_sources:

        # Get the sourceUris index
        tmp = udp_source.split("//")
        prefix_udp = tmp[0]
        url_full = tmp[1]
        ip, port, lan = url_full.split(":")
        ip1, ip2, ip3, ip4 = ip.split(".")

        # newSourceUriEDS = f"{SOURCE_URI_PREFIXE}.1{ip4}.0:{port}:{lan}"
        # print(f"Updating sourceUri from {sourceUri} to {newSourceUriEDS}")

        new_udp_source = f"{SOURCE_URI_PREFIXE}.{ip4}.0:{port}:{lan}"
        print(f"Updating sourceUri from {udp_source} to {new_udp_source}")

        new_udp_sources.append(new_udp_source)

    # Update the sourceUri
    mbtsSources[0]["udp_sources"] = new_udp_sources

    option = {"mbtsSources": mbtsSources}
    print(f"Updating udp_sources from {udp_sources} to {new_udp_sources}")

    return option


def update_codec_private_data_changes(channel_props):

    channel_props["conf"]["options"]["ignoreVideoCodecPrivateDataChanges"] = True

    option = {"ignoreVideoCodecPrivateDataChanges": True}

    # option = {"options": {"ignoreVideoCodecPrivateDataChanges": True}}

    return option


def main():
    # Initialize an ASOAP object
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    logger.info(f"Connecting to {HOST}")
    soap_client = SoapClient.SoapClient(HOST, "ott", (SUT_USER, SUT_PWD))

    # Update channel sourceUris from 239.10.10.1 to 239.68.1.1 by using self.soap_client.Modify_live_channel() api

    # Get all live channels
    live_channels = soap_client.List_live_channels()
    for live_channel in live_channels:
        print(live_channel)
        # Get the sourceUris
        channel_props = soap_client.Get_live_channel_props(live_channel)
        print(channel_props["conf"]["options"]["ignoreVideoCodecPrivateDataChanges"])
        # channel_props_updated = update_sourceUri(soap_client, channel_props)

        channel_props_updated = update_codec_private_data_changes(channel_props)

        # Update the channel
        try:
            print(f"Updating channel {live_channel}")
            print(channel_props_updated)
            soap_client.Modify_live_channel(live_channel, channel_props_updated)
        except Exception as e:
            print(f"Error during updating {live_channel}")
            print(e)


if __name__ == "__main__":
    main()
