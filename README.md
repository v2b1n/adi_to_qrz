## adi_to_qrz

This python script uploads your ADI-logfile to qrz.com logbook.

## Why?
My WSJT-X runs on a raspberry pi. After having used the WSJT-X for a while i noticed that the manual upload-procedure to qrz.com is rather boring.
This script should fix it - being triggered every 10 minutes by cron, it grabs the "wsjtx_log.adi" and the uploads the QSO-records.


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
