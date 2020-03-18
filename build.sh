#!/bin/sh
mkdir /tmp/ebs
cd /tmp/ebs
apt install devscripts debhelper git
git clone https://github.com/jakeobsen/ebs
cd ebs
dpkg-buildpackage -us -uc
dpkg -i ../ebs*.deb
cd $HOME
rm -rf /tmp/ebs
