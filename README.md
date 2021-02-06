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

## qrz.com account requirements
Please keep in mind, that to be able to upload logs automatically you need a valid qrz.com account **and have a valid subcription**. It is needed needed to get the Logbook API key which is used for uploads via the API. The subscription is also needed for the xml-lookups. The "XML Logbook Data Subscription" is sufficient.

## System requirements & installation instructions

### API-key
To authenticate agains qrz.com an api-key for the your logbook, where the QSOs will be imported, is needed. Right the first search result in https://www.google.de/search?q=qrz+logbook+api+key will lead you to QRZ.com forum where you will get the answer how to find the api-key.


### For Linux users

Beside regular python installation, following python package is required:
```
python-requests
python-xmltodict
python-dateutil
```

On a debian-based linux-distro a
```
apt-get update
apt-get -y install python-requests python-xmltodict python-dateutil
```
will usually make things work. All other distros should try

```
python -m pip install requests xmltodict dateutils
```

Then, put the [adi_to_qrz.py](https://gitlab.com/v2b1n/adi_to_qrz/-/raw/master/adi_to_qrz.py?inline=false) into your WSJT-X log directory (by default  "~/.local/share/WSJT-X") and create a cronjob like this:

```
pi@raspberrypi:~ $ crontab -l

MAILTO=""
# trigger every 5 minutes
*/5 * * * * cd ~/.local/share/WSJT-X && python adi_to_qrz.py -x -a "My_Api_Key_Here"
pi@raspberrypi:~ $

```

### For Windows users

1. Grab the latest python 3.X release from https://www.python.org/downloads/windows/ and install it. When installing, tick the "Add Python 3.X to PATH" checkbox.

2. Grab and launch the [install_prerequisites.cmd](https://gitlab.com/v2b1n/adi_to_qrz2/-/raw/master/windows/install_prerequisites.cmd?inline=false) - this one will install the required python packages. You can also install them on your own by issuing ```python -m pip install install requests xmltodict dateutils``` in the windows terminal.

3. Grab the latest release of [adi_to_qrz.py](https://gitlab.com/v2b1n/adi_to_qrz2/-/raw/master/adi_to_qrz.py?inline=false) and put it into your WJCT-X log directory (the default is ```C:\Users\$USERNAME\AppData\Local\WSJT-X```, *where* **$USERNAME** *is your username*)

4. Add a scheduled task that enter the WSJT-X directory and trigger "adi_to_qrz.py" every X minutes. (How? Please google for "How to create an automated task using Task Scheduler on Windows").

Important points when creating a task are:
  *  "General" tab ([screenshot 1](https://gitlab.com/v2b1n/adi_to_qrz2/-/raw/master/windows/task1.png)):
      * Choose here "Run whether user is logged on or not" and "Do not store password" options.
  *  "Trigger" tab ([screenshot 2](https://gitlab.com/v2b1n/adi_to_qrz2/-/raw/master/windows/task2.png)):
      *  Create here a "trigger" that will be execute the task that often how you define it. In my example i execute it every minute.
  * "Action" tab ([screenshot 3](https://gitlab.com/v2b1n/adi_to_qrz2/-/raw/master/windows/task3.png)) items should be:
    * Action: ```Start a program```
    * Program/script: ```C:\Users\$USERNAME\AppData\Local\Programs\Python\Python39-32\python.exe```
      * alter the path accordingly - **$USERNAME** should be your username and the python directory (here "Python39-32") the one where you've installed python
    * Add Arguments: ```C:\Users\$USERNAME\AppData\Local\WSJT-X\adi_to_qrz.py -a "your-api-key"```
      * Here ^^ you have to put your api-key
      * if you want to add other arguments - like ```-d``` to delete the existing log-entries or ```-x``` to do Locator-lookups - add them also to the list of arguments above, e.g.
      * ```C:\Users\$USERNAME\AppData\Local\WSJT-X\adi_to_qrz.py -a "your-api-key" -d -x```
    * Start in : ```C:\Users\$USERNAME\AppData\Local\WSJT-X```

### For Mac OS users
(will follow; any contributions are welcome)

## Usage

As the "help" sections shows, the usage is pretty straightforward

```
./adi_to_qrz.py  -h
Usage: adi_to_qrz.py [options]
 -h  --help             print this usage and exit
 -a  --apikey           setting apikey for api-connection
 -x  --xmllookups       make grid data lookups over qrz.com's xml-interface, default: no
 -u  --username         qrz.com username for xml-lookups
 -p  --password         qrz.com password for xml-lookups
 -i  --inputfile        setting inputfile, default: wsjtx_log.adi
 -e  --enable-idle-log  log idle message "The source file in is empty; doing nothing" on every run
 -l  --logfile          setting logfile, default: adi_to_qrz.log
 -d  --delete           empty the inputfile after import, default: no
     --debug            enable debugging output
```

The only mandatory option is "-a" - sure, you have to provide a valid API-key for QRZ.com logbook-access.

Beside of specifying the api-key as "-a" option you can also set it as environment variable "APIKEY".

qrz.com username and password can be provided as options -u/--username && -p/--password or as environment variables: "QRZ_COM_USERNAME" and "QRZ_COM_PASSWORD".

All actions are logged into a logfile.

To disable logfile writing entirely specify "-l null".

All ADI-log-records rejected by QRZ-server are stored into a file that is named "YYYMMDD_HHmm_failed_records.adi", where YYYYMMDD_HHmm is the current date and time.



# FAQ

* Q: _Will that script overwrite existing entries in the QRZ logbook? 
  * A: No, the script will NOT overwrite your existing entries. It will only add NEW records.


* Q: _Will that script empty/delete my ADI logfile after importing records into QRZ logbook ? 
  * A: By default - no, the script will NOT empty the file you specified for import. If you specify a key "-d" - yes, it will.


* Q: _If i specify "-d" flag so my ADI logfile is emptied - what happens to the erroneous/non-imported QSO-records? 
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

In most cases the server responses with a more or less self-explanatory message like

> Server response was:"QRZ Internal Error: Unable to add QSO to database. add_qso: outside date range"

E.g "add_qso: outside date range" means that the the QSO does not "fit" into logbook's date-range (which is specified when creating the logbook)

## "Things still does not work as expected!"

Please run the program with the "--debug" flag. In most cases the error message shows clearly what the actual problem is - either a broken log-file, or weird formatted entries/fields & you can possibly fix is on your own.

## "Can't figure out what the error is! Please help!"

If you still cannot handle the problems or the run of the program show  some python code errors - feel free to open an issue at https://gitlab.com/v2b1n/adi_to_qrz/issues/new, describe the problem and
provide
* the adi-logfile that makes troubles
* the log from the "--debug" program run
* output of ```python -V```
* the info which adi_to_qrz.py program version you are using


# Links

* WSJT-X: https://physics.princeton.edu/pulsar/k1jt/wsjtx.html
* ADIF format specs: http://www.adif.org (v1/v2/v3)
* qrz.com REST API PDF: http://files.qrz.com/static/qrz/The%20QRZ%20Logbook%20API.pdf
* qrz.com xml interface specification https://www.qrz.com/XML/current_spec.html
* lotw developer information https://lotw.arrl.org/lotw-help/developer-information/
