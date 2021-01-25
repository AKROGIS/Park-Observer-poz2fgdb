# Park Observer Survey to Esri File Geodatabase

 A tool kit for creating an esri file geodatabase from a
 [Park Observer](https://github.com/AKROGIS/Park-Observer) survey archive.

The tool kit has 4 tools built off a common library.

## 1) An HTTP service: `server.py`

A python script that runs a web service that listens for requests
upload and process a survey archive (*.poz) from Park Observer.
This service maintains an esri file geodatabase for each major
version of a protocol file that it sees.  These file geodatabases
are maintained on the server and can feed map services (created
with `make_service.py`).  They can also be downloaded by the users.

This service supported the _sync to server_ option in Park Observer
1.x.  However it was rarely used, since most users did not have
access to the NPS WiFi on their mobile devices.  This service is not
used with Park Observer 2.0, and is no longer deployed.

The `server.py` script has options to be run as an un-secure (HTTP)
service and as a secure (HTTPS) service.  It loads the modules
`csv_loader.py` and `database_creator.py`. `database_creator.py` relies on
the file `csv.json` which describes the default mapping from the Park
Observer database schema to a set of related feature classes in a FGDB.

See [Server.md](https://github.com/AKROGIS/poz2fgdb/blob/master/Server.md)
for additional details on setting up `server.py` as
a service.

## 2) Command Line Script: `make_service.py`

A simple python script which creates a map service
from a map file (MXD).  This requires the creation of a MXD
set up for each of the file geodatabases created by `server.py`
It was hoped that this could be fully automated, but for
now it is a one time manual process.  The name of the map file
must be set in the script before it is run.

## 3) Command Line Script: `poz2fgdb.py`

This script takes as input a Park Observer survey archive (*.poz),
and builds an appropriate file geodatabase (if one does not exist),
and creates or appends to the appropriate feature classes. The
script takes only one required argument, the path of the `*.poz` file.
It creates the file geodatabase in the current directory unless one
already exists there.

The script `poz2fgdb.py` loads the modules `csv_loader.py` and
`database_creator.py`. `database_creator.py` relies on the file
`csv.json` which describes the default mapping from the Park Observer
database schema to a set of related feature classes in a FGDB.

This tool is typically only used by the developer during testing.  It could be
deployed to the users, but most will prefer the toolbox (below).

## 4) ArcGIS Toolbox: `ParkObserver.pyt`

This is an ArcGIS python toolbox than can be run from ArcCatalog,
or ArcMap. It provides the same functionality as `poz2fgdb.py`.
For convenience of distribution/installation the dependent modules
and `csv.json` are embedded.  See the source code for more details.

### Build

Do not edit `ParkObserver.pyt` directly.  Edit `csv_loader.py` and/or
`database_creator.py`, and then test with `poz2fgdb.py`. Once changes have been
verified, the changes can be copied to `ParkObserver.pyt`.

### Testing

There is a collection of survey archives (`*.poz` files) in the GIS Team network
drive (`T:\PROJECTS\AKR\ParkObserver\pozs`) that can be used for testing changes
to this tool.  There are several `*.poz` files in that folder that will fail
for various good reasons.  Be sure to see the file `testing Notes.md` in the
`poz` folder for details on why.

### Deploy

Copy the updated `ParkObserver.pyt` to the deployed location of the
[Park Observer website](https://github.com/AKROGIS/Park-Observer-website).
Update the website
[download document](https://github.com/AKROGIS/Park-Observer-Website/blob/master/downloads2/index.html#L67-L70)
with the new release date of the toolbox and any significant changes.

### Use

ArcGIS users can open the toolbox in ArcMap, ArcCatalog, or Pro.  The only input
parameter is the file system path to the survey archive file (`*.poz`).  If a
file geodatabase with the correct name exists in the same folder as the archive
it will get new data appended to it, otherwise a new geodatabase will be created
and the data added to it.  **WARNING** If you convert the same `*.poz` file
twice with the same database, the survey will be added twice and you will get
have items in the database.

More detailed usage instructions can be found on the
[Park Observer website](https://github.com/AKROGIS/Park-Observer-website).
