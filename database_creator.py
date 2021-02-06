# -*- coding: utf-8 -*-
"""
Module to create an esri file geodatabase for a Park Observer protocol file.

Written for Python 2.7; works with Python 3.x.
Requires the Esri ArcGIS arcpy module.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from io import open
import json
import os

import arcpy


def database_for_protocol_file(protocol_path, fgdb_folder):
    """Create an esri file geodatabase from a Park Observer protocol file.

    Takes a file path to the protocol file (string) and a file path to the
    folder where the geodatabase is to be created (string).

    Returns the file path of the geodatabase (string) and the protocol (object).
    """
    with open(protocol_path, "r", encoding="utf-8") as handle:
        protocol = json.load(handle)
    # I either crashed or I have a good protocol
    if protocol["meta-name"] == "NPS-Protocol-Specification":
        version = protocol["meta-version"]
        if version <= 2:
            if "csv" not in protocol:
                add_missing_csv_section(protocol)
            database = database_for_version1(protocol, fgdb_folder)
            return database, protocol
        print(
            "Unable to process protocol specification version {1} (in file {0}).".format(
                protocol_path, version
            )
        )
    else:
        print("File {0} is not a valid protocol file".format(protocol_path))
    return None, None


def add_missing_csv_section(protocol):
    """Add the default csv property to a protocol object and return the protocol."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    csv_path = os.path.join(script_dir, "csv.json")
    with open(csv_path, "r", encoding="utf-8") as handle:
        csv = json.load(handle)
        protocol["csv"] = csv
    return protocol


def database_for_version1(protocol, workspace):
    """Create a geodatabase from a PO protocol file and return the fgdb's path."""
    version = int(protocol["version"])  # get just the major number of the protocol
    raw_database_name = "{0}_v{1}".format(protocol["name"], version)
    valid_database_name = arcpy.ValidateTableName(raw_database_name, workspace) + ".gdb"
    database = os.path.join(workspace, valid_database_name)
    if not arcpy.Exists(database):
        database = build_database_version1(protocol, workspace, valid_database_name)
    return database


def build_database_version1(protocol, folder, database):
    """Create a geodatabase from a PO version 1 protocol file and return the fgdb's path."""
    print("Building {0} in {1}".format(database, folder))
    arcpy.CreateFileGDB_management(folder, database)
    fgdb = os.path.join(folder, database)
    spatial_ref = arcpy.SpatialReference(4326)
    domains = get_domains_from_protocol_v1(protocol)
    aliases = get_aliases_from_protocol_v1(protocol)
    build_domains(fgdb, domains)
    build_gpspoints_table_version1(fgdb, spatial_ref, protocol)
    # mission is optional in Park Observer 2.0
    try:
        attribute_list = get_attributes(protocol["mission"], domains, aliases)
    except KeyError:
        attribute_list = []
    build_tracklog_table_version1(fgdb, spatial_ref, attribute_list, protocol)
    build_observations_table_version1(fgdb, spatial_ref, protocol)
    for feature in protocol["features"]:
        build_feature_table_version1(
            fgdb,
            spatial_ref,
            feature["name"],
            get_attributes(feature, domains, aliases),
            protocol,
        )
    build_relationships(fgdb, protocol)
    return fgdb


def get_attributes(feature, domains=None, aliases=None):
    """Converts a protocol feature's attributes into esri attribute properties.

    Takes a feature (object) from the protocol file, and dictionary of
    domains (default None), and a dictionary of aliases (default None).

    Return a list of esri attribute objects for each attribute in the feature.
    """
    attribute_list = []
    type_table = {
        0: "LONG",
        100: "SHORT",
        200: "LONG",
        300: "DOUBLE",  # 64bit int (not supported by ESRI)
        400: "DOUBLE",  # NSDecimal  (not supported by ESRI)
        500: "DOUBLE",
        600: "FLOAT",
        700: "TEXT",
        800: "SHORT",  # Boolean (use 0 = false, 1 = true)
        900: "DATE",
        1000: "BLOB",
    }
    # attributes are optional in Park Observer 2.0
    try:
        attributes = feature["attributes"]
    except KeyError:
        attributes = []
    for attribute in attributes:
        name = attribute["name"]
        datatype = type_table[attribute["type"]]
        try:
            nullable = not attribute["required"]
        except KeyError:
            nullable = True

        alias = name.replace("_", " ")
        if aliases:
            try:
                feature_aliases = aliases[feature["name"]]
            except KeyError:
                try:
                    feature_aliases = aliases["mission"]
                except KeyError:
                    feature_aliases = None
            if feature_aliases and name in feature_aliases:
                alias = feature_aliases[name]

        if attribute["type"] == 800:
            domain = "YesNoBoolean"
        else:
            if domains and name in domains:
                domain = "{0}Codes".format(name)
            else:
                domain = ""

        attribute_props = {
            "name": name,
            "nullable": nullable,
            "type": datatype,
            "alias": alias,
            "domain": domain,
        }
        attribute_list.append(attribute_props)
    return attribute_list


