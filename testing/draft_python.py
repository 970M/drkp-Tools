#!/usr/bin/env python3

import random
import time

import datetime


# Fonction pour calculer la médiane d'une liste
def median(lst):
    n = len(lst)
    s = sorted(lst)
    return (sum(s[n // 2 - 1 : n // 2 + 1]) / 2.0, s[n // 2])[n % 2] if n else None


class Toto:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Toto {self.name}"


foo = Toto("foo")


print(foo["name"])


# r = range(199)

# npvr = "npvr_bench_channel_178_rec_089"

# for i in range(177, 200):
#     if str(i) in npvr:
#         print(i)


# npvr_to_remove = []

# for i_ch in range(177, 200):
#     for i_npvr in range(0, 100):
#         npvr_to_remove.append(f"npvr_bench_channel_{i_ch:003}_rec_{i_npvr:003}")

# print(npvr_to_remove)


# channel_list = []

# for i_ch in range(177, 200):
#     for i_npvr in range(0, 100):
#         channel_list.append(f"bench_channel_{i_ch:003}")

# print(channel_list)

###################################
# # from soap import ASOAP, UTC
# class UTC(datetime.tzinfo):
#     def utcoffset(self, dt):
#         return datetime.timedelta(0)

#     def tzname(self, dt):
#         return "UTC"

#     def dst(self, dt):
#         return datetime.timedelta(0)


# def random_time(start, end time_format):

#     start_time = datetime.datetime.strptime(start, time_format)
#     print("start_time:", start_time)

#     now = datetime.datetime.now(UTC()).replace(microsecond=0)
#     print(now)
#     now_timestamp = now.timestamp()
#     print("now_timestamp:", now_timestamp)


# random_time("2024-03-18 12:52:39", "2024-03-18 12:52:39", "%Y-%m-%d %H:%M:%S")
###################################################


# def str_time_prop(start, end, time_format, prop):
#     """Get a time at a proportion of a range of two formatted times.

#     start and end should be strings specifying times formatted in the
#     given format (strftime-style), giving an interval [start, end].
#     prop specifies how a proportion of the interval to be taken after
#     start.  The returned time will be in the specified format.
#     """

#     stime = time.mktime(time.strptime(start, time_format))
#     etime = time.mktime(time.strptime(end, time_format))

#     ptime = stime + prop * (etime - stime)

#     return time.strftime(time_format, time.localtime(ptime))


# def random_date(start, end, prop):
#     # return str_time_prop(start, end, "%m/%d/%Y %I:%M %p", prop)
#     return str_time_prop(start, end, "%Y-%m-%d %H:%M:%S%z", prop)


# print(
#     str_time_prop(
#         "2024-03-18 12:20:04+00:00",
#         "2025-03-18 12:20:04+00:00",
#         "%Y-%m-%d %H:%M:%S%z",
#         random.random(),
#     )
# )
