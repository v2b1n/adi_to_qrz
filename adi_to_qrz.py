#!/usr/bin/env python

# Author: Vladimir Vecgailis <vladimir@vovka.de>, DM2VV
# https://www.vovka.de/v2b1n/adi_to_qrz/
#
# This program is distributed under terms of GPL.
#

import datetime
import getopt
import logging
import os
import re
import sys

import requests
import xmltodict

program_name = "adi_to_qrz"
program_version = "0.5"
program_url = "https://www.vovka.de/v2b1n/adi_to_qrz/"

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
PATH = os.path.dirname(os.path.abspath(__file__))

xmlkey = "QRZ_COM_XMLKEY"
xmlurl = "http://xmldata.qrz.com/xml/current/"
xml_username = "QRZ_COM_USERNAME"
xml_password = "QRZ_COM_PASSWORD"
xml_userdata = {}
xml_lookups = False
userdata = {}
apikey = "QRZ_COM_APIKEY"
apiurl = "https://logbook.qrz.com/api"
logfile = os.path.basename(__file__).split(".")[0] + ".log"
inputfile = "wsjtx_log.adi"
failed_records = []
delete_flag = False
write_idle_log = False
debug_flag = False
exitcode = 0


def get_xml_session_key():
    global xmlurl, xmlkey, xml_username, xml_password

    session_key_cache = ".session_key"

    # either set the provided key
    if 'XMLKEY' in os.environ:
        xmlkey = os.environ['XMLKEY']
        return

    # try to read the cached key
    try:
        with open(session_key_cache) as f:
            xmlkey = f.read()
            xmlkey = xmlkey.strip()
            logger.debug("Cache file exists, cached key " + str(xmlkey))

            # validate by doing a dxcc fetch for entity 291 (USA)
            logger.debug("Validating xmlkey")

            payload = {'s': xmlkey, 'dxcc': "291"}

            try:
                r = requests.post(xmlurl, data=payload)
            except Exception:
                logger.error("Could not connect to " + xmlurl)
                exit(1)
            else:
                if r.status_code == 200:
                    doc = xmltodict.parse(r.text)

                    if 'Error' in doc['QRZDatabase']['Session']:
                        if doc['QRZDatabase']['Session']['Error'] == "Session Timeout":
                            logger.info("Cached key is expired")
                        elif doc['QRZDatabase']['Session']['Error'] == "Invalid session key":
                            logger.info("Cached key is no more valid")
                        else:
                            logger.error(
                                "An error occured when validating cached key: " + doc['QRZDatabase']['Session'][
                                    'Error'])

                        xmlkey = ""
                    else:
                        logger.debug("Session key is valid")


    except IOError:
        logger.debug("Cache file does not exist")
        xmlkey = ""

    # if still empty - then it has to be retrieved & saved
    if xmlkey == "":
        logger.debug("Getting a new xmlkey")

        payload = {'username': xml_username, 'password': xml_password, 'agent': program_name + "/" + program_version}

        try:
            r = requests.post(xmlurl, data=payload)
        except Exception:
            logger.error("Could not connect to " + xmlurl)
            exit(1)
        else:
            if r.status_code == 200:
                doc = xmltodict.parse(r.text)

                if 'Error' in doc['QRZDatabase']['Session']:
                    logger.error("Error: " + doc['QRZDatabase']['Session']['Error'])
                    exit(1)
                else:
                    # if no 'Callsign' in the answer for any reason
                    if 'Key' not in doc['QRZDatabase']['Session']:
                        logger.error("Could not find session key in xml-response")
                        logger.debug(r.headers)
                        logger.debug(r.text)
                        exit(1)
                    else:
                        # success, key is present and readable
                        xmlkey = doc['QRZDatabase']['Session']['Key']
                        logger.debug("Have retrieved and set xmlkey " + xmlkey)
                        logger.info("Successfully retrieved a new session key")
                        # caching it
                        try:
                            f = open(session_key_cache, "w")
                            f.write(xmlkey)
                            f.close()
                            logger.debug("Written session key into " + session_key_cache)
                        except Exception as e:
                            logger.error("Could not write session key cache file " + session_key_cache)
                            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
                            exit(1)


