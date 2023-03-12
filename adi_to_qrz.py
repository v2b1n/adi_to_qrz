#!/usr/bin/env python3

# Author: Vladimir Vecgailis <vladimir@vovka.de>, DM2VV
# https://www.vovka.de/v2b1n/adi_to_qrz/
#
# This program is distributed under terms of GPL.
#

from __future__ import print_function

import datetime
import getopt
import logging
import os
import re
import sys
from hashlib import sha1

import requests
import xmltodict

PROGRAM_NAME = "adi_to_qrz"
PROGRAM_VERSION = "0.8"
PROGRAM_URL = "https://www.vovka.de/v2b1n/adi_to_qrz/"

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

LOGGER = logging.getLogger()
FORMATTER = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
STDOUT_HANDLER = logging.StreamHandler()
STDOUT_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(STDOUT_HANDLER)
PATH = os.path.dirname(os.path.abspath(__file__))

XMLKEY = "QRZ_COM_XMLKEY"
XMLURL = "http://xmldata.qrz.com/xml/current/"
XML_USERNAME = "QRZ_COM_USERNAME"
XML_PASSWORD = "QRZ_COM_PASSWORD"
XML_USERDATA = {}
XML_LOOKUPS = False
USERDATA = {}
APIKEY = "QRZ_COM_APIKEY"
APIURL = "https://logbook.qrz.com/api"
LOGFILE = os.path.basename(__file__).split(".")[0] + ".log"
INPUTFILE = "wsjtx_log.adi"
RECORD_CACHE = "record_cache.txt"
PROCESSED_RECORDS = 0
CACHED_RECORDS = 0
FAILED_RECORDS = []
IGNORED_RECORDS = 0
ADDED_RECORDS = 0
DELETE_FLAG = False
WRITE_IDLE_LOG = False
DEBUG_FLAG = False
EXITCODE = 0


# Getting/Refreshing XML session-key
def get_xml_session_key():
    global XMLURL, XMLKEY, XML_USERNAME, XML_PASSWORD

    session_key_cache = ".session_key"

    # either set the provided key
    if 'XMLKEY' in os.environ:
        XMLKEY = os.environ['XMLKEY']
        return

    # try to read the cached key
    try:
        with open(session_key_cache) as file:
            XMLKEY = file.read()
            XMLKEY = XMLKEY.strip()
            LOGGER.debug("Session file exists, cached session key %s", str(XMLKEY))

            # validate by doing a dxcc fetch for entity 291 (USA)
            LOGGER.debug("Validating session key")

            payload = {'s': XMLKEY, 'dxcc': "291"}

            try:
                response = requests.post(XMLURL, data=payload)
            except Exception:
                LOGGER.error("Could not connect to %s", XMLURL)
                exit(1)
            else:
                if response.status_code == 200:
                    doc = xmltodict.parse(response.text)

                    if 'Error' in doc['QRZDatabase']['Session']:
                        if doc['QRZDatabase']['Session']['Error'] == "Session Timeout":
                            LOGGER.info("Session  is expired")
                        elif doc['QRZDatabase']['Session']['Error'] == "Invalid session key":
                            LOGGER.info("Session key is no more valid")
                        else:
                            LOGGER.error(
                                "An error occured when validating session key: %s", doc['QRZDatabase']['Session'][
                                    'Error'])

                        XMLKEY = ""
                    else:
                        LOGGER.debug("Session key is valid")


    except IOError:
        LOGGER.debug("Session file does not exist")
        XMLKEY = ""

    # if still empty - then it has to be retrieved & saved
    if XMLKEY == "":
        LOGGER.debug("Getting a new session key")

        payload = {'username': XML_USERNAME, 'password': XML_PASSWORD, 'agent': PROGRAM_NAME + "/" + PROGRAM_VERSION}

        try:
            response = requests.post(XMLURL, data=payload)
        except Exception:
            LOGGER.error("Could not connect to %s", XMLURL)
            exit(1)
        else:
            if response.status_code == 200:
                doc = xmltodict.parse(response.text)

                if 'Error' in doc['QRZDatabase']['Session']:
                    LOGGER.error("Error: %s", doc['QRZDatabase']['Session']['Error'])
                    exit(1)
                else:
                    # if no 'Callsign' in the answer for any reason
                    if 'Key' not in doc['QRZDatabase']['Session']:
                        LOGGER.error("Could not find session key in xml-response")
                        LOGGER.debug(response.headers)
                        LOGGER.debug(response.text)
                        exit(1)
                    else:
                        # success, key is present and readable
                        XMLKEY = doc['QRZDatabase']['Session']['Key']
                        LOGGER.debug("Have retrieved and set xmlkey %s", XMLKEY)
                        LOGGER.info("Successfully retrieved a new session key")
                        # caching it
                        try:
                            file = open(session_key_cache, "w")
                            file.write(XMLKEY)
                            file.close()
                            LOGGER.debug("Written session key into %s", session_key_cache)
                        except IOError as e:
                            LOGGER.error("Could not write session key cache file %s", session_key_cache)
                            LOGGER.error("I/O error({0}): {1}".format(e.errno, e.strerror))
                            exit(1)


