#!/usr/bin/env python3


import os
import hashlib
from collections import defaultdict
import glob
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find duplicate JPG files in a directory."
    )
    parser.add_argument(
        "directory", type=str, help="The directory to search for duplicate JPG files."
    )

    parser.add_argument(
        "-e",
        "--extension",
        type=str,
        default="jpg",
        help="The file extension to search for duplicates (default: jpg).",
    )

    parser.add_argument(
        "-d",
        "--duplicate-threshold",
        type=int,
        default=1,
        help="The threshold for the number of duplicates (default: 1).",
    )

    return parser.parse_args()


args = parse_arguments()
directory_path = args.directory
extension = args.extension
duplicate_threshold = args.duplicate_threshold


def hash_file(file_path, block_size=65536):
    """Calcule un hash SHA-1 pour un fichier donné."""
    sha1 = hashlib.sha1()
    try:
        with open(file_path, "rb") as file:
            while chunk := file.read(block_size):
                sha1.update(chunk)
    except IOError as e:
        print(f"Erreur lors de l'ouverture du fichier {file_path}: {e}")
    return sha1.hexdigest()


def find_duplicate_files_by_extention(directory, extension):
    # Dictionnaire pour stocker les fichiers par leur hash
    hash_dict = defaultdict(list)

    ret = os.listdir(directory)
    extension
    # Parcourir le répertoire et ses sous-répertoires
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(f".{extension}"):
                file_path = os.path.join(root, file)

                # Calculer le hash du fichier
                file_hash = hash_file(file_path)
                # Ajouter le fichier à la liste des fichiers de même hash
                hash_dict[file_hash].append([root, file])

    # Afficher les doublons
    print("Fichiers en doublons trouvés :")
    for paths in hash_dict.values():
        if len(paths) > duplicate_threshold:
            for path in paths:
                root = path[0]
                file = path[1]
                file_path = os.path.join(root, file)

                print(f"{file}: {root}")

                if "Phone" in file_path:

                    print(f"Deleting {root}/{file}")
                    os.remove(file_path)

            print("-" * 50)

    return hash_dict


if __name__ == "__main__":
    find_duplicate_files_by_extention(directory_path, extension)
