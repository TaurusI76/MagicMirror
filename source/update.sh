#!/bin/bash
# Check for updates
cd ota_updates
git fetch
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})
if [ $LOCAL != $REMOTE ]; then
	echo “Repository is outdated. Updating…”
	# git pull
	# Download updates
	git checkout master
	# Replace the current application with the updated version
	rsync -a ./..
	echo “Repository updated.”
	exit 1
else
	echo “Repository is up to date.”
	exit 0
fi