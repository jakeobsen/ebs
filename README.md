# EBS

EBS was designed to syncronise internal backups to external disks in an
automated way. In ebs.ini the sync source, destination and mountpath is
specified along with a set of whitelisted partion UUID's.

The purpose of this script is to make it easy to handle external backups in a
way that only require the external disk to be swapped.

## Example
Dirvish is used for backups, and stores vaults in /mnt/backup/dirvish/

The external disk is mounted in /mnt/externalbackup/

The desination folder is /mnt/externalbackup/dirvish/

A config file would look like:

```
[DEFAULT]
enabled = true

[BACKUP]
blkid = 1de6a920-29d8-4901-af96-c611e01fb8c5, 614926a2-7b19-404b-8249-861edf216b3e
rsync_source = /mnt/backup/dirvish/
rsync_destination = /mnt/externalbackup/dirvish/
mount_path = /mnt/externalbackup/
```

When EBS is run, it will loop through the specified partitions and look for
them in the systems partition id table. When a valid parition is found, it
will be mounted into the folder /mnt/externalbackup/

Then rsync is started to sync /mnt/backup/dirvish/ into /mnt/externalbackup/dirvish/

When rsync is done, the disk is synced and umounted. EBS then proceeds to
the next id in the list, if it's present the whole process starts again.
This way multiple external disks can be synced at once. E.g. to make two
copies of the internal backup disk.

## Installing

On a freshly baked debian box, install - as root - using:

```bash
wget -O- https://gitlab.com/jakeobsen/ebs/raw/master/build.sh | sh
```
