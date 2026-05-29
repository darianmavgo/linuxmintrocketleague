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
# Optimize Rocket League Garbage Collection to run more frequently between games
for INI_FILE in \
  "$HOME/Documents/My Games/Rocket League/TAGame/Config/TASystemSettings.ini" \
  "$HOME/.steam/steam/steamapps/compatdata/252950/pfx/drive_c/users/steamuser/Documents/My Games/Rocket League/TAGame/Config/TASystemSettings.ini"; do
    if [ -f "$INI_FILE" ]; then
        echo "Configuring Rocket League garbage collection in $INI_FILE..."
        # Ensure [Core.System] exists
        if ! grep -q "\\[Core.System\\]" "$INI_FILE"; then
            echo -e "\\n[Core.System]" >> "$INI_FILE"
        fi
        # Ensure TimeBetweenPurgingPendingKillObjects is set to 15
        if grep -q "TimeBetweenPurgingPendingKillObjects=" "$INI_FILE"; then
            sed -i 's/TimeBetweenPurgingPendingKillObjects=.*/TimeBetweenPurgingPendingKillObjects=15/' "$INI_FILE"
        else
            sed -i '/\\[Core.System\\]/a TimeBetweenPurgingPendingKillObjects=15' "$INI_FILE"
        fi
    fi
done

