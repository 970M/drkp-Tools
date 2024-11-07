#!/usr/bin/env python3

import argparse
import ott_service_manager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host_url", help="Host url to use.")
    parser.add_argument(
        "-c",
        "--clean",
        choices=["live", "npvr", "vod", "all"],
        help="Clean the ott configuration",
        default="all",
    )

    args = parser.parse_args()

    print(f"Cleaning {args.clean} configuration on {args.host_url}")
    sut = ott_service_manager.OttConfig(host_url=args.host_url)

    if args.clean == "live":
        sut.clean_live()

    elif args.clean == "npvr":
        sut.clean_npvr()

    elif args.clean == "vod":
        sut.clean_vod()

    elif args.clean == "all":
        sut.clean_vod()
        sut.clean_npvr()
        sut.clean_live()
        sut.clean_scrambling()
        sut.clean_sa_saf()


if __name__ == "__main__":
    main()
