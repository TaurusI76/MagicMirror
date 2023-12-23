#!/bin/bash
# Check for updates

# Check if any arguments were supplied
if [ $# -eq 0 ] ; then
    echo "update.sh: No arguments supplied"
	exit 1
fi

if [ -z "$1" ] ; then
    echo "update.sh: No source path supplied"
	exit 1
fi

SOURCEPATH=$1

# Change to source directory
cd $SOURCEPATH

# Check git for changes
sudo git fetch

if [ $? -ne 0 ] ; then
    echo "update.sh: git fetch failed."
	exit 1
fi

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})
if [ $LOCAL != $REMOTE ] ; then
	echo "update.sh: Repository is outdated. Updating…"
	sudo git pull --rebase
	
	if [ $? -ne 0 ]; then
		echo "update.sh: git pull failed."
		exit 1
	fi

	echo "update.sh: Repository updated."
	exit 1
else
	echo "update.sh: Repository is up to date."
	exit 0
fi