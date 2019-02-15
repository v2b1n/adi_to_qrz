# adi_to_qrz

This python script uploads your ADI-logfile to qrz.com logbook.

## Why?
My WSJT-X runs on a raspberry pi. After having used the WSJT-X for a while i noticed that the manual upload-procedure to qrz.com is rather boring.
This script fixes it - being triggered every minute by cron, it grabs the "wsjtx_log.adi" and the uploads the QSO-records.

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
will usually make things work.

Then, put the adi_to_qrz.py into your WSJT-X log directory (by default  "~/.local/share/WSJT-X") and create a cronjob like this:

```
pi@raspberrypi:~ $ crontab -l

* * * * * cd ~/.local/share/WSJT-X && python adi_to_qrz.py -d -a "My_Api_Key_Here"
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
 -h  --help              print this usage and exit
 -a  --apikey            setting apikey for api-connection
 -h  --inputfile         setting inputfile, default: wsjtx_log.adi
 -e  --enable-idle-log   log idle message "The source file in is empty; doing nothing" on every run
 -l  --logfile           setting logfile, default: adi_to_qrz.log
 -d  --delete            empty the inputfile after import, default: no
```

The only mandatory option is "-a" - sure, you have to provide a valid API-key for QRZ.com logbook-access. Where do you get one?
Please, just google for it https://www.google.de/search?q=qrz+logbook+api+key.

Beside of specifying the apikey as "-a" option you can also set it as environment variable "APIKEY".

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

### Links

* WSJT-X: https://physics.princeton.edu/pulsar/k1jt/wsjtx.html
* ADIF format specs: http://www.adif.org (v1/v2/v3)
* QRZ API PDF: http://files.qrz.com/static/qrz/The%20QRZ%20Logbook%20API.pdf
