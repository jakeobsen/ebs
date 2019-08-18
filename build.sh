#!/bin/sh
apt install devscripts debhelper git
git clone https://gitlab.com/jakeobsen/ebs
cd ebs
dpkg-buildpackage -us -uc
dpkg -i ../ebs*.deb