def fetch_callsign_data(call):
    global xmlkey, xmlurl, userdata

    call = call.upper()

    logger.debug("Fetching callsign data for " + call)

    payload = dict(s=xmlkey, callsign=call)

    try:
        r = requests.post(xmlurl, data=payload)
    except Exception:
        logger.error("Could not connect to " + xmlurl)
        exit(1)
    else:
        if r.status_code == 200:
            doc = xmltodict.parse(r.text)

            if 'Error' in doc['QRZDatabase']['Session']:
                if re.match("Not found.*", doc['QRZDatabase']['Session']['Error']):
                    logger.info("Call " + call + " was not found on qrz.com")
                else:
                    logger.error("Some unhandled error occured: " + doc['QRZDatabase']['Session']['Error'])
                    logger.debug(r.headers)
                    logger.debug(r.text)
                    exit(1)
            else:
                if 'Callsign' in doc['QRZDatabase']:
                    # success, userdata is present and readable
                    userdata = {}
                    userdata = doc['QRZDatabase']['Callsign']
                else:
                    # if no 'Callsign' in the answer for any reason
                    logger.error("Could not find userdata in xml-response body:")
                    logger.debug(r.headers)
                    logger.debug(r.text)
                    exit(1)


def fetch_locator():
    global userdata

    if 'grid' in userdata:
        # logger.info("Grid of user "+userdata['call']+" is "+userdata['grid'])
        return userdata['grid']
    else:
        return ""


def add_record(record):
    global apikey, apiurl
    global userdata
    global exitcode

    # filtering of the record in general is not done for simple reason:
    # - comment/info/nameit fields *may* contain language-specific chars
    # trying to catch all the possibilities is not really usefull.
    # It's up to users program to properly log records.
    # So will pass the stuff 1:1 to qrz.com.

    record = enrich_record(record)

    logger.debug("Will try to add record \"" + record + "\"")

    payload = {'KEY': apikey, 'ACTION': 'INSERT', 'ADIF': record}
    call = ""

    # independently of the xml-lookup availability -
    # find CALL in record and set it for later use
    for x in record.split('<'):
        # filtering out weird stuff in fields when looking for a "call"
        x = re.sub('[^\w\s:<>\-]+', '', x)
        if x == "" or x.startswith("eor>") or x.startswith("EOR>"):
            continue
        else:
            key = x.split(':')[0].lower()
            value = x.split('>')[1]
            if key == "call":
                call = value.strip()

    try:
        r = requests.post(apiurl, data=payload)
    except Exception:
        logger.error("Could not connect to " + apiurl)
        exit(1)
    else:
        if r.status_code == 200:
            params = dict(x.split('=') for x in r.text.split('&'))

            if 'RESULT' in params:
                if params['RESULT'] == "OK":
                    logger.info("QSO record with " + call + " added")
                else:
                    failed_records.append(record)
                    if 'REASON' in params:
                        reason = params['REASON']
                    else:
                        reason = "No failure reasons provided by server"
                    logger.error("Insert of QSO with " + call + " failed.")
                    logger.error("Server response was: \"" + reason + "\"")
                    logger.debug("Failed record: " + record)
                    exitcode = 1

            if 'STATUS' in params:
                if params['STATUS'] == "FAIL":
                    failed_records.append(record)
                    if 'REASON' in params:
                        reason = params['REASON']
                    else:
                        reason = "No failure reasons provided by server"
                    if 'EXTENDED' in params:
                        reason += " " + params['EXTENDED']

                    logger.error("Insert of QSO with " + call + " failed")
                    logger.error("Server response was: \"" + reason + "\"")
                    logger.debug("Failed record: " + record)
                    exitcode = 1
        else:
            logger.error(
                "The server responded with http-code " + str(r.status_code) + " upon submission of QSO with " + call)
            exit(1)


def print_help():
    print("")
    print(program_name + " " + program_version + " ( " + program_url + " )")
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
    print("")
    exit(0)


