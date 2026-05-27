#!/usr/bin/env bash
# Script to disable and remove the HDD/SSD swap file, keeping only ZRAM.
set -e

SWAP_FILE="/swapfile"

echo "Checking if swap file $SWAP_FILE is active..."
if grep -q "$SWAP_FILE" /proc/swaps; then
    echo "Disabling swap file $SWAP_FILE..."
    sudo swapoff "$SWAP_FILE"
else
    echo "Swap file $SWAP_FILE is not active."
fi

if [ -f "$SWAP_FILE" ]; then
    echo "Removing swap file $SWAP_FILE..."
    sudo rm -f "$SWAP_FILE"
else
    echo "Swap file $SWAP_FILE does not exist."
fi

echo "Removing $SWAP_FILE entry from /etc/fstab..."
if grep -q "$SWAP_FILE" /etc/fstab; then
    sudo sed -i '\!/swapfile!d' /etc/fstab
    echo "Entry removed from /etc/fstab."
else
    echo "No entry found for $SWAP_FILE in /etc/fstab."
fi

echo "Verifying remaining active swaps..."
swapon --show
free -h

echo "HDD swap space successfully removed!"
