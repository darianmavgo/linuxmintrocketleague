#!/bin/bash
# Check if run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (using sudo)"
  exit 1
fi

echo "Creating local override helper script at /usr/local/bin/hda-jack-override.sh..."
cat << 'EOF' > /usr/local/bin/hda-jack-override.sh
#!/bin/bash
# Find the ALC3861 sound card and apply pin overrides
for hw in /sys/class/sound/hwC*D*; do
  if [ -f "$hw/chip_name" ] && grep -q "ALC3861" "$hw/chip_name"; then
    echo "Applying ALC3861 pin overrides (fixing jack availability)..."
    echo "0x14 0x81014010" > "$hw/user_pin_configs"
    echo "0x1b 0x82214020" >> "$hw/user_pin_configs"
    echo 1 > "$hw/reconfig"
    break
  fi
done
EOF

chmod +x /usr/local/bin/hda-jack-override.sh

echo "Creating systemd system service unit at /etc/systemd/system/hda-jack-override.service..."
cat << 'EOF' > /etc/systemd/system/hda-jack-override.service
[Unit]
Description=Apply HDA Jack Overrides for ALC3861
DefaultDependencies=no
After=sysinit.target
Before=sound.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/hda-jack-override.sh
RemainAfterExit=yes

[Install]
WantedBy=sound.target
EOF

echo "Reloading systemd daemon and enabling the service..."
systemctl daemon-reload
systemctl enable hda-jack-override.service

echo "=========================================================="
echo "SUCCESS: Boot override service installed and enabled!"
echo "Your audio fixes are now permanent and will survive reboots."
echo "=========================================================="
