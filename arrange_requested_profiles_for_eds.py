#!/usr/bin/env python3

import os
import argparse
import csv

# parser = argparse.ArgumentParser()
# parser.add_argument("host")
# parser.add_argument("-c", "--clean", action="store_true", required=False)
# args = parser.parse_args()
# print(args)
# print("Number of output files", args.nb_output_files)
# parser.add_argument("s")


### Configuration
input_dir = "/home/gdaguet/bin/in"
output_dir = "/home/gdaguet/bin/out"
input_filename = "requested_profiles.csv"

input_file_path = input_dir + "/" + input_filename


def open_csv_file_into_table(input_csv_file_path):
    with open(input_csv_file_path, "r") as file_in:
        file_list = list(csv.reader(file_in, delimiter=","))
    return file_list


def write_csv_file_from_table(output_csv_file_path, file_list):
    with open(output_csv_file_path, "w") as file_out:
        wobj = csv.writer(file_out, delimiter=",")
        wobj.writerows([["url", "bitrate"]])
        wobj.writerows(file_list)


def arrange_file_for_2_playouts(input_file_path, output_dir):
    file_list = open_csv_file_into_table(input_file_path)

    if ["url", "bitrate"] == file_list[0]:
        file_list.pop(0)

    number_of_lines = len(file_list)
    print("Number of lines in file:", number_of_lines)
    number_of_lines_per_playout = int(number_of_lines / 2)
    print("Number of lines per playout:", number_of_lines_per_playout)

    filename_without_extension = os.path.splitext(input_filename)[0]
    filename_extension = ".csv"
    output_file_path = (
        f"{output_dir}/{filename_without_extension}_arr{filename_extension}"
    )

    file_list_arranged = [None for i in range(number_of_lines)]
    for i in range(number_of_lines_per_playout):
        # print(" file_list[i]", file_list[i])
        # print(
        #     " file_list[number_of_lines_per_playout + i]",
        #     file_list[number_of_lines_per_playout + i],
        # )

        file_list[i][0] = file_list[i][0].replace("OTT_IP", "OTT_IP_1")
        file_list[number_of_lines_per_playout + i][0] = file_list[
            number_of_lines_per_playout + i
        ][0].replace("OTT_IP", "OTT_IP_2")

        file_list_arranged[i * 2], file_list_arranged[i * 2 + 1] = (
            file_list[i],
            file_list[number_of_lines_per_playout + i],
        )

    print("Writing file:", output_file_path)
    write_csv_file_from_table(
        output_file_path,
        file_list_arranged,
    )


arrange_file_for_2_playouts(input_file_path, output_dir)


# print(file_list)

# split_file(input_file_path, output_directory_path, num_files_to_create)
