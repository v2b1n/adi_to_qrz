#!/usr/bin/env python

# Author: Vladimir Vecgailis <vladimir@vovka.de>, DO2VV
# https://www.vovka.de/v2b1n/adi_to_qrz/
#
# This program is distributed under terms of GPL.
#
# v0.2

import io
import logging
import os
import requests
import sys
import time
import datetime
import getopt

import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
PATH = os.path.dirname(os.path.abspath(__file__))

apikey = "APIKEY_NOT_SPECIFIED"
apiurl = "https://logbook.qrz.com/api"
logfile = os.path.basename(__file__).split(".")[0] + ".log"
inputfile = "wsjtx_log.adi"
failed_records = []
delete = False
idle_log = False

def add_record(record):
    global apikey
    global apiurl
    payload = {'KEY': apikey, 'ACTION': 'INSERT', 'ADIF': record }
    call = ""

    # Find CALL in record and set it for later use
    for x in record.split('<'):
        if x == "" or x.startswith("eor>") or x.startswith("EOR>"):
            next
        else:
            key = x.split(':')[0].lower()
            value = x.split('>')[1]
            if key == "call":
                call = value.strip()

    try:
        r = requests.post(apiurl, data = payload)
    except Exception as c:
        logger.error("Could not connect to "+ apiurl)
        exit(1)
    else:
        if ( r.status_code == 200 ):
            params = dict(x.split('=') for x in r.text.split('&'))


            if 'RESULT' in params:
                if params['RESULT'] == "OK":
                    logger.info("QSO record with "+ call +" added")
                else:
                    failed_records.append(record)
                    if 'REASON' in params:
                        reason = params['REASON']
                    else:
                        reason = "No failure reasons provided by server"
                    logger.error("Insert of QSO with " + call +" failed(Server response was: \"" + reason +"\")")
                    logger.error("Failed record: " + record )

            if 'STATUS' in params:
                if params['STATUS'] == "FAIL":
                    failed_records.append(record)
                    if 'REASON' in params:
                        reason = params['REASON']
                    else:
                        reason = "No failure reasons provided by server"

                    logger.error("Insert of QSO with " + call +" failed(Server response was:\"" + reason +"\")")
                    logger.error("Failed record: " + record )
        else:
            logger.error("The server responded with http-code " + str(r.status_code) + " upon submission of QSO with " + call)
            exit(1)


def print_help():
    print("Usage: " + os.path.basename(__file__) + " [options]")
    print(" -h  --help              print this usage and exit")
    print(" -a  --apikey            setting apikey for api-connection")
    print(" -i  --inputfile         setting inputfile, default: wsjtx_log.adi")
    print(" -e  --enable-idle-log   log even if the log is empty")
    print(" -l  --logfile           setting logfile, default: "+ os.path.basename(__file__).split(".")[0] + ".log")
    print(" -d  --delete            empty the inputfile after import, default: no")
    exit(0)

def main():
    global logfile
    global apikey
    global inputfile
    global delete

    if 'APIKEY' in os.environ:
        apikey = os.environ['APIKEY']

    # grab opts
    options, remainder = getopt.gnu_getopt(sys.argv[1:],
        'l:a:hedi:',
        ['logfile=', 'apikey=', 'help', 'idle_log','delete', 'inputfile=', ])

    # check opts
    for opt, arg in options:
        if opt in ('-l', '--logfile'):
            logfile = arg
        elif opt in ('-a', '--apikey'):
            apikey = arg
        elif opt in ('-d', '--delete'):
            delete = True
        elif opt in ('-e', '--enable-idle-log'):
            idle_log = True
        elif opt in ('-h', '--help'):
            print_help()
        elif opt in ('-i', '--inputfile'):
            inputfile = arg

    # now check whether everything needed is given - at least apikey & inputfile
    # must be present
    if apikey in ('', 'APIKEY_NOT_SPECIFIED'):
        logger.error("API key for qrz.com not specified. Please use either \"-a\" key or set environment variable \"APIKEY\".")
        exit(2)

    if not os.path.isfile(inputfile):
        logger.error("The inputfile " + inputfile + " does not exist")
        exit(3)

    # AND write a file
    if logfile != "null":
        fhandler = logging.FileHandler(logfile)
        fhandler.setFormatter(formatter)
        logging.getLogger().addHandler(fhandler)

    with open(inputfile) as f:
        lines = [line.rstrip('\n') for line in open(inputfile)]
    print("marker #1")

    print("Lines: ",len(lines))
    if len(lines) < 1 or (len(lines) == 1 and lines[0].endswith("ADIF Export<eoh>")):
        print("marker #2")
        if idle_log == True:
            print("Case 0")
            logger.info("The source file " + inputfile + " is empty; doing nothing")
        else:
            #logger.handlers = []
            #
            #logger = logging.getLogger()
            #formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
            #handler = logging.StreamHandler()
            #handler.setFormatter(formatter)
            #logger.addHandler(handler)
            print("Case 1")
            logger.info("The source file " + inputfile + " is empty; doing nothing")
        exit(0)
    print("marker #3")

    # per record - add
    for line in lines:
        print("marker #4")
        if line.endswith("<EOR>") or line.endswith("<eor>"):
            add_record(line)

    print("marker #5")
    # now, if there are any failed records - write them into a separate file
    if len(failed_records) > 0:
        failed_records_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_failed_records.adi"
        logger.info("Writing " + str(len(failed_records)) + " failed records into file " + failed_records_file)
        try:
            f = open(failed_records_file, "w")
            f.write("ADIF Export<eoh>\n")
            for failed in failed_records:
                f.write(failed + "\n")
            f.close();
        except Exception as e:
            logger.error("Could not write failed records into " + failed_records_file)
            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            if delete == True:
                logger.warn("Will *not* empty " + inputfile + " due to error above")
            exit(1)
        else:
            # if succeeded writing down failed records - empty the source file, if "-d" flag was provided
            if delete == True:
                logger.info("Emptying the source file " + inputfile)
                try:
                    f = open(inputfile, "w")
                    f.write("ADIF Export<eoh>\n")
                    f.close()
                except Exception as e2:
                    logger.error("Could not empty " + inputfile)
                    logger.error("I/O error({0}): {1}".format(e2.errno, e2.strerror))
                    exit(1)



########################################

if __name__ == "__main__":
    main()
