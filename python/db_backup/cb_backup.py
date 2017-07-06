#!/usr/bin/python
##-------------------------------------------------------------------
## File : cb_backup.py
## Author : DennyZhang.com <denny@dennyzhang.com>
## Description : Couchbase Daily Backup
## --
## Created : <2016-08-01>
## Updated: Time-stamp: <2017-07-05 20:29:17>
##-------------------------------------------------------------------
# TODO: move to common library
import argparse
import os, sys
from datetime import date
import calendar
import subprocess

log_folder = "%s/log" % (os.path.expanduser('~')
if os.path.exists(log_folder) is False
    os.makedirs(log_folder)
log_file = "%s/%s.log" % (log_folder, os.path.basename(__file__).rstrip('\.py'))
# setup logging
from logging.handlers import RotatingFileHandler
import logging
format = "%(asctime)s %(filename)s:%(lineno)d - %(levelname)s: %(message)s"
formatter = logging.Formatter(format)
log = logging.getLogger('cbbackup')

Rthandler = RotatingFileHandler(log_file, maxBytes=5*1024*1024,backupCount=5)
Rthandler.setLevel(logging.INFO)
Rthandler.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)
# log critical info to both console output and log files
log.setLevel(logging.INFO)
log.addHandler(consoleHandler)
log.addHandler(Rthandler)

################################################################################
# Critical Configuration
# Sample:
#   python cb_backup.py --username $MYUSERNAME --password $MYPASSWD --cbserver http://127.0.0.1.8091
parser = argparse.ArgumentParser()
parser.add_argument('--username', default='Administrator', required=True,
                    help="username of couchbase", type=str)
parser.add_argument('--password', default='password', required=True,
                    help="password of couchbase", type=str)
parser.add_argument('--bucket_list', default = 'bucket1,bucket2',
                    help="Bucket name list to be backup", type=str)
parser.add_argument('--cbserver', default='http://127.0.0.1:8091',
                    help="Couchbase management url", type=str)
parser.add_argument('--cbbackup_bin', default='/opt/couchbase/bin/cbbackup',
                    help="Path of cbbackup command line", type=str)
parser.add_argument('--backup_dir', default='/data/backup/couchbase',
                    help="Destination directory for backup", type=str)
parser.add_argument('--backup_method', default='',
                    help="Backup method: full, diff, accu", type=str)
args = parser.parse_args()

bucket_list = args.bucket_list
cbserver = args.cbserver
cbbackup_bin = args.cbbackup_bin
username = args.username
password = args.password
backup_dir = args.backup_dir
backup_method = args.backup_method

weekday_method = {
    "Sunday": "diff",
    "Monday": "full",
    "Tuesday": "diff",
    "Wednesday": "accu", # accumulate
    "Thursday": "diff",
    "Friday": "diff",
    "Saturday": "diff"
}

################################################################################
def cb_backup_command(bucket, method):
    # Back up all nodes and all buckets:
    # https://developer.couchbase.com/documentation/server/current/cli/backup-cbbackup.html
    command = "%s %s %s/%s -u %s -p %s -b %s -m %s -t 4" % \
              (cbbackup_bin, cbserver, backup_dir, bucket, username, password, bucket, method)
    # Sample: /opt/couchbase/bin/cbbackup http://127.0.0.1:8091 \
    #         /data/cb_backup/bucket1 -u $MYUSERNAME \
    #         -p $MYPASSWD -b bucket1 -m diff -t 4
    return "%s >> %s" % (command, log_file)

def cb_backup_bucket(bucket, backup_method = ""):
    if backup_method == "":
        today = date.today()
        day = calendar.day_name[today.weekday()]
        # Run DB backup with complete/diff/accu in different days
        backup_method = weekday_method.get(day)
    backup_command = cb_backup_command(bucket, backup_method)
    log.info("Backup Couchbase bucket: %s, method: %s" % (bucket, backup_method))
    log.info("Run command: %s" % (backup_command))
    # TODO: get command output
    returncode = subprocess.call(backup_command, shell=True)
    if returncode != 0:
        log.error("Backup fails for %s" % (bucket))
        sys.exit(returncode)

################################################################################
if __name__=='__main__':
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    for bucket in bucket_list.split(','):
        cb_backup_bucket(bucket, backup_method)
    # TODO: show file size of backup set
    log.info("Backup succeed for Couchbase.")
## File : cb_backup.py ends
