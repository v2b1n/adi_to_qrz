## Table of Contents

- [1. Features](#1-features)
- [2. Why?](#2-why)
- [3. Requirements](#3-requirements)
  - [3.1 Supported python-versions](#31-supported-python-versions)
  - [3.2 qrz.com subscription](#32-qrzcom-subscription)
  - [3.3 API-key](#33-api-key)
- [4. Installation instructions](#4-installation-instructions)
  - [4.1 For Linux users](#41-for-linux-users)
  - [4.2 Docker: prepared docker images for amd64](#42-docker-prepared-docker-images-for-amd64)
  - [4.3 Docker: images for arm64: raspberry/Macbooks with M1/M2 CPUs](#43-docker-images-for-arm64-raspberrymacbooks-with-m1m2-cpus)
  - [4.4 For Windows users](#44-for-windows-users)
  - [4.5 For Mac OS users](#45-for-mac-os-users)
- [5. Usage](#5-usage)
- [6. FAQ](#6-faq)
- [7. Troubleshooting](#7-troubleshooting)
  - [7.1 Duplicates](#71-duplicates)
  - [7.2 ADI Log mandatory fields](#72-adi-log-mandatory-fields)
  - [7.3 "Things still does not work as expected!"](#73-things-still-does-not-work-as-expected)
  - [7.4 "Can't figure out what the error is! Please help!"](#74-cant-figure-out-what-the-error-is-please-help)
- [8. Links](#8-links)
- [9. Donations](#9-donations)

<TOC>

# adi_to_qrz

This python script uploads your WSJT-X ADI-logfile to qrz.com logbook. Please see "Features" for a full features list.

## 1. Features[](#features)

* uploads WSJT-X ADI-logfile entries to qrz.com logbook
* keeps track of added records using a local cache
* fetches remote party's grid locator data from qrz.com
  * if desired, can fetch remote party's grid locator data from qrz.com's xml-interface and "enrich" the QSO data with it, before saving in a logbook; while WSJT-X provides only 4 chars of the grid locator, on 2m band the precision of 4 chars long locator vs 6 chars long does make quite a difference in distance calculation.
* keeps erroneous/non-imported QSOs and writes them into a separate file, see FAQ
* empties the ADI-logfile if told to do so

## 2. Why?
My WSJT-X runs on a raspberry pi. After having used the WSJT-X for a while i noticed that the manual upload-procedure to qrz.com is really annoying.
This script fixes it - being triggered every couple of minutes by cron, it grabs the "wsjtx_log.adi" and the uploads the QSO-records.

## 3. Requirements<a id='3.0'></a>

### 3.1 Supported python-versions
The application is tested with following python builds:

* python 3.10
* python 3.11
* python 3.12

So make sure you have one installed for your OS.

### 3.2 qrz.com subscription
To be able to upload logs automatically you need a valid qrz.com account **and have a valid subscription**. It is needed to get the Logbook API key which is used for uploads via the API. The subscription is also needed for the xml-lookups. The "XML Logbook Data Subscription" is sufficient. 
And, no, i'm not affiliated by qzr.com.

### 3.3 API-key
To authenticate against qrz.com an api-key for your logbook, where the QSOs will be imported, is needed. Right the first search result in https://www.google.de/search?q=qrz+logbook+api+key will lead you to QRZ.com forum where you will get the answer how to find the api-key.


## 4. Installation instructions
### 4.1 For Linux users

Beside regular python installation, following python packages are required:
```
python3-requests
python3-xmltodict
python3-dateutil
```

On a debian-based linux-distro an
```
apt-get update
apt-get -y install --no-install-recommends python3-requests python3-xmltodict python3-dateutil
```
will usually make things work.

Other distros should try
```
python3 -m pip install -r requirements.txt
```

Then, put the [adi_to_qrz.py](https://gitlab.com/v2b1n/adi_to_qrz/-/raw/master/adi_to_qrz.py?inline=false) into your WSJT-X log directory (by default  "~/.local/share/WSJT-X") and make it executable:

```
chmod ugo+x adi_to_qrz.py
```

Enter your WSJT-X log directory and create a ```.env``` file. It has to contain your apikey/qrz.com credentials and has to have following structure:

```
# your api-key, this is used to push the data
APIKEY="1234-5678-9012"

# The callsign and password are used for User-data-lookups
# your qrz.com callsign
QRZ_COM_USERNAME="AB1CD"
# your qrz.com password
QRZ_COM_PASSWORD="YourPassWord"
```

At last, create a cronjob using ```crontab -e``` command.

One like this:

```
user@workstation:~ $ crontab -l

MAILTO=""
# trigger every 5 minutes
*/5 * * * * cd ~/.local/share/WSJT-X && . .env && ./adi_to_qrz.py -x
```

### 4.2 Docker: prepared docker images for amd64

Docker users can grab and run the pre-built docker-image.

To run it -

create the ```.env``` file as described in the general linux section above and run:

```
cd ~/.local/share/WSJT-X && docker run --env-file .env -v $(pwd)/:/data/ v2b1n/adi_to_qrz:latest -x
```

or run it via cronjob:

```
user@workstation:~ $ crontab -l

MAILTO=""
# trigger every 5 minutes
*/5 * * * * cd ~/.local/share/WSJT-X && docker run --env-file .env -v $(pwd)/:/data/ v2b1n/adi_to_qrz:latest -x
```

One important notice: current builds are for amd64-architecture only, so dear raspberry/M1/M2-Macbook users - please refer to the next section.


### 4.3 Docker: images for arm64: raspberry/Macbooks with M1/M2 CPUs

As a docker-user you can grab and build the latest version on your own:

```
git clone https://gitlab.com/v2b1n/adi_to_qrz.git
cd adi_to_qrz
docker build . -t v2b1n/adi_to_qrz:latest
```

and then run it as described above in other sections - i.e. as a cronjob.


### 4.4 For Windows users

1. Grab the latest supported python release from https://www.python.org/downloads/windows/ and install it. When installing, tick the "Add Python 3.X to PATH" checkbox.

2. Grab and launch the [install_prerequisites.cmd](https://gitlab.com/v2b1n/adi_to_qrz/-/raw/master/windows/install_prerequisites.cmd?inline=false) - this one will install the required python packages. You can also install them on your own by issuing ```python -m pip install requests xmltodict dateutils``` in the Windows terminal.

3. Grab the latest release of [adi_to_qrz.py](https://gitlab.com/v2b1n/adi_to_qrz/-/raw/master/adi_to_qrz.py?inline=false) and put it into your WSJT-X log directory (the default is ```C:\Users\$USERNAME\AppData\Local\WSJT-X```, *where* **$USERNAME** *is your Windows username*)

4. Add a scheduled task that enter the WSJT-X directory and trigger "adi_to_qrz.py" every X minutes. (How? Please google for "How to create an automated task using Task Scheduler on Windows").

Important points when creating a task are:
  *  "General" tab ([screenshot 1](https://gitlab.com/v2b1n/adi_to_qrz/-/raw/master/windows/task1.png)):
      * Choose here "Run whether user is logged on or not" and "Do not store password" options.
  *  "Trigger" tab ([screenshot 2](https://gitlab.com/v2b1n/adi_to_qrz/-/raw/master/windows/task2.png)):
      *  Create here a "trigger" that will be execute the task that often how you define it. In my example i execute it every minute.
  * "Action" tab ([screenshot 3](https://gitlab.com/v2b1n/adi_to_qrz/-/raw/master/windows/task3.png)) items should be:
    * Action: ```Start a program```
    * Program/script: ```C:\Users\$USERNAME\AppData\Local\Programs\Python\Python39-32\python.exe```
      * alter the path accordingly - **$USERNAME** should be your username and the python directory (here "Python39-32") the one where you've installed python
    * Add Arguments: ```C:\Users\$USERNAME\AppData\Local\WSJT-X\adi_to_qrz.py -a "your-api-key"```
      * Here ^^ you have to put your api-key
      * if you want to add other arguments - like ```-d``` to delete the existing log-entries or ```-x``` to do Locator-lookups - add them also to the list of arguments above, e.g.
      * ```C:\Users\$USERNAME\AppData\Local\WSJT-X\adi_to_qrz.py -a "your-api-key" -d -x```
    * Start in : ```C:\Users\$USERNAME\AppData\Local\WSJT-X```

### 4.5 For Mac OS users
(will follow; any contributions are welcome)

## 5. Usage

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

The only mandatory option is ```-a``` - sure, you have to provide a valid API-key for QRZ.com logbook-access.

Beside of specifying the api-key as ```-a``` option you can also set it as environment variable ```APIKEY```.

qrz.com username and password can be provided as options ```-u```/```--username``` and ```-p```/```--password``` or as environment variables ```QRZ_COM_USERNAME``` and ```QRZ_COM_PASSWORD```.

All actions are logged into a logfile.

To disable logfile writing entirely specify ```-l null```.

All ADI-log-records rejected by QRZ-server are stored into a file that is named ```YYYMMDD_HHmm_failed_records.adi```, where```YYYYMMDD_HHmm``` is the current date and time.

***Important notice:*** when you start the script for the very first time and if your wsjtx_log.adi is NOT empty, the program will attempt to add all the entries to your logbook. If, however, you already added these entries to QRZ.com then this very first run will result in (possibly many) errors ("Unable to add QSO to database: duplicate"). This is naturally expected, since adi_to_qrz has not yet built up a local-cache. 
After this first run adi_to_qrz will add all the failed "duplicate" entries to the local cache and won't complain anymore
in next runs.


## 6. FAQ

* Q: Will that script overwrite existing entries in the QRZ logbook? 
  * A: No, the script will NOT overwrite your existing entries. It will only add NEW records.


* Q: Will that script empty/delete my ADI logfile after importing records into QRZ logbook ? 
  * A: By default - no, the script will NOT empty the file you specified for import. If you specify a key ```-d``` - yes, it will.


* Q: If I specify the ```-d``` flag so that my ADI logfile is getting emptied - what happens to the erroneous/non-imported QSO-records? 
  * A: All failed records are written into a separate ADI-logfile in the same directory. The name of this new logfile is ```YYYMMDD_HHmm_failed_records.adi```, where ```YYYYMMDD_HHmm``` is the current date and time.

## 7. Troubleshooting

### 7.1 Duplicates

The error

> Server response was:"Unable to add QSO to database: duplicate"

is pretty self-explanatory. It means that the logbook where you are trying to import the qso record into, has already such a record. Either you find and delete the QSO-entry from your QRZ.com logbook, or the appropriate record-line from the logfile.


### 7.2 ADI Log mandatory fields

If the import fails, and you spot an error

> Server response was:"QRZ Internal Error: Unable to add QSO to database."

check first whether the mandatory fields are presend in your ADIF-log.

The api of logbook.qrz.com requires that an ADIF QSO-record has at least following mandatory fields:

```
CALL
QSO_DATE
BAND
MODE
```
In most cases the server responses with a more or less self-explanatory message like

> Server response was:"QRZ Internal Error: Unable to add QSO to database. add_qso: outside date range"

E.g "add_qso: outside date range" means that the QSO does not "fit" into your logbook's date-range (which is specified when creating the logbook)

### 7.3 "Things still does not work as expected!"

Please run the program with the "--debug" flag. In most cases the error message shows clearly what the actual problem is - either a broken log-file, or weird formatted entries/fields & you can possibly fix is on your own.

### 7.4 "Can't figure out what the error is! Please help!"

If you still cannot handle the problem, or the run of the program show some python code errors - feel free to open an issue at https://gitlab.com/v2b1n/adi_to_qrz/issues/new, describe the problem and
provide
* output of ```python3 -V```
* output of ```adi_to_qrz.py --version```
* the adi-logfile that makes troubles
* the log from the "--debug" program run

## 8. Links

* WSJT-X: https://physics.princeton.edu/pulsar/k1jt/wsjtx.html
* ADIF format specs: http://www.adif.org (v1/v2/v3)
* qrz.com REST API documentation https://www.qrz.com/docs/logbook/QRZLogbookAPI.html
* qrz.com xml interface specification https://www.qrz.com/XML/current_spec.html
* LOTW developer information https://lotw.arrl.org/lotw-help/developer-information/

## 9. Donations

Like what i'm doing? Donations are welcome

* Paypal [paypal.me/m4vr](paypal.me/m4vr)
* Bitcoin bc1q33y4j9f0t7fw0dd7cawk2dekdp758hunjhxm8z
* Litecoin MGa9NvzVGddAtJT39aa9wHRCYcL3nKXKok
* Ethereum 0x5ebe3b361ba3aab064cb6882e10a3dcc96900ed5
* Monero 46rogMzYmEWhE9MWn8wRAf5GgzgjziUwhYHC5LrtDfqfBm2KKKTxUvKNYv25uB4vTkSSgsw7Mix51eB3iHvvM5WgCbkmwqt
