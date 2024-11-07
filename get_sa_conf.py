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

args = parser.parse_args()
print(args)

print("Configure host", args.host)

host = args.host  # "gda-1.lab1.anevia.com"
port = "8080"
user = "admin"
pwd = "paris"
service_type = "ott"
soap = SoapClient(f"{host}:{port}", service_type, (user, pwd))


print("Get SA configuration...")
sa_conf = {}
for sa in soap.List_stream_adaptations():
    sa_conf[sa] = soap.Get_stream_adaptation_conf(sa)


for sa in [
    "dash-fhd",
    "dash-fhd15m",
    "dash-fhddvr",
    "hls-ios-fhd",
    "hls-ios-fhd-preset",
    "hls-ios-fhddvr",
    "hls-ios-fhddvr-preset",
    "hls-stb-fhd",
    "hls-stb-fhddvr",
    "hls-stb-hddvr",
    "hss-hd",
    "hss-hddvr",
]:
    print(sa, sa_conf[sa])
