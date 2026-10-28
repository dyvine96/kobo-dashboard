#!/bin/sh
# Downloads the newest dashboard image, then draws it on screen.
DIR=/mnt/onboard/.adds/dashboard
"$DIR/fetch.sh" && "$DIR/show.sh"
