#!/bin/bash
# Runs MagicMirror executables and updates source files on failure
# This script should be run from the EXEPATH

# Check if any arguments were supplied
if [[ $# -eq 0 ]] ; then
    echo "No arguments supplied"
	exit 1
fi

if [[ -z "$1" ]] ; then
    echo "No exe path supplied"
	exit 1
fi

if [[ -z "$2" ]] ; then
    echo "No source path supplied"
	exit 1
fi

# Get paths from arguments
EXEPATH=$1
SOURCEPATH=$2
LOGFILE=$3

if [[ -z "$3" ]] ; then
    echo "No log file path supplied. Running without log file."
	sudo python3 $EXEPATH/SnapPrintSend.py
else
	sudo python3 $EXEPATH/SnapPrintSend.py | tee $LOGFILE
fi

if [[ $? = 0 ]]; then
    echo "MagicMirror ran successfully."
	exit 0
else
    echo "Executing MagicMirror failed: $?"
	
	# Go into the source directory and try updating the source files from git
	cd ../$SOURCEPATH
	sudo git fetch
	sudo git pull --rebase
	
	# Copy updates to program folder
	sudo cp ./source/*.py ../$EXEPATH
	sudo cp ./source/*.sh ../$EXEPATH
	
	exit 1
fi
