#!/bin/sh
# Pixy launcher for the UNO Q.
#
# The Python bridge API and Pillow live inside the App Lab brick container, not
# on the host, so everything runs in there with the router socket mounted.
#
#   ./pixy.sh start [xiao-ip]   run the console (detached, survives logout)
#   ./pixy.sh stop              stop it
#   ./pixy.sh logs              follow output
#   ./pixy.sh deck              run the input tester instead
#   ./pixy.sh status            what is running

IMAGE=ghcr.io/arduino/app-bricks/python-apps-base:0.12.0
APP=/home/arduino/ledmatrix
NAME=pixy
XIAO=${2:-192.168.1.64}

run() {   # run() <container-name> <python -m target>
    docker rm -f "$1" >/dev/null 2>&1
    docker run -d --name "$1" --restart unless-stopped --network host \
        -v /var/run/arduino-router.sock:/var/run/arduino-router.sock \
        -v "$APP":/app -w /app --entrypoint python3 \
        "$IMAGE" -m "$2" "$XIAO" >/dev/null
    echo "$1 started -> panel at $XIAO"
    echo "follow with: $0 logs"
}

case "$1" in
    start)  run "$NAME" pixy.app ;;
    deck)   run "$NAME" pixy.decktest ;;
    stop)   docker rm -f "$NAME" >/dev/null 2>&1 && echo "stopped" ;;
    logs)   docker logs -f "$NAME" ;;
    status)
        docker ps --filter "name=$NAME" --format "{{.Names}} {{.Status}} {{.Command}}"
        echo "--- link to panel ---"
        ss -tn 2>/dev/null | grep 3333 || echo "not connected"
        ;;
    *) sed -n '2,12p' "$0" ;;
esac