def main():
    global logfile, debug_flag, exitcode
    global apikey, apiurl
    global xmlkey, xml_username, xml_password, xml_lookups
    global inputfile
    global delete_flag
    global write_idle_log

    if 'APIKEY' in os.environ:
        apikey = os.environ['APIKEY']

    if 'QRZ_COM_USERNAME' in os.environ:
        xml_username = os.environ['QRZ_COM_USERNAME']

    if 'QRZ_COM_PASSWORD' in os.environ:
        xml_password = os.environ['QRZ_COM_PASSWORD']

    # grab opts
    options, rest = getopt.gnu_getopt(sys.argv[1:],
                                      'l:a:hedi:xu:p:',
                                      ['logfile=', 'apikey=', 'help', 'idle_log', 'delete', 'inputfile=',
                                       'xmllookups', 'username=', 'password=', 'debug'])

    # check opts
    for opt, arg in options:
        if opt in ('-l', '--logfile'):
            logfile = arg
        elif opt in ('-a', '--apikey'):
            apikey = arg
        elif opt in ('-x', '--xmllookups'):
            xml_lookups = True
        elif opt in ('-u', '--username'):
            xml_username = arg
        elif opt in ('-p', '--password'):
            xml_password = arg
        elif opt in ('-d', '--delete'):
            delete_flag = True
        elif opt in ('-e', '--enable-idle-log'):
            write_idle_log = True
        elif opt in ('--debug'):
            debug_flag = True
        elif opt in ('-h', '--help'):
            print_help()
        elif opt in ('-i', '--inputfile'):
            inputfile = arg

    if debug_flag:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # now check whether everything needed is given - at least apikey & inputfile
    # must be present
    if apikey in ('', 'QRZ_COM_APIKEY'):
        print("")
        logger.error(
            "API key for qrz.com not specified. Please use either \"-a\" key or set environment variable \"APIKEY\".")
        print_help()
        exit(2)

    # if xml_lookups are requested, username and password must be provided
    if xml_lookups:
        if xml_username in ('', 'QRZ_COM_USERNAME'):
            print("")
            logger.error(
                "Username for qrz.com not specified. Please use either \"-u\" key or set environment variable \"QRZ_COM_USERNAME\".")
            print_help()
            exit(2)

        if xml_password in ('', 'QRZ_COM_PASSWORD'):
            print("")
            logger.error(
                "Password for qrz.com not specified. Please use either \"-p\" key or set environment variable \"QRZ_COM_PASSWORD\".")
            print_help()
            exit(2)

        get_xml_session_key()

    if not os.path.isfile(inputfile):
        logger.error("The inputfile " + inputfile + " does not exist")
        exit(3)

    # AND write a file
    if logfile != "null":
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

    with open(inputfile):
        lines = [line.rstrip('\n') for line in open(inputfile)]

    if len(lines) < 1 or (len(lines) == 1 and lines[0].endswith("ADIF Export<eoh>")):
        if write_idle_log:
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
            f.close()
        except Exception as e:
            logger.error("Could not write failed records into " + failed_records_file)
            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            if delete_flag:
                logger.warning("Will *not* empty " + inputfile + " due to error above")
            # and exit NOW, do NOT empty the source file
            exit(1)
        else:
            logger.info("Written " + str(len(failed_records)) + " failed records into file " + failed_records_file)

    # if succeeded writing down failed records (not exited with (1) above) - empty the source file,
    # if "-d" flag was provided
    if delete_flag:
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
    exit(exitcode)


def enrich_record(record):
    if xmlkey in ('', 'QRZ_COM_XMLKEY'):
        logger.debug("XMLKEY not set; missing qrz.com username/password. Will *not* try to enrich QSO grid data.")
    else:
        # enriching the record data with some values,
        # e.g. adding an at least 6 chars long locator

        data = {}

        # splitting fields
        for x in record.split('<'):
            if x == "" or x.startswith("eor>") or x.startswith("EOR>"):
                logger.debug("Ignoring field: " + x)
            else:
                # trying to split the line
                key = ""
                try:
                    key = x.split(':')[0].upper()
                except ValueError:
                    logger.debug("Failed to extract key from \"" + x + "\"")

                # ignoring keys with weird stuff in names
                # the only permitted chars are "[A-Z0-9_]", thus "\w"
                # So, if anything else is present - it can't be right, ignoring the key then
                if re.match('[^\w]+', key):
                    logger.debug("Ignoring key: " + key)
                else:
                    value = ((x.split('>')[1]).strip()).upper()
                    data[key] = str(value)

        if len(data['GRIDSQUARE']) <= 4:
            if data['GRIDSQUARE'] == "":
                data['GRIDSQUARE'] = "(not provided)"
            logger.debug("Will try to enrich grid locator data for " + data['CALL'])
            logger.debug("Grid locator from wsjtx_log.adi: " + data['GRIDSQUARE'])
            fetch_callsign_data(data['CALL'])

            new_locator = fetch_locator()
            if len(new_locator) >= 6:
                logger.info("Updating " + data['CALL'] + " locator from " + data['GRIDSQUARE'] + " to " + new_locator)
                data['GRIDSQUARE'] = new_locator
                logger.debug("Old record: " + record)
                # constructing back the ADIF record since data was modified
                record = ""
                for element in data:
                    record += "<" + element.lower() + ":" + str(len(data[element])) + ">" + str(data[element]) + " "
                record += " <eor>"
                logger.debug("New record: " + record)
            else:
                logger.info("No precise locator data found; leaving record untouched")

    return record


########################################

if __name__ == "__main__":
    main()