def fetch_callsign_data(call):
    global XMLKEY, XMLURL, USERDATA

    call = call.upper()

    LOGGER.debug("Fetching callsign data for %s", call)

    payload = dict(s=XMLKEY, callsign=call)

    try:
        response = requests.post(XMLURL, data=payload)
    except Exception:
        LOGGER.error("Could not connect to %s", XMLURL)
        exit(1)
    else:
        if response.status_code == 200:
            doc = xmltodict.parse(response.text)

            if 'Error' in doc['QRZDatabase']['Session']:
                if re.match("Not found.*", doc['QRZDatabase']['Session']['Error']):
                    LOGGER.info("Call %s was not found on qrz.com", call)
                else:
                    LOGGER.error("Some unhandled error occured: %s", doc['QRZDatabase']['Session']['Error'])
                    LOGGER.debug(response.headers)
                    LOGGER.debug(response.text)
                    exit(1)
            else:
                if 'Callsign' in doc['QRZDatabase']:
                    # success, userdata is present and readable
                    USERDATA = {}
                    USERDATA = doc['QRZDatabase']['Callsign']
                else:
                    # if no 'Callsign' in the answer for any reason
                    LOGGER.error("Could not find userdata in xml-response body:")
                    LOGGER.debug(response.headers)
                    LOGGER.debug(response.text)
                    exit(1)


def fetch_locator():
    global USERDATA

    if 'grid' in USERDATA:
        return USERDATA['grid']
    else:
        return ""


def add_record(record):
    global APIKEY, APIURL
    global USERDATA
    global EXITCODE
    global ADDED_RECORDS

    # filtering of the record in general is not done for simple reason:
    # - comment/info/<nameit> fields *may* contain language-specific chars
    # trying to catch all the possibilities is not really useful.
    # It's up to users program to properly log records.
    # So will pass the stuff 1:1 to qrz.com.
    original_record = record
    record = enrich_record(record)

    LOGGER.debug("Will try to add record \"%s\"", record)

    payload = {'KEY': APIKEY, 'ACTION': 'INSERT', 'ADIF': record}
    call = ""

    # independently of the xml-lookup availability -
    # find CALL in record and set it for later use
    for chunk in record.split('<'):
        # filtering out weird stuff in fields when looking for a "call"
        chunk = re.sub('[^\w\s:<>\-]+', '', chunk)
        if chunk == "" or chunk.startswith("eor>") or chunk.startswith("EOR>"):
            continue
        else:
            key = chunk.split(':')[0].lower()
            value = chunk.split('>')[1]
            if key == "call":
                call = value.strip()

    try:
        response = requests.post(APIURL, data=payload)
    except Exception:
        LOGGER.error("Could not connect to %s", APIURL)
        exit(1)
    else:
        if response.status_code == 200:
            params = dict(x.split('=') for x in response.text.split('&'))

            if 'RESULT' in params:

                if params['RESULT'] == "OK":
                    LOGGER.info("QSO record with %s added", call)
                    ADDED_RECORDS = ADDED_RECORDS + 1
                    add_record_to_cache(original_record)
                else:
                    FAILED_RECORDS.append(record)
                    if 'REASON' in params:
                        reason = params['REASON']
                    else:
                        reason = "No failure reasons provided by server"
                    LOGGER.error("Insert of QSO with %s failed.", call)
                    LOGGER.error("Server response was: \"%s\"", reason)
                    LOGGER.debug("Failed record: %s", record)
                    EXITCODE = 1


            if 'STATUS' in params:

                if params['STATUS'] == "FAIL" or params['STATUS'] == "AUTH":
                    FAILED_RECORDS.append(record)
                    if 'REASON' in params:
                        reason = params['REASON']
                    else:
                        reason = "No failure reasons provided by server"
                    if 'EXTENDED' in params:
                        reason += " " + params['EXTENDED']

                    LOGGER.error("Insert of QSO with %s failed", call)
                    LOGGER.error("Server response was: \"%s\"", reason)
                    LOGGER.debug("Failed record: %s", record)
                    if "duplicate" in reason:
                        if DELETE_FLAG is False:
                            LOGGER.info(
                                "Since servers complain was \"duplicate\" - i assume the record is added to QRZ, so, adding that record to local cache too")
                            add_record_to_cache(original_record)
                    EXITCODE = 1
        else:
            LOGGER.error(
                "The server responded with http-code %s upon submission of QSO with %s", str(response.status_code),
                call)
            exit(1)


