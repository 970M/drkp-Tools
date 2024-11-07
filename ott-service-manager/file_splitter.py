#!/usr/bin/env python3

import os
import argparse
import csv


def open_csv_file_into_table(input_csv_file_path):
    with open(input_csv_file_path, "r") as file_in:
        file_list = list(csv.reader(file_in, delimiter=","))
    return file_list


def write_csv_file_from_table(output_csv_file_path, file_list):
    with open(output_csv_file_path, "w") as file_out:
        wobj = csv.writer(file_out, delimiter=",")
        wobj.writerows([["url", "bitrate"]])
        wobj.writerows(file_list)


def split_file(
    input_dir, output_dir, filename, num_files_to_create, output_filename_suffix
):

    input_file_path = input_dir + "/" + filename

    file_list = open_csv_file_into_table(input_file_path)

    if ["url", "bitrate"] == file_list[0]:
        file_list.pop(0)

    number_of_lines = len(file_list)
    print("Number of lines in file:", number_of_lines)
    number_of_lines_per_file = int(number_of_lines / num_files_to_create)
    print("Number of lines per file:", number_of_lines_per_file)

    for i in range(num_files_to_create):
        filename_without_extension = os.path.splitext(filename)[0]
        filename_extension = ".csv"
        output_file_path = f"{output_dir}/{filename_without_extension}{output_filename_suffix}{i+1}{filename_extension}"
        print("Writing file:", output_file_path)
        write_csv_file_from_table(
            output_file_path,
            file_list[
                i * number_of_lines_per_file : (i + 1) * number_of_lines_per_file
            ],
        )


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input directory path",
        default="../in",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Input directory path",
        default="../out",
    )
    parser.add_argument(
        "-f",
        "--filename",
        help="File name to split",
        default="requested_profiles.csv",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        help="Output file name suffix",
        default="",
    )
    parser.add_argument("-n", "--num", required=True, help="Number of files to create")

    args = parser.parse_args()

    print(f"Args : {args}")

    input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.input))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.output))

    split_file(input_dir, output_dir, args.filename, int(args.num), args.suffix)


if __name__ == "__main__":
    main()
