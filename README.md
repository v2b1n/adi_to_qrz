# adi_to_qrz

This python script uploads your ADI-logfile to qrz.com logbook. Please see "Features" for a full features list.

## Features

* uploads ADI-logfile entries to qrz.com logbook
* empties the ADI-logfile if told to do so
* fetches remote party's grid locator data from qrz.com
  * if desired, the program can fetch remote party's grid locator data from qrz.com's xml-interface and "enrich" the QSO data with it, before saving in logbook; while WSJT-X provides only 4 chars of the grid locator, on 2m band the precision of 4 chars long locator vs 6 chars long does make quite a difference in distance calculation.
* keeps erroneous/non-imported QSOs and writes them into a separate file, see FAQ 

## Why?
My WSJT-X runs on a raspberry pi. After having used the WSJT-X for a while i noticed that the manual upload-procedure to qrz.com is rather boring.
This script fixes it - being triggered every couple of minutes by cron, it grabs the "wsjtx_log.adi" and the uploads the QSO-records.

## System requirements & installation instructions

### For Linux users

Beside regular python installation, following python package is required:
```
python-requests
```

On a debian-based linux-distro a
```
apt-get update
apt-get -y install python-requests
```
will usually make things work. All other distros should try

```
python -m pip install requests
```

Then, put the adi_to_qrz.py into your WSJT-X log directory (by default  "~/.local/share/WSJT-X") and create a cronjob like this:

```
pi@raspberrypi:~ $ crontab -l

# trigger every 5 minutes
*/5 * * * * cd ~/.local/share/WSJT-X && python adi_to_qrz.py -d -a "My_Api_Key_Here"
pi@raspberrypi:~ $

```



### For Windows users

1. Grab the latest python 3.X release from https://www.python.org/downloads/windows/ and install it

2. Add python installation directory (e.g. the default "C:\Program Files (x86)\Python37-32" or whereever you've installed it) to environment's PATH variable according e.g. to one of these howto's:

  *  Windows 7 users: http://geekswithblogs.net/renso/archive/2009/10/21/how-to-set-the-windows-path-in-windows-7.aspx
  *  Windows 10 users: https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/

3. Grab the latest release of "adi_to_qrz" from https://gitlab.com/v2b1n/adi_to_qrz and put the contained "adi_to_qrz.py" into your WJCT-X log directory (the default is "C:\Users\\$USERNAME\AppData\Local\WSJT-X")

4. Edit the "adi_to_qrz.py" and put your QRZ-logbook apikey around line 32 replacing the "APIKEY_NOT_SPECIFIED" string there and save the "adi_to_qrz.py".

5. Add a scheduled task that triggers "adi_to_qrz.py" every YOU_NAME_IT minutes. (Howto? Please google for "windows how to run scheduled task every x minutes"



## Usage

As the "help" sections shows, the usage is pretty straightforward

```
./adi_to_qrz.py  -h
Usage: adi_to_qrz.py [options]
 -h  --help       print this usage and exit
 -a  --apikey     setting apikey for api-connection
 -x  --xmllookups enable xml-lookups for better grid locator data
 -u  --username   qrz.com username, must be provided if xml-lookups are enabled
 -p  --password   qrz.com password, must be provided if xml-lookups are enabled
 -i  --inputfile  setting inputfile, default: wsjtx_log.adi
 -l  --logfile    setting logfile, default: adi_to_qrz.log
 -d  --delete     empty the inputfile after import, default: no
     --debug      enable debugging output
```

The only mandatory option is "-a" - sure, you have to provide a valid API-key for QRZ.com logbook-access. Where do you get one?
Please, just google for it https://www.google.de/search?q=qrz+logbook+api+key.

Beside of specifying the apikey as "-a" option you can also set it as environment variable "APIKEY".

qrz.com username and password can be provided as options -u/--username && -p/--password or as environment variables: "QRZ_COM_USERNAME" and "QRZ_COM_PASSWORD".

All actions are logged into a logfile.

To disable logfile writing entirely specify "-l null".

All ADI-log-records rejected by QRZ-server are stored into a file that is named "YYYMMDD_HHmm_failed_records.adi", where YYYYMMDD_HHmm is the current date and time.



# FAQ

* Q: _Will that script overwrite existing entries in the QRZ logbook?_
  * A: No, the script will NOT overwrite your existing entries. It will only add NEW records.

* Q: _Will that script empty/delete my ADI logfile after importing records into QRZ logbook ?_
  * A: By default - no, the script will NOT empty the file you specified for import. If you specify a key "-d" - yes, it will.

* Q: _If i specify "-d" flag so my ADI logfile is emptied - what happens to the erroneous/non-imported QSO-records?_
  * A: All failed records are written into a separate ADI-logfile in the same directory. The name of this new logfile is "YYYMMDD_HHmm_failed_records.adi", where YYYYMMDD_HHmm is the current date and time.






# Troubleshooting

## Duplicates

The error

> Server response was:"Unable to add QSO to database: duplicate"

is pretty self explanatory. It means that the logbook where you trying to import the qso entry into, already has such an entry. Either you delete the QRZ-entry in the logbook or the QSO-entry line in the logfile.


## ADI Log mandatory fields

If the import fails and you spot an error

> Server response was:"QRZ Internal Error: Unable to add QSO to database."

check first whether the mandatory fields are presend in your ADIF-log.

The api of logbook.qrz.com requires that an ADIF qso record has at least following mandatory fields:

```
STATION_CALLSIGN or OPERATOR
CALL
QSO_DATE
BAND
MODE
```
where *STATION_CALLSIGN* or *OPERATOR* **must** contain YOUR callsign


## "Things does not work as expected! Please help!"

Please open an issue at https://gitlab.com/v2b1n/adi_to_qrz/issues/new and describe the problem.
Also attaching the adi-logfile and the program-logfile, or their relevant parts, will help.


# Links

* WSJT-X: https://physics.princeton.edu/pulsar/k1jt/wsjtx.html
* ADIF format specs: http://www.adif.org (v1/v2/v3)
* qrz.com REST API PDF: http://files.qrz.com/static/qrz/The%20QRZ%20Logbook%20API.pdf
* qrz.com xml interface specification https://www.qrz.com/XML/current_spec.html
* lotw developer information https://lotw.arrl.org/lotw-help/developer-information/
