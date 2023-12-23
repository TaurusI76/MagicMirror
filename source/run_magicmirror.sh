#!/bin/bash
# Runs MagicMirror executables and updates source files on failure
# This script should be run from the EXEPATH

# Check if any arguments were supplied
if [ $# -eq 0 ] ; then
    echo "run_magicmirror.sh: No arguments supplied"
	exit 1
fi

if [ -z "$1" ] ; then
    echo "run_magicmirror.sh: No exe path supplied"
	exit 1
fi

if [ -z "$2" ] ; then
    echo "run_magicmirror.sh: No source path supplied"
	exit 1
fi

# Get paths from arguments
EXEPATH=$1
SOURCEPATH=$2
LOGFILE=$3

if [ -z "$3" ] ; then
    echo "run_magicmirror.sh: No log file path supplied. Running without log file."
	sudo python3 $EXEPATH/SnapPrintSend.py $EXEPATH $SOURCEPATH
else
    echo "run_magicmirror.sh: Running $EXEPATH/SnapPrintSend.py with $EXEPATH and $SOURCEPATH and logging to $LOGFILE"
	
	# Run sudo python3 /home/magicmirror/MagicMirrorExecutables/SnapPrintSend.py /home/magicmirror/MagicMirrorExecutables /home/magicmirror/MagicMirror | tee /home/magicmirror/magicmirror.log
	sudo python3 $EXEPATH/SnapPrintSend.py $EXEPATH $SOURCEPATH | tee $LOGFILE
fi

if [ $? = 0 ]; then
    echo "run_magicmirror.sh: MagicMirror ran successfully."
	exit 0
else
    echo "run_magicmirror.sh: Executing MagicMirror failed: $?"
	
	echo "run_magicmirror.sh: Trying to update from git..."
	
	# Go into the source directory and try updating the source files from git
	cd $SOURCEPATH
	sudo git fetch
	
	if [ $? -ne 0 ]; then
		echo "run_magicmirror.sh: git fetch failed."
		exit 1
	fi

	sudo git pull --rebase
	
	if [ $? -ne 0 ]; then
		echo "run_magicmirror.sh: git pull failed."
		exit 1
	fi

	echo "run_magicmirror.sh: Copying updated files to exe directory..."
	
	# Copy updates to program folder
	sudo cp $SOURCEPATH/source/*.py $EXEPATH
	
	if [ $? -ne 0 ] ; then
		echo "run_magicmirror.sh: Copying python scripts failed."
		exit 1
	fi

	sudo cp $SOURCEPATH/source/*.sh $EXEPATH
	
	if [ $? -ne 0 ] ; then
		echo "run_magicmirror.sh: Copying bash scripts failed."
		exit 1
	fi

	echo "run_magicmirror.sh: Emergency update finished. Please reboot."
	exit 1
fi
