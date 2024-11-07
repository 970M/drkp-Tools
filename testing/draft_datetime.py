#!/usr/bin/env python3


from datetime import datetime


starting_time = "79256:20:38.777"
current_time = "79256:21:41.577"


def format_time(ttml_time: str, reference_hour: int = 0):
    hours = ttml_time.split(":")[0]
    minutes = ttml_time.split(":")[1]
    seconds = ttml_time.split(":")[2].split(".")[0]
    milliseconds = ttml_time.split(":")[2].split(".")[1]

    hours = int(hours) - reference_hour

    return f"{hours}:{minutes}:{seconds}.{milliseconds}"


def timedelta_to_str(timedelta_obj):
    total_seconds = int(timedelta_obj.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = timedelta_obj.microseconds // 1000
    return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, minutes, seconds, milliseconds)


def relative_time(starting_time: str, current_time: str):
    format_date = "%H:%M:%S.%f"

    try:
        datetime1 = datetime.strptime(starting_time, format_date)
        datetime2 = datetime.strptime(current_time, format_date)

        difference = datetime2 - datetime1

        print(
            "Différence entre les deux dates :", difference.total_seconds(), "secondes"
        )

        return difference

    except ValueError:
        print("Format de date invalide. Assurez-vous d'utiliser le format hh:mm:ss.ms")


format_date = "%H:%M:%S.%f"

starting_hour = int(starting_time.split(":", maxsplit=1)[0])

starting_time = format_time(starting_time, starting_hour)
current_time = format_time(current_time, starting_hour)

datetime1 = datetime.strptime(starting_time, format_date)
datetime2 = datetime.strptime(current_time, format_date)


difference = datetime2 - datetime1
difference = timedelta_to_str(difference)


print(difference)
