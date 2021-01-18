# Park Observer Survey to Esri File Geodatabase

 A tool kit for creating an esri file geodatabase from a
 [Park Observer](https://github.com/AKROGIS/Park-Observer) survey archive.

The tool kit has 4 tools built off a common library.

## 1) An HTTP service: `Server.py`

A python script that runs a web service that listens for requests
upload and process a survey archive (*.poz) from Park Observer.
This service maintains an esri file geodatabase for each major
version of a protocol file that it sees.  These file geodatabases
are maintained on the server and can feed map services (created
with `MakeService.py`).  They can also be downloaded by the users.

This service supported the _sync to server_ option in Park Observer
1.x.  However it was rarely used, since most users did not have
access to the NPS wifi on their mobile devices.  This service is not
used with Park Observer 2.0

The `Server.py` script has options to be run as an un-secure (HTTP)
service and as a secure (HTTPS) service.  It loads the modules
`CsvLoader.py` and `DatabaseCreator.py`. `DatabaseCreator.py` relies on
the file `CSV.json` which describes the default mapping from the Park
Observer database schema to a set of related feature classes in a FGDB.

See [Server.md](https://github.com/AKROGIS/poz2fgdb/blob/master/Server.md)
for additional details on setting up `Server.py` as
a service.

## 2) Command Line Script: `MakeService.py`

A simple python script which creates a map service
from a map file (MXD).  This requires the creation of a MXD
set up for each of the file geodatabases created by `Server.py`
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

The script `poz2fgdb.py` loads the modules `CsvLoader.py` and 
`DatabaseCreator.py`. `DatabaseCreator.py` relies on the file
`CSV.json` which describes the default mapping from the Park Observer
database schema to a set of related feature classes in a FGDB.

## 4) ArcGIS Toolbox: `ParkObserver.pyt`

This is an ArcGIS python toolbox than can be run from ArcCatalog,
or ArcMap. It provides the same functionality as `poz2fgdb.py`.
For convenience of distribution/installation the dependent modules
and `csv.json` are embedded.  See the source code for more details.
