#!/bin/sh
# magicmirror_launcher.sh
# navigate to home directory, then to MagicMirror directory, then execute python script, then back home

cd /
cd home/magicmirror/MagicMirror
sudo python3 source/SnapPrintSend.py > magicmirror.log 2>&1
cd /