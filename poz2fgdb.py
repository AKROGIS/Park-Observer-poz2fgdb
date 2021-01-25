# -*- coding: utf-8 -*-

"""
Park Observer Sync Tool

A command line tool for creating an esri file geodatabase from a
[Park Observer](https://github.com/AKROGIS/Park-Observer) survey archive.

Written for Python 2.7; works with Python 3.x.
Requires the Esri ArcGIS arcpy module.
"""

from __future__ import print_function

import os
import shutil
import sys
import tempfile
import zipfile

import csv_loader

USAGE = "Usage: {0} FILE.poz\n"


def process(archive):
    """Process the survey archive file."""
    extraction_folder = tempfile.mkdtemp()
    try:
        # unzip file
        with zipfile.ZipFile(archive) as my_zip:
            for name in my_zip.namelist():
                my_zip.extract(name, extraction_folder)
        # get the protocol file
        protocol_path = os.path.join(extraction_folder, "protocol.obsprot")
        fgdb_folder = os.path.dirname(archive)
        make_database = csv_loader.database_creator.database_for_protocol_file
        database, protocol_json = make_database(protocol_path, fgdb_folder)
        # load the csv files
        csv_loader.process_csv_folder(extraction_folder, protocol_json, database)
    finally:
        shutil.rmtree(extraction_folder)


def main():
    """Get the command line parameters or quit."""
    if len(sys.argv) != 2:
        print(USAGE.format(sys.argv[0]))
        sys.exit()
    archive_path = os.path.realpath(sys.argv[1])
    if not os.path.exists(archive_path):
        print("Error: '{0}' does not exist".format(archive_path))
        print(USAGE.format(sys.argv[0]))
        sys.exit()
    process(archive_path)


if __name__ == "__main__":
    main()
