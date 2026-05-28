#!/usr/bin/env bash
# Script to apply the GRUB patch to disable PCIe AER log flooding.
# Run this script with: sudo ./apply_grub_patch.sh

if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run with sudo/root privileges."
    echo "Usage: sudo $0"
    exit 1
fi

GRUB_FILE="/etc/default/grub"

if [ -f "$GRUB_FILE" ]; then
    echo "📸 Backing up $GRUB_FILE to ${GRUB_FILE}.bak..."
    cp "$GRUB_FILE" "${GRUB_FILE}.bak"
    
    echo "⚙️ Adding pci=noaer to GRUB_CMDLINE_LINUX_DEFAULT..."
    if grep -q "GRUB_CMDLINE_LINUX_DEFAULT=" "$GRUB_FILE"; then
        if grep -q "pci=noaer" "$GRUB_FILE"; then
            echo "✓ pci=noaer is already present in GRUB configuration."
        else
            sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 pci=noaer"/' "$GRUB_FILE"
            echo "✓ GRUB configuration updated."
        fi
    else
        echo "❌ Error: Could not find GRUB_CMDLINE_LINUX_DEFAULT in $GRUB_FILE"
        exit 1
    fi
    
    echo "🚀 Running update-grub to apply changes..."
    update-grub
    echo "🎉 Success! Please reboot your system to apply the changes."
else
    echo "❌ Error: $GRUB_FILE not found."
    exit 1
fi
