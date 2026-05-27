#!/bin/bash
# Check if run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (using sudo)"
  exit 1
fi

echo "Applying pin connectivity overrides to Intel Audio codec (hwC1D0)..."
# Overriding 0x14 (Line Out) and 0x1b (Headphones) to be 'Fixed' instead of 'Jack'
echo "0x14 0x81014010" > /sys/class/sound/hwC1D0/user_pin_configs
echo "0x1b 0x82214020" >> /sys/class/sound/hwC1D0/user_pin_configs

echo "Triggering audio codec reconfiguration..."
echo 1 > /sys/class/sound/hwC1D0/reconfig

echo "Done! Pin overrides have been successfully applied."
