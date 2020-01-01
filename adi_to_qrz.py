#!/usr/bin/env python

# Author: Vladimir Vecgailis <vladimir@vovka.de>, DM2VV
# https://www.vovka.de/v2b1n/adi_to_qrz/
#
# This program is distributed under terms of GPL.
#
# v0.4

import io
import logging
import os
# https://2.python-requests.org//de/latest/user/quickstart.html
import requests
import sys
import time
import datetime
import getopt
import xmltodict
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)
PATH = os.path.dirname(os.path.abspath(__file__))

xmlkey = "QRZ_COM_XMLKEY"
xmlurl = "http://xmldata.qrz.com/xml/current/"
xml_username = "QRZ_COM_USERNAME"
xml_password = "QRZ_COM_PASSWORD"
xml_userdata = {}
userdata = {}

apikey = "QRZ_COM_APIKEY"
apiurl = "https://logbook.qrz.com/api"

logfile = os.path.basename(__file__).split(".")[0] + ".log"
inputfile = "wsjtx_log.adi"
failed_records = []
delete = False
idle_log = False


def get_xml_session_key():
    global xmlurl,xmlkey,xml_username,xml_password

    # either set the provided key
    if 'XMLKEY' in os.environ:
        xmlkey = os.environ['XMLKEY']
    else:
        level.debug("Checking xmlkey...")
        # login
        #http://xmldata.qrz.com/xml/current/?username=xx1xxx;password=abcdef

        # or ...
        # TODO:
        # check whether there is a cached key
            # if there is a cached key, check it's validity
            # if no more valid, get a new one
        # set the cached || retrieved key


def fetch_callsign_data(call):
    global xmlkey,xmlurl,userdata

    call = call.upper()

    #
    # http://xmldata.qrz.com/xml/current/?s=f894c4bd29f3923f3bacf02c532d7bd9;callsign=aa7bq
    logger.debug("Fetching callsign data for "+ call)

    # dict operations
    # https://www.w3schools.com/python/python_dictionaries.asp


    payload = {'s': xmlkey, 'callsign': call }

    try:
        r = requests.post(xmlurl, data = payload)
    except Exception as c:
        logger.error("Could not connect to "+ xmlurl)
        exit(1)
    else:
        if ( r.status_code == 200 ):
            doc = xmltodict.parse(r.text)

            if 'Error' in doc['QRZDatabase']['Session']:
                logger.error("Error: "+doc['QRZDatabase']['Session']['Error'])
                exit(1)
            else:
                # if no 'Callsign' in the answer for any reason
                if 'Callsign' not in doc['QRZDatabase']:
                    logger.error("Could not find userdata in xml-response body:")
                    logger.error(r.text)
                    #logger.error(r.status_code)
                    #logger.error(r.headers)
                    exit(1)
                else:
                    # success, userdata is present and readable
                    userdata = {}
                    userdata = doc['QRZDatabase']['Callsign']




def fetch_locator():
    global userdata

#    if 'grid' in userdata:
#        logger.info("Grid of user "+userdata['call']+" is "+userdata['grid'])

    return userdata['grid']

def add_record(record):
    global apikey,apiurl
    global userdata

    record = enrich_record(record)

    logger.debug("Will add record "+record)

    payload = {'KEY': apikey, 'ACTION': 'INSERT', 'ADIF': record }
    call = ""

    # independently of the xml-lookup availability -
    # find CALL in record and set it for later use
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
    print(" -x  --xmlkey            setting xmlkey for xml-connection")
    print(" -u  --username          setting username for xml-connection")
    print(" -p  --password          setting password for xml-connection")
    print(" -i  --inputfile         setting inputfile, default: wsjtx_log.adi")
    print(" -e  --enable-idle-log   log idle message \"The source file in is empty; doing nothing\" on every run")
    print(" -l  --logfile           setting logfile, default: "+ os.path.basename(__file__).split(".")[0] + ".log")
    print(" -d  --delete            empty the inputfile after import, default: no")
    exit(0)

