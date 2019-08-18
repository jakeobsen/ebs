#!/usr/bin/env python3
# Copyright 2019 Morten Jakobsen. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

# -*- coding: utf-8 -*-

"""
This program is used together with the dirvish backup solution.
It is intended to sync the internal backup partition with an
external backup disk.

You can sync x number of backups to the disk, or the whole archive
depending on the configuration.

The system keeps an internal list of whitelisted partition ID's that
it uses to determine which partition it should mount in the external
backup location, and then sync.
"""

import configparser
import subprocess
import os
import logging
import argparse
import time


""" Main class for EBS program """


class Main:
    def __init__(self, configurationFile):
        """ Initialize class """
        self.lockFilePath = '/var/lock/ebs'
        self.configFilename = configurationFile

    def setLockFile(self):
        with open(self.lockFilePath, 'w') as f:
            f.write('ebs')

    def deleteLockFile(self):
        os.remove(self.lockFilePath)

    def checkLockFile(self):
        if os.path.isfile(self.lockFilePath):
            logging.warning("Lockfile found, exiting.")
            return False
        else:
            return True

    def run(self):
        """ Begin execution """
        self.config = configparser.ConfigParser()
        if self.checkLockFile():
            self.setLockFile()
            self.loadConfig()
            self.main()
            self.deleteLockFile()

    def saveConfig(self):
        """ Save configuration file """
        logging.debug("Saving configuration file to {}".format(self.configFilename))
        with open(self.configFilename, 'w') as configfile:
            self.config.write(configfile)

    def loadConfig(self):
        """ Load configuration file, if empty load default config """
        logging.debug("Trying to load configuration file from {}".format(self.configFilename))
        if len(self.config.read(self.configFilename)) == 0:
            logging.warning("No configuration file in path specified. Creating default configuration file.")
            self.setDefaultConfig()
            self.saveConfig()

    def setDefaultConfig(self):
        """ Set default configuration """
        self.config['DEFAULT'] = {}
        self.config['DEFAULT']['enabled'] = "false"
        self.config['BACKUP'] = {}
        self.config['BACKUP']['blkid'] = ''
        self.config['BACKUP']['rsync_source'] = '/mnt/backup/dirvish/'
        self.config['BACKUP']['rsync_destination'] = '/mnt/externalbackup/dirvish/'
        self.config['BACKUP']['mount_path'] = '/mnt/externalbackup/'

    def main(self):
        """ Execute program """
        # Only run if enabled in config
        if self.config['DEFAULT']['enabled'] == "true":
            logging.debug("EBS is enabled")

            # Determine what to backup
            #self.getLastBackup()

            # Get list of valid backup ID's
            logging.debug("Trying to get list of valid UUID's")
            uuidList = self.config['BACKUP']['blkid'].split(",")

            # Run over said list
            logging.debug("Checking list of UUID")
            for uuidListItem in uuidList:

                # Assign list item to uuid variable
                uuid = uuidListItem.strip()
                logging.debug("Trying {}".format(uuid))

                # Check each uuid against blkid and get device name
                blkidResult = subprocess.run(["/sbin/blkid", "-U", uuid], stdout=subprocess.PIPE)

                # If blockid returns an item, process it
                if(blkidResult.returncode == 0):
                    # Print disk name
                    device = blkidResult.stdout.decode("utf-8").strip()
                    logging.info('Found valid disk: {}'.format(device))

                    # Mount backup partition
                    logging.info("Mounting disk in {}".format(self.config['BACKUP']['mount_path']))
                    subprocess.run(["/bin/mount", device, self.config['BACKUP']['mount_path']], stdout=subprocess.PIPE)

                    # Run backup process
                    self.backupData()

                    # Unmount backup partition
                    logging.info("Syncing disks prior to umount")
                    subprocess.run(["/bin/sync"], stdout=subprocess.PIPE)
    
                    # Unmount backup partition
                    logging.info("Unmounting disk from {}".format(self.config['BACKUP']['mount_path']))
                    subprocess.run(["/bin/umount", self.config['BACKUP']['mount_path']], stdout=subprocess.PIPE)
                else:
                    logging.debug("Invalid disk")
        else:
            # EBS is not enabled
            logging.warning("EBS is not enabled, please refer to the documentation, and update the configuration file before you continue.")

    def backupData(self):
        logging.info("Initiating backup process")
        rsync = subprocess.run(['/usr/bin/rsync','-qrlHptgoD','--delete-before',self.config['BACKUP']['rsync_source'],self.config['BACKUP']['rsync_destination']], stdout=subprocess.PIPE)
        logging.debug(rsync)
        if rsync.returncode == 0:
            logging.info("Backup process completed.")
        else:
            logging.info("Backup process completed with returncode: {}.".format(rsync.returncode))

    def getLastBackup(self):    
        """ Try and figure out the last backup made """
        dirContents = os.listdir(self.config['BACKUP']['rsync_source'])
        logging.debug("Checking folders in: {}".format(self.config['BACKUP']['rsync_source']))
        lastChangeTime = 0
        for entry in dirContents:
            logging.debug("Checking dir: {}".format(entry))
            if entry != "dirvish":
                fullPath = "{}/{}".format(self.config['BACKUP']['rsync_source'], entry)
                changeTime = int(os.stat(fullPath).st_ctime)
                isDir = os.path.isdir(fullPath)
                if isDir == True:
                    logging.debug("Is a directory")
                    if changeTime > lastChangeTime:
                        logging.debug("Found valid path: {} ({})".format(self.config['BACKUP']['rsync_source'], changeTime))
                        self.lastBackup = fullPath
                        lastChangeTime = changeTime
                else:
                    logging.debug("Is not a directory")
            else:
                logging.debug("Invalid folder name")
        logging.info("Found valid backup source: {}".format(self.lastBackup))


"""
Run EBS if called from command line
"""
if __name__ == "__main__":
    # Description
    parser = argparse.ArgumentParser(description="External Backup Script: copy dirvish backups to external disks")
    # Config
    parser.add_argument('-c', '--config', type=str, help="Configuration File", default="/etc/ebs.ini")
    # Loglevel
    parser.add_argument('-l', '--loglevel', type=int, help="Set execution log level", default=3, choices=range(0, 6))
    # Parse input
    args = parser.parse_args()

    # Configure logging
    if args.loglevel == 0:
        logging.basicConfig(level=logging.NOTSET)
    elif args.loglevel == 1:
        logging.basicConfig(level=logging.DEBUG)
    elif args.loglevel == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.loglevel == 3:
        logging.basicConfig(level=logging.WARNING)
    elif args.loglevel == 4:
        logging.basicConfig(level=logging.ERROR)
    elif args.loglevel == 5:
        logging.basicConfig(level=logging.CRITICAL)

    # Single instance only
    ebs = Main(args.config)
    ebs.run()