def build_gpspoints_table_version1(fgdb, spatial_ref, protocol):
    """Create a feature class of GPS points."""
    table_name = protocol["csv"]["gps_points"]["name"]
    field_names = protocol["csv"]["gps_points"]["field_names"]
    field_types = protocol["csv"]["gps_points"]["field_types"]
    arcpy.CreateFeatureclass_management(
        fgdb, table_name, "POINT", "#", "#", "#", spatial_ref
    )
    # doing multiple operations on a view is faster than on a table
    view = arcpy.MakeTableView_management(os.path.join(fgdb, table_name), "view")
    try:
        # Protocol Attributes
        #  - None
        # Standard Attributes
        for i, field_name in enumerate(field_names):
            alias = field_name.replace("_", " ")
            arcpy.AddField_management(
                view, field_name, field_types[i], "", "", "", alias
            )
        # Links to related data
        arcpy.AddField_management(view, "TrackLog_ID", "LONG")
    finally:
        arcpy.Delete_management(view)


def build_tracklog_table_version1(fgdb, spatial_ref, attributes, protocol):
    """Create a feature class of track logs."""
    table_name = protocol["csv"]["track_logs"]["name"]
    field_names = protocol["csv"]["track_logs"]["field_names"]
    field_types = protocol["csv"]["track_logs"]["field_types"]
    arcpy.CreateFeatureclass_management(
        fgdb, table_name, "POLYLINE", "#", "#", "#", spatial_ref
    )
    view = arcpy.MakeTableView_management(os.path.join(fgdb, table_name), "view")
    try:
        # Protocol Attributes
        for attribute in attributes:
            arcpy.AddField_management(
                view,
                attribute["name"],
                attribute["type"],
                "",
                "",
                "",
                attribute["alias"],
                "",
                "",
                attribute["domain"],
            )
        # Standard Attributes
        for i, field_name in enumerate(field_names):
            alias = field_name.replace("_", " ")
            arcpy.AddField_management(
                view, field_name, field_types[i], "", "", "", alias
            )
            # Links to related data
            #  - None
    finally:
        arcpy.Delete_management(view)


def build_observations_table_version1(fgdb, spatial_ref, protocol):
    """Create a feature class of PO observation locations."""
    table_name = protocol["csv"]["features"]["obs_name"]
    field_names = protocol["csv"]["features"]["obs_field_names"]
    field_types = protocol["csv"]["features"]["obs_field_types"]
    arcpy.CreateFeatureclass_management(
        fgdb, table_name, "POINT", "", "", "", spatial_ref
    )
    view = arcpy.MakeTableView_management(os.path.join(fgdb, table_name), "view")
    try:
        # Protocol Attributes
        #  - None
        # Standard Attributes
        for i, field_name in enumerate(field_names):
            alias = field_name.replace("_", " ")
            arcpy.AddField_management(
                view, field_name, field_types[i], "", "", "", alias
            )
        # Link to related data
        arcpy.AddField_management(view, "GpsPoint_ID", "LONG")
    finally:
        arcpy.Delete_management(view)


def build_feature_table_version1(fgdb, spatial_ref, raw_name, attributes, protocol):
    """Create a feature class of PO observation items (features)."""
    valid_feature_name = arcpy.ValidateTableName(raw_name, fgdb)
    field_names = protocol["csv"]["features"]["feature_field_names"]
    field_types = protocol["csv"]["features"]["feature_field_types"]
    arcpy.CreateFeatureclass_management(
        fgdb, valid_feature_name, "POINT", "#", "#", "#", spatial_ref
    )
    view = arcpy.MakeTableView_management(
        os.path.join(fgdb, valid_feature_name), "view"
    )
    try:
        # Protocol Attributes
        for attribute in attributes:
            arcpy.AddField_management(
                view,
                attribute["name"],
                attribute["type"],
                "",
                "",
                "",
                attribute["alias"],
                "",
                "",
                attribute["domain"],
            )
        # Standard Attributes
        for i, field_name in enumerate(field_names):
            alias = field_name.replace("_", " ")
            arcpy.AddField_management(
                view, field_name, field_types[i], "", "", "", alias
            )
        # Link to related data
        arcpy.AddField_management(view, "GpsPoint_ID", "LONG")
        arcpy.AddField_management(view, "Observation_ID", "LONG")
    finally:
        arcpy.Delete_management(view)


