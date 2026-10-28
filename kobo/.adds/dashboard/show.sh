#!/bin/sh
# Draws the last downloaded dashboard image on the screen using the FBInk
# that ships with KOReader. Works on top of the normal Kobo interface.

DIR=/mnt/onboard/.adds/dashboard
IMG=/mnt/onboard/.kobo/screensaver/dashboard.png
FBINK=/mnt/onboard/.adds/koreader/fbink

[ -f "$IMG" ] || { echo "$(date) no image to show" > "$DIR/show_err.txt"; exit 1; }
[ -x "$FBINK" ] || { echo "$(date) fbink not found at $FBINK" > "$DIR/show_err.txt"; exit 1; }

"$FBINK" -c -f -g "file=$IMG,halign=CENTER,valign=CENTER" 2> "$DIR/show_err.txt"
exit $?
