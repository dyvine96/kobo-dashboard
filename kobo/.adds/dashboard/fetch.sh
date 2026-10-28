#!/bin/sh
# Downloads the latest dashboard image and installs it as the Kobo screensaver.
# Finds whichever downloader this firmware has (curl or wget), retries for about
# a minute while WiFi connects, and only replaces the old image if the new
# download is a valid PNG. Writes details to last_run.log.

DIR=/mnt/onboard/.adds/dashboard
SS=/mnt/onboard/.kobo/screensaver
TMP=/tmp/dashboard.png
LOG="$DIR/last_run.log"
ERR="$DIR/dl_err.txt"
CA=/etc/ssl/certs/ca-certificates.crt

. "$DIR/config.sh"   # defines DASH_URL
mkdir -p "$SS"
rm -f "$ERR"

find_tool() {
    for p in /usr/bin/$1 /bin/$1 /usr/local/bin/$1 /sbin/$1 /usr/sbin/$1; do
        [ -x "$p" ] && { echo "$p"; return; }
    done
    command -v "$1" 2>/dev/null
}

CURL=$(find_tool curl)
WGET=$(find_tool wget)

download() {
    if [ -n "$CURL" ]; then
        if [ -f "$CA" ]; then
            "$CURL" -sS -L --max-time 20 --cacert "$CA" -o "$TMP" "$DASH_URL" 2>> "$ERR"
        else
            "$CURL" -sS -L --max-time 20 -o "$TMP" "$DASH_URL" 2>> "$ERR"
        fi
        return $?
    elif [ -n "$WGET" ]; then
        "$WGET" -q -T 20 -O "$TMP" "$DASH_URL" 2>> "$ERR"
        return $?
    else
        echo "no curl or wget found" >> "$ERR"
        return 127
    fi
}

i=0
rc=1
while [ "$i" -lt 12 ]; do
    download
    rc=$?
    if [ "$rc" -eq 0 ] && head -c 4 "$TMP" | grep -q PNG; then
        mv "$TMP" "$SS/dashboard.png"
        echo "$(date) ok" > "$LOG"
        rm -f "$ERR"
        exit 0
    fi
    [ "$rc" -eq 127 ] && break
    i=$((i + 1))
    sleep 5
done

{
    echo "$(date) failed, exit code $rc"
    echo "curl: ${CURL:-none}  wget: ${WGET:-none}"
    echo "ca file: $([ -f "$CA" ] && echo yes || echo no)"
    echo "PATH=$PATH"
    echo "--- error output"
    head -c 400 "$ERR" 2>/dev/null
    echo "--- tools in /usr/bin and /bin"
    ls /usr/bin /bin 2>/dev/null | grep -E '^(curl|wget|openssl|ssl_helper|nc|busybox)$' | tr '\n' ' '
} > "$LOG"
rm -f "$TMP"
exit 1
