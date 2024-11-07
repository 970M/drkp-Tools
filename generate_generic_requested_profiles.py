#!/usr/bin/env python3

"""
Generates requested profiles files for the Regression benchmark test
"""

BITRATES = [
    500000,
    1500000,
    2500000,
    3500000,
    5200000,
    7000000,
]  # , 1400000, 3300000, 5500000]
# BITRATES = [400000, 800000, 960000, 1200000, 1800000, 2300000]  # Sources LG Titan
# BITRATES = [100000, 110000, 190000, 300000, 500000, 750000, 1100000, 1500000, 2000000, 3400000, 4000000]  # Sources Arte

NB_CHANNELS = 300
SEP = ","
DISK = "disk1"  # eds for EDS
CHANNEL_PREFIXE = "generic_channel_"  # npv for nPVR
# ["dash_time_scr", "dash_number_scr", "hls_auto_ts_scr", "hls_auto_fmp4_scr", "hls_v7_ts_scr" ,"hls_auto_fmp4_scr"]


def main():
    # Use a breakpoint in the code line below to debug your script.
    CSVHeaders = f"url{SEP}bitrate"

    tmp_url = """http://${{OTT_IP}}/live/disk1/{channel}/{profile}/{channel}{manifest_extension}{sep}{bitrate}
"""

    channels = [
        {
            "name": f"{CHANNEL_PREFIXE}",
            "bitrates": BITRATES[1:6],
            "profiles": {
                # "dash_number": ".mpd",
                "dash_time": ".mpd",
                # "hls_v3_ts_scr": ".m3u8",
                # "hls_v5_ts_scr": ".m3u8",
                # "hls_v7_ts_scr": ".m3u8",
                # "hls_v7_fmp4_scr": ".m3u8",
                # "ss_20_scr": ".m3u8",
                # "ss_22_scr": ".m3u8",
                "cmaf": ".mpd",
            },
            "number": NB_CHANNELS,
        },
    ]

    allEndpoints = ""
    for channel in channels:
        for num in range(0, channel.get("number")):
            name = channel.get("name")
            channel_name = f"{name}{str(num).zfill(3)}"
            print("name=", channel_name)
            profiles = channel.get("profiles")
            for profile in profiles:
                print("profile=", profile)
                manifest_extension = profiles.get(profile)
                for bitrate in channel.get("bitrates"):
                    print("bitrate=", bitrate)
                    allEndpoints += tmp_url.format(
                        channel=channel_name,
                        profile=profile,
                        bitrate=bitrate,
                        sep=SEP,
                        manifest_extension=manifest_extension,
                    )

    with open("/home/gdaguet/bin/out/requested_profiles.csv", "w") as f:
        f.write(f"{CSVHeaders}\n")
        f.write(allEndpoints)


if __name__ == "__main__":
    main()