def find_cached_record(record):
    global IGNORED_RECORDS

    LOGGER.debug("Looking for record in cache: %s", str(record))
    record_hash = sha1(record.encode('utf-8')).hexdigest()

    try:
        with open(RECORD_CACHE, 'r') as file:
            # Read all lines in the file one by one
            for line in file:
                # For each line, check if line contains the string
                if record_hash in line:
                    LOGGER.debug("Hash entry %s for record \"%s\" found in cache", record_hash, record)
                    LOGGER.debug("Will not try to add that entry to logbook")
                    IGNORED_RECORDS = IGNORED_RECORDS + 1
                    return True
    except IOError:
        LOGGER.debug("Record cache file does not exist")
        return False
    file.close()
    return False


def add_record_to_cache(record):
    global DELETE_FLAG
    global CACHED_RECORDS

    if DELETE_FLAG:
        LOGGER.debug("Delete-flag is active - will not add the entry to cache")
    else:
        LOGGER.debug("Adding record to cache: %s", str(record))
        record_hash = sha1(record.encode('utf-8')).hexdigest()
        try:
            f = open(RECORD_CACHE, "a")
            f.write(record_hash + ":" + record + os.linesep)
            f.close()
            CACHED_RECORDS = CACHED_RECORDS + 1
        except IOError as e:
            LOGGER.error("Could not write into record_cache cache file %s", RECORD_CACHE)
            LOGGER.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            exit(1)


def print_help():
    print("")
    print(PROGRAM_NAME + " v" + PROGRAM_VERSION + " ( " + PROGRAM_URL + " )")
    print("")
    print("Usage: " + os.path.basename(__file__) + " [options]")
    print(" -h  --help              print this usage and exit")
    print(" -a  --apikey            setting apikey for api-connection")
    print(" -x  --xmllookups        make grid data lookups over qrz.com's xml-interface, default: no")
    print(" -u  --username          qrz.com username for xml-lookups")
    print(" -p  --password          qrz.com password for xml-lookups")
    print(" -i  --inputfile         setting inputfile, default: wsjtx_log.adi")
    print(
        " -e  --enable-idle-log   log message \"The source file is empty; doing nothing\" on every run if logfile is empty")
    print(" -l  --logfile           setting logfile, default: " + os.path.basename(__file__).split(".")[0] + ".log")
    print(" -d  --delete            empty the inputfile after import, default: no")
    print("     --debug             enable debugging output")
    print(" -v  --version           print program version and exit")
    print("")
    exit(0)


def print_version():
    print("")
    print(PROGRAM_NAME + " v" + PROGRAM_VERSION + " ( " + PROGRAM_URL + " )")
    print("")
    exit(0)


