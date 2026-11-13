#!/bin/sh
# Static Linux — (re)start the bar
pkill -x polybar
while pgrep -x polybar >/dev/null; do sleep 0.2; done
polybar main >/dev/null 2>&1 &
