#!/bin/bash
# Copy updates to program folder

# Check if any arguments were supplied
if [ $# -eq 0 ] ; then
    echo "copy.sh: No arguments supplied"
	exit 1
fi

if [ -z "$1" ] ; then
    echo "copy.sh: No exe path supplied"
	exit 1
fi

if [ -z "$2" ] ; then
    echo "copy.sh: No source path supplied"
	exit 1
fi

EXEPATH=$1
SOURCEPATH=$2

echo "copy.sh: Copying python scripts from $SOURCEPATH to $EXEPATH"
sudo cp $SOURCEPATH/source/*.py $EXEPATH

if [ $? -ne 0 ] ; then
    echo "copy.sh: Copying python scripts failed."
	exit 1
fi

echo "copy.sh: Copying bash scripts from $SOURCEPATH to $EXEPATH"
sudo cp $SOURCEPATH/source/*.sh $EXEPATH

if [ $? -ne 0 ] ; then
    echo "copy.sh: Copying bash scripts failed."
	exit 1
fi

exit 0