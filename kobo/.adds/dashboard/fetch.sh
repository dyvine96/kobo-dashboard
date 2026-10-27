#!/bin/sh
# Downloads the latest dashboard image and installs it as the Kobo screensaver.
# Safe to run repeatedly: the old image is only replaced if the new download is a valid PNG.

DIR=/mnt/onboard/.adds/dashboard
SS=/mnt/onboard/.kobo/screensaver
TMP=/tmp/dashboard.png
LOG="$DIR/last_run.log"

. "$DIR/config.sh"   # defines DASH_URL

mkdir -p "$SS"

if curl -fsSL --max-time 40 --cacert /etc/ssl/certs/ca-certificates.crt -o "$TMP" "$DASH_URL"; then
    if head -c 4 "$TMP" | grep -q PNG; then
        mv "$TMP" "$SS/dashboard.png"
        echo "$(date) ok" > "$LOG"
        exit 0
    fi
fi

echo "$(date) failed" > "$LOG"
rm -f "$TMP"
exit 1