def enrich_record(record):
    if XMLKEY in ('', 'QRZ_COM_XMLKEY'):
        LOGGER.debug("XMLKEY not set; missing qrz.com username/password. Will *not* try to enrich QSO grid data.")
    else:
        # enriching the record data with some values,
        # e.g. adding an at least 6 chars long locator

        data = {}

        # splitting fields
        for entry in record.split('<'):
            if entry == "" or entry.startswith("eor>") or entry.startswith("EOR>"):
                LOGGER.debug("Ignoring field: %s", entry)
            else:
                # trying to split the line
                key = ""
                try:
                    key = entry.split(':')[0].upper()
                except ValueError:
                    LOGGER.debug("Failed to extract key from \"%s\"", entry)

                # ignoring keys with weird stuff in names
                # the only permitted chars are "[A-Z0-9_]", thus "\w"
                # So, if anything else is present - it can't be right, ignoring the key then
                if re.match('[^\w]+', key):
                    LOGGER.debug("Ignoring key: %s", key)
                else:
                    value = ((entry.split('>')[1]).strip()).upper()
                    data[key] = str(value)

        if len(data['GRIDSQUARE']) <= 4:
            if data['GRIDSQUARE'] == "":
                data['GRIDSQUARE'] = "(not provided)"
            LOGGER.debug("Will try to enrich grid locator data for %s", data['CALL'])
            LOGGER.debug("Grid locator from wsjtx_log.adi: %s", data['GRIDSQUARE'])
            fetch_callsign_data(data['CALL'])

            new_locator = fetch_locator()
            if len(new_locator) >= 6:
                LOGGER.info("Updating %s locator from %s to %s", data['CALL'], data['GRIDSQUARE'], new_locator)
                data['GRIDSQUARE'] = new_locator
                LOGGER.debug("Old record: %s", record)
                # constructing back the ADIF record since data was modified
                record = ""
                for element in data:
                    record += "<" + element.lower() + ":" + str(len(data[element])) + ">" + str(data[element]) + " "
                record += " <eor>"
                LOGGER.debug("New record: %s", record)
            else:
                LOGGER.info("No precise locator data found; leaving record untouched")

    return record


