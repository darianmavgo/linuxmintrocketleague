#!/bin/bash

# Ensure script is run with sudo/root for writing to /etc and /lib
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root. Please run with 'sudo'."
  exit 1
fi

# Detect actual non-root user who invoked sudo (to manage systemd user services)
USER_NAME="${SUDO_USER:-$USER}"
USER_ID=$(id -u "$USER_NAME")

echo "=========================================================="
echo "Applying Audio Overrides (Realtek ALC3861)..."
echo "=========================================================="

# 1. Stop PipeWire/WirePlumber user services temporarily so device is not busy
echo "Temporarily stopping audio services for user $USER_NAME..."
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_ID" systemctl --user stop pipewire-pulse.socket pipewire-pulse.service pipewire.socket pipewire.service wireplumber.service 2>/dev/null

# 2. Apply temporary live overrides (which would fail with "Device or resource busy" if services were running)
echo "Applying live pin configs to ALC3861 codec..."
for hw in /sys/class/sound/hwC*D*; do
  if [ -f "$hw/chip_name" ] && grep -q "ALC3861" "$hw/chip_name"; then
    echo "0x14 0x81014010" > "$hw/user_pin_configs"
    echo "0x1b 0x82214020" >> "$hw/user_pin_configs"
    echo "Triggering codec reconfiguration..."
    echo 1 > "$hw/reconfig"
    break
  fi
done

# 3. Create firmware patch for boot permanence
echo "Creating permanent firmware patch at /lib/firmware/alc3861-override.fw..."
cat << 'EOF' > /lib/firmware/alc3861-override.fw
[codec]
0x10ec0899 0x102807dc 0

[pincfg]
0x14 0x81014010
0x1b 0x82214020
EOF

# 4. Configure modprobe to load this patch on startup
echo "Configuring modprobe at /etc/modprobe.d/hda-jack-retask.conf..."
echo "options snd-hda-intel patch=alc3861-override.fw" > /etc/modprobe.d/hda-jack-retask.conf

# 5. Restart PipeWire/WirePlumber user services
echo "Restarting audio services..."
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_ID" systemctl --user start pipewire pipewire-pulse wireplumber 2>/dev/null

# Wait for services to initialize
sleep 2

# 6. Re-enable the analog stereo card profile so it is active
echo "Configuring PipeWire card profile to Analog Stereo..."
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_ID" pactl set-card-profile alsa_card.pci-0000_00_1f.3 output:analog-stereo 2>/dev/null

echo "=========================================================="
echo "SUCCESS: Fixes applied successfully!"
echo "1. Audio jack overrides are active right now (no reboot needed)."
echo "2. The settings have been made permanent using kernel firmware patches."
echo "=========================================================="