def main():
    global logfile
    global apikey,apiurl
    global xmlkey,xml_username,xml_password
    global inputfile
    global delete
    global idle_log

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
        elif opt in ('-x', '--xmlkey'):
            xmlkey = arg
        elif opt in ('-u', '--username'):
            xml_username = arg
        elif opt in ('-p', '--password'):
            xml_password = arg
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
    if apikey in ('', 'QRZ_COM_APIKEY'):
        logger.error("API key for qrz.com not specified. Please use either \"-a\" key or set environment variable \"APIKEY\".")
        exit(2)

    #
    get_xml_session_key()

    if not os.path.isfile(inputfile):
        logger.error("The inputfile " + inputfile + " does not exist")
        exit(3)

    # AND write a file
    if logfile != "null":
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

    with open(inputfile) as f:
        lines = [line.rstrip('\n') for line in open(inputfile)]

    if len(lines) < 1 or (len(lines) == 1 and lines[0].endswith("ADIF Export<eoh>")):
        if idle_log == True:
            logger.info("The source file " + inputfile + " is empty; doing nothing")
        else:
            logger.handlers = []
            logger.addHandler(stdout_handler)
            logger.info("The source file " + inputfile + " is empty; doing nothing")
        exit(0)

    # per record - add
    for line in lines:
        if line.endswith("<EOR>") or line.endswith("<eor>"):
            add_record(line)

    # now, if there are any failed records - write them into a separate file
    if len(failed_records) > 0:
        failed_records_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_failed_records.adi"
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
            # and exit NOW, do NOT empty the source file
            exit(1)
        else:
            logger.info("Written " + str(len(failed_records)) + " failed records into file " + failed_records_file)

    # if succeeded writing down failed records (not exited with (1) above) - empty the source file, if "-d" flag was provided
    if delete == True:
        try:
            f = open(inputfile, "w")
            f.write("ADIF Export<eoh>\n")
            f.close()
        except Exception as e2:
            logger.error("Could not empty " + inputfile)
            logger.error("I/O error({0}): {1}".format(e2.errno, e2.strerror))
            exit(1)
        else:
            logger.info("Emptied the source file " + inputfile)


def enrich_record(record):

    if xmlkey in ('', 'QRZ_COM_XMLKEY'):
        logger.warning("XML key for qrz.com not specified. Please use either \"-x\" key or set environment variable \"XMLKEY\".")
        logger.warning("Will *not* try to enrich QSO grid data.")
        #exit(2)
    else:
        # enriching the record data with some values,
        # e.g. adding an at least 6 chars long locator

        data = {}

        # splitting fields
        for x in record.split('<'):
            if x == "" or x.startswith("eor>") or x.startswith("EOR>"):
                next
            else:
                key = x.split(':')[0].upper()
                value = ((x.split('>')[1]).strip()).upper()
                data[key] = str(value)

        if len(data['GRIDSQUARE']) <= 4:
            logger.info("Will try to enrich grid locator data for "+data['CALL'])
            logger.debug("Grid locator currently: "+data['GRIDSQUARE'])
            fetch_callsign_data(data['CALL'])

            new_locator = fetch_locator()
            if (len(new_locator) >= 6):
                logger.info("Updating "+data['CALL']+" locator from "+data['GRIDSQUARE']+" to "+new_locator)
                data['GRIDSQUARE'] = new_locator
                logger.debug("Old record: "+record)
                # constructing back the ADIF record since data was modified
                record = ""
                for element in data:
                    record += "<" + element.lower() + ":" + str(len(data[element])) + ">" + str(data[element]) + " "
                record += " <eor>"
                logger.debug("New record: "+record)
            else:
                logger.info("No precise locator data found; leaving record untouched")

    return record



########################################

if __name__ == "__main__":
    main()