def main():
    global LOGFILE, DEBUG_FLAG, EXITCODE
    global APIKEY, APIURL
    global XMLKEY, XML_USERNAME, XML_PASSWORD, XML_LOOKUPS
    global INPUTFILE
    global DELETE_FLAG
    global WRITE_IDLE_LOG
    global PROCESSED_RECORDS

    # grab variables if present in environment
    if 'APIKEY' in os.environ:
        APIKEY = os.environ['APIKEY']

    if 'QRZ_COM_USERNAME' in os.environ:
        XML_USERNAME = os.environ['QRZ_COM_USERNAME']

    if 'QRZ_COM_PASSWORD' in os.environ:
        XML_PASSWORD = os.environ['QRZ_COM_PASSWORD']

    # grab opts
    options, rest = getopt.gnu_getopt(sys.argv[1:],
                                      'l:a:hedi:xu:p:v',
                                      ['logfile=', 'apikey=', 'help', 'idle_log', 'delete', 'inputfile=',
                                       'xmllookups', 'username=', 'password=', 'debug', 'version'])

    # check opts
    for opt, arg in options:
        if opt in ('-l', '--logfile'):
            LOGFILE = arg
        elif opt in ('-a', '--apikey'):
            APIKEY = arg
        elif opt in ('-x', '--xmllookups'):
            XML_LOOKUPS = True
        elif opt in ('-u', '--username'):
            XML_USERNAME = arg
        elif opt in ('-p', '--password'):
            XML_PASSWORD = arg
        elif opt in ('-d', '--delete'):
            DELETE_FLAG = True
        elif opt in ('-e', '--enable-idle-log'):
            WRITE_IDLE_LOG = True
        elif opt in '--debug':
            DEBUG_FLAG = True
        elif opt in ('-h', '--help'):
            print_help()
        elif opt in ('-v', '--version'):
            print_version()
        elif opt in ('-i', '--inputfile'):
            INPUTFILE = arg

    if DEBUG_FLAG:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    # now check whether everything needed is given - at least apikey & inputfile
    # must be present
    if APIKEY in ('', 'QRZ_COM_APIKEY'):
        print("")
        LOGGER.error(
            "API key for qrz.com not specified. Please use either \"-a\" key or set environment variable \"APIKEY\".")
        print_help()
        exit(2)

    # if xml_lookups are requested, username and password must be provided
    if XML_LOOKUPS:
        if XML_USERNAME in ('', 'QRZ_COM_USERNAME'):
            print("")
            LOGGER.error(
                "Username for qrz.com not specified. Please use either \"-u\" key or set environment variable \"QRZ_COM_USERNAME\".")
            print_help()
            exit(2)

        if XML_PASSWORD in ('', 'QRZ_COM_PASSWORD'):
            print("")
            LOGGER.error(
                "Password for qrz.com not specified. Please use either \"-p\" key or set environment variable \"QRZ_COM_PASSWORD\".")
            print_help()
            exit(2)

        get_xml_session_key()

    # check whether the default/specified inputfile is present
    if not os.path.isfile(INPUTFILE):
        LOGGER.error("The inputfile %s does not exist", INPUTFILE)
        exit(3)

    # create the default/requested logfile
    if LOGFILE != "null":
        file_handler = logging.FileHandler(LOGFILE)
        file_handler.setFormatter(FORMATTER)
        logging.getLogger().addHandler(file_handler)

    with open(INPUTFILE):
        lines = [line.rstrip('\n') for line in open(INPUTFILE)]

    # if the inputfile contains only the header, then there's nothing to do
    if len(lines) < 1 or (len(lines) == 1 and lines[0].endswith("ADIF Export<eoh>")):
        if WRITE_IDLE_LOG:
            LOGGER.info("The source file %s is empty; nothing to do", INPUTFILE)
        else:
            LOGGER.handlers = []
            LOGGER.addHandler(STDOUT_HANDLER)
            LOGGER.info("The source file %s is empty; nothing to do", INPUTFILE)
        exit(0)

    # if it does contain entries - per record - add
    for line in lines:
        if line.endswith("<EOR>") or line.endswith("<eor>"):
            # check local records cache and if the record is not present in it - add the record
            if not find_cached_record(line):
                add_record(line)
            PROCESSED_RECORDS = PROCESSED_RECORDS + 1

    # now, if there are any failed records - write them into a separate file
    if len(FAILED_RECORDS) > 0:
        failed_records_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_failed_records.adi"
        try:
            file = open(failed_records_file, "w")
            file.write("ADIF Export<eoh>\n")
            for failed in FAILED_RECORDS:
                file.write(failed + "\n")
            file.close()
        except IOError as e:
            LOGGER.error("Could not write failed records into %s", failed_records_file)
            LOGGER.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            if DELETE_FLAG:
                LOGGER.warning("Will *not* empty %s due to error above", INPUTFILE)
            # and exit NOW, do NOT empty the source file
            exit(1)
        else:
            LOGGER.info("Written %s failed records into file %s", str(len(FAILED_RECORDS)), failed_records_file)

    # if succeeded writing down failed records (not exited with (1) above) - empty the source file,
    # if "-d" flag was provided
    if DELETE_FLAG:
        try:
            file = open(INPUTFILE, "w")
            file.write("ADIF Export<eoh>\n")
            file.close()
        except IOError as e2:
            LOGGER.error("Could not empty %s", INPUTFILE)
            LOGGER.error("I/O error({0}): {1}".format(e2.errno, e2.strerror))
            exit(1)
        else:
            LOGGER.info("Emptied the source file %s", INPUTFILE)

    stats = "Run statistics - " + str(PROCESSED_RECORDS) + " records processed: "
    name_plural = "records"
    name_singular = "record"
    if ADDED_RECORDS > 0:
        records_name = name_plural
        if ADDED_RECORDS == 1:
            records_name = name_singular
        stats = stats + str(ADDED_RECORDS) + " new " + records_name + " added. "
    if IGNORED_RECORDS > 0:
        records_name = name_plural
        if IGNORED_RECORDS == 1:
            records_name = name_singular
        stats = stats + str(IGNORED_RECORDS) + " cached " + records_name + " ignored. "
    if len(FAILED_RECORDS) > 0:
        records_name = name_plural
        if len(FAILED_RECORDS) == 1:
            records_name = name_singular
        stats = stats + str(len(FAILED_RECORDS)) + " " + records_name + " failed."

    if CACHED_RECORDS > 0 or ADDED_RECORDS > 0 or len(FAILED_RECORDS) > 0:
        LOGGER.info(stats)
    exit(EXITCODE)


########################################

if __name__ == "__main__":
    main()
