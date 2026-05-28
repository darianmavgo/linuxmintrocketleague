#!/usr/bin/env bash
# Helper script to cap ZRAM swap size to 4 GB.
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo."
    echo "Usage: sudo $0"
    exit 1
fi

echo "🛑 Stopping zram-config service..."
systemctl stop zram-config.service || true

echo "⚙️ Writing new configuration to /usr/bin/init-zram-swapping..."
cat << 'EOF' > /usr/bin/init-zram-swapping
#!/bin/sh

modprobe zram

# Calculate memory to use for zram (1/2 of ram)
totalmem=`LC_ALL=C free | grep -e "^Mem:" | sed -e 's/^Mem: *//' -e 's/  *.*//'`
mem=$((totalmem / 2 * 1024))

# Cap ZRAM size at 4 GB (1,073,741,824 bytes)
if [ $mem -gt 4294967296 ]; then
    mem=4294967296
fi

# initialize the devices
echo $mem > /sys/block/zram0/disksize
mkswap /dev/zram0
swapon -p 5 /dev/zram0
EOF

chmod +x /usr/bin/init-zram-swapping
echo "✅ Configuration updated."

echo "🚀 Restarting zram-config service..."
systemctl start zram-config.service

echo "📊 Verifying new swap allocations..."
swapon --show
free -h

echo "🎉 ZRAM successfully capped at 4 GB!"
