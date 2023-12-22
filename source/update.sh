#!/bin/bash
# Check for updates
cd ota_updates
sudo git fetch
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})
if [ $LOCAL != $REMOTE ]; then
	echo “Repository is outdated. Updating…”
	git pull --rebase
	echo “Repository updated.”
	exit 1
else
	echo “Repository is up to date.”
	exit 0
fi