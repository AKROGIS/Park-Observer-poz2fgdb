# -*- coding: utf-8 -*-
"""
A simple python script which creates a map service from a map file (MXD).

UNFINISHED

Written for Python 2.7; will not work with Python 3.x.
TO use with Python 3.x (Pro) convert arcpy.mapping to arcpy.mp
Requires the Esri ArcGIS arcpy module.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import arcpy

# define local variables
WORKSPACE = r"D:\MapData\Observer"
PROTOCOL = "Test_Protocol_v1"


def main():
    """Create and upload service definition"""

    mxd = os.path.join(WORKSPACE, PROTOCOL + ".mxd")
    map_doc = arcpy.mapping.MapDocument(mxd)
    # connectionfile = 'GIS Servers/ArcGIS on MyServer_6080 (publisher).ags'

    sddraft = os.path.join(WORKSPACE, PROTOCOL + ".sddraft")
    sd_file = os.path.join(WORKSPACE, PROTOCOL + ".sd")

    summary = "Survey Protocol " + PROTOCOL
    tags = "Survey, Protocol, Park Observer, " + PROTOCOL

    # create service definition draft
    analysis = arcpy.mapping.CreateMapSDDraft(
        map_doc,
        sddraft,
        PROTOCOL,
        "ARCGIS_SERVER",
        None,
        False,
        "ParkObserver",
        summary,
        tags,
    )

    # stage and upload the service if the sddraft analysis did not contain errors
    if analysis["errors"] == {}:
        # Execute StageService
        arcpy.StageService_server(sddraft, sd_file)
        # Execute UploadServiceDefinition
        # arcpy.UploadServiceDefinition_server(sd_file, connectionfile)
    else:
        # if the sddraft analysis contained errors, display them
        print(analysis["errors"])


if __name__ == "__main__":
    main()
