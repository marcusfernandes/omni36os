#!/bin/sh
# Android em ancoragem USB com classe EF/04/01: usa o rndis_host pela entrada de referencia 1630:0042.
# $1 = PRODUCT do udev (vid/pid/bcd)
vid=$(echo "$1" | cut -d/ -f1); pid=$(echo "$1" | cut -d/ -f2)
/sbin/modprobe rndis_host || exit 1
echo "$vid $pid ef 1630 0042" > /sys/bus/usb/drivers/rndis_host/new_id 2>/dev/null
exit 0
