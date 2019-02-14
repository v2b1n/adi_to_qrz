# adi_to_qrz

This python script uploads your ADI-logfile to qrz.com logbook.

## Why?
My WSJT-X runs on a raspberry pi. After having used the WSJT-X for a while i noticed that the manual upload-procedure to qrz.com is rather boring.
This script should fix it - being triggered every 10 minutes by cron, it grabs the "wsjtx_log.adi" and the uploads the QSO-records.

## System requirements

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


## Usage

As the "help" sections shows, the usage is pretty straightforward

```
./adi_to_qrz.py  -h
Usage: adi_to_qrz.py [options]
 -h  --help      print this usage and exit
 -a  --apikey    setting apikey for api-connection
 -i  --inputfile setting inputfile, default: wsjtx_log.adi
 -l  --logfile   setting logfile, default: adi_to_qrz.log
 -d  --delete    empty the inputfile after import, default: no
```

The only mandatory option is "-a" - sure, you have to provide a valid API-key for QRZ.com logbook-access. Where do you get one?
Please, just google for it https://www.google.de/search?q=qrz+logbook+api+key.

Beside of specifying the apikey as "-a" option you can also set it as environment variable "APIKEY".

All actions are logged into a logfile.
To disable logfile writing entirely specify "-l null".

All ADI-log-records rejected by QRZ-server are stored into a file that is named "YYYMMDD_HHmm_failed_records.adi", where YYYYMMDD_HHmm is the current date and time.

## Example

In my case the script resides directly in the WSJT-X directory and is executed by following crontab entry:
```
pi@raspberrypi:~ $ crontab -l

*/10 * * * * cd ~/.local/share/WSJT-X && python adi_to_qrz.py -d -a "My_Api_Key_Here"
pi@raspberrypi:~ $
```

# FAQ

* Q: _Will that script overwrite existing entries in the QRZ logbook?_
  * A: No, the script will NOT overwrite your existing entries. It will only add NEW records.

* Q: _Will that script empty/delete my ADI logfile after importing records into QRZ logbook ?_
  * A: By default - no, the script will empty the file you specified for import. If you specify a key "-d" - yes, it will.

* Q: _If i specify "-d" flag so my ADI logfile is emptied - what happens to the erroneous/non-imported QSO-records?_
  * A: All failed records are written into a separate ADI-logfile. The name of this new logfile is "YYYMMDD_HHmm_failed_records.adi", where YYYYMMDD_HHmm is the current date and time.






# Troubleshooting

## Duplicates

The error

> Server response was:"Unable to add QSO to database: duplicate"

is pretty self explanatory. It means that the logbook where you trying to import the qso entry into, already has such an entry.


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

### Links

WSJT-X: https://physics.princeton.edu/pulsar/k1jt/wsjtx.html
ADIF format specs: http://www.adif.org (v1/v2/v3)
QRZ API PDF: http://files.qrz.com/static/qrz/The%20QRZ%20Logbook%20API.pdf
