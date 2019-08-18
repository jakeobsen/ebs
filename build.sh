#!/bin/sh
apt install devscripts debhelper
dpkg-buildpackage -us -uc
