#!/usr/bin/env bash
# Optimize system kernel parameters for ZRAM and gaming workloads.
set -e

echo "Setting kernel parameters for ZRAM..."
sudo sysctl vm.swappiness=180
sudo sysctl vm.page-cluster=0
sudo sysctl vm.watermark_boost_factor=0
sudo sysctl vm.watermark_scale_factor=125

echo "Making ZRAM optimizations persistent across reboots..."
CONF_FILE="/etc/sysctl.d/99-zram-tuning.conf"
echo "Writing configuration to $CONF_FILE..."
echo "# ZRAM and Gaming Memory Optimizations
vm.swappiness = 180
vm.page-cluster = 0
vm.watermark_boost_factor = 0
vm.watermark_scale_factor = 125" | sudo tee "$CONF_FILE" > /dev/null

echo "System memory parameters tuned successfully!"