def build_relationships(fgdb, protocol):
    """Create the relationships between the various PO feature classes."""
    gps_points_table = os.path.join(fgdb, protocol["csv"]["gps_points"]["name"])
    track_logs_table = os.path.join(fgdb, protocol["csv"]["track_logs"]["name"])
    observations_table = os.path.join(fgdb, "Observations")
    arcpy.CreateRelationshipClass_management(
        track_logs_table,
        gps_points_table,
        os.path.join(fgdb, "GpsPoints_to_TrackLog"),
        "COMPOSITE",
        "GpsPoints",
        "TrackLog",
        "NONE",
        "ONE_TO_MANY",
        "NONE",
        "OBJECTID",
        "TrackLog_ID",
    )

    arcpy.CreateRelationshipClass_management(
        gps_points_table,
        observations_table,
        os.path.join(fgdb, "Observations_to_GpsPoint"),
        "SIMPLE",
        "Observations",
        "GpsPoints",
        "NONE",
        "ONE_TO_ONE",
        "NONE",
        "OBJECTID",
        "GpsPoint_ID",
    )

    for feature_obj in protocol["features"]:
        feature = arcpy.ValidateTableName(feature_obj["name"], fgdb)
        feature_table = os.path.join(fgdb, feature)
        arcpy.CreateRelationshipClass_management(
            gps_points_table,
            feature_table,
            os.path.join(fgdb, "{0}_to_GpsPoint".format(feature)),
            "SIMPLE",
            feature,
            "GpsPoint",
            "NONE",
            "ONE_TO_ONE",
            "NONE",
            "OBJECTID",
            "GpsPoint_ID",
        )
        arcpy.CreateRelationshipClass_management(
            observations_table,
            feature_table,
            os.path.join(fgdb, "{0}_to_Observation".format(feature)),
            "SIMPLE",
            feature,
            "Observation",
            "NONE",
            "ONE_TO_ONE",
            "NONE",
            "OBJECTID",
            "Observation_ID",
        )


def build_domains(fgdb, domains):
    """Create the esri domains (picklists) for track logs and features."""
    arcpy.CreateDomain_management(
        fgdb, "YesNoBoolean", "Yes/No values", "SHORT", "CODED"
    )
    arcpy.AddCodedValueToDomain_management(fgdb, "YesNoBoolean", 0, "No")
    arcpy.AddCodedValueToDomain_management(fgdb, "YesNoBoolean", 1, "Yes")
    for domain in domains:
        name = "{0}Codes".format(domain)
        description = "Valid values for {0}".format(domain)
        arcpy.CreateDomain_management(fgdb, name, description, "SHORT", "CODED")
        items = domains[domain]
        for i, item in enumerate(items):
            arcpy.AddCodedValueToDomain_management(fgdb, name, i, item)


def get_aliases_from_protocol_v1(protocol):
    """Create esri field name aliases using the attribute titles from the  input form."""
    results = {}
    # mission is optional in Park Observer 2.0
    try:
        mission_list = [protocol["mission"]]
    except KeyError:
        mission_list = []
    for feature in mission_list + protocol["features"]:
        try:
            feature_name = feature["name"]
        except KeyError:
            feature_name = "mission"
        feature_results = {}
        # dialog is optional in Park Observer 2.0
        if "dialog" in feature:
            for section in feature["dialog"]["sections"]:
                try:
                    section_title = section["title"]
                except KeyError:
                    section_title = None
                field_title = None
                for field in section["elements"]:
                    try:
                        field_title = field["title"]
                    except KeyError:
                        pass
                    try:
                        field_name = field["bind"].split(":")[1]
                    except (KeyError, IndexError, AttributeError):
                        field_name = None
                    if field_name and field_title:
                        if section_title:
                            field_alias = "{0} {1}".format(section_title, field_title)
                        else:
                            field_alias = field_title
                        feature_results[field_name] = field_alias
        results[feature_name] = feature_results
    return results


def get_domains_from_protocol_v1(protocol):
    """Return a dictionary of valid values (list) for each attribute name (string)."""
    results = {}
    # mission, attributes, dialog and bind are optional properties in Park Observer 2.0
    if "mission" in protocol:
        if "attributes" in protocol["mission"]:
            mission_attribute_names = [
                attrib["name"]
                for attrib in protocol["mission"]["attributes"]
                if attrib["type"] == 100
            ]
            if "dialog" in protocol["mission"]:
                for section in protocol["mission"]["dialog"]["sections"]:
                    for field in section["elements"]:
                        if "bind" in field:
                            if field["type"] == "QRadioElement" and field[
                                "bind"
                            ].startswith("selected:"):
                                name = field["bind"].replace("selected:", "").strip()
                                if name in mission_attribute_names:
                                    results[name] = field["items"]
    for feature in protocol["features"]:
        # attributes, dialog and bind are optional properties in Park Observer 2.0
        if "attributes" in feature:
            attribute_names = [
                attrib["name"]
                for attrib in feature["attributes"]
                if attrib["type"] == 100
            ]
            if "dialog" in feature:
                for section in feature["dialog"]["sections"]:
                    for field in section["elements"]:
                        if "bind" in field:
                            if field["type"] == "QRadioElement" and field[
                                "bind"
                            ].startswith("selected:"):
                                name = field["bind"].replace("selected:", "").strip()
                                if name in attribute_names:
                                    results[name] = field["items"]
    return results


if __name__ == "__main__":
    database_for_protocol_file(
        protocol_path=r"\\akrgis.nps.gov\inetApps\observer\protocols\sample.obsprot",
        fgdb_folder=r"C:\tmp\observer",
    )
