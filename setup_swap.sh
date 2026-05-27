#!/bin/bash
set -e

SWAP_FILE="/swapfile"
SWAP_SIZE="8G"

echo "Checking if swap file already exists..."
if [ -f "$SWAP_FILE" ] || grep -q "$SWAP_FILE" /proc/swaps; then
    echo "Swap space is already configured at $SWAP_FILE or active in /proc/swaps."
    swapon --show
    free -h
    exit 0
fi

echo "Creating swap file of size $SWAP_SIZE at $SWAP_FILE..."
# Try fallocate first (fast), fall back to dd if filesystem doesn't support preallocation
sudo fallocate -l $SWAP_SIZE $SWAP_FILE || sudo dd if=/dev/zero of=$SWAP_FILE bs=1M count=8192

echo "Setting correct permissions (chmod 600)..."
sudo chmod 600 $SWAP_FILE

echo "Setting up swap space (mkswap)..."
sudo mkswap $SWAP_FILE

echo "Enabling swap space (swapon)..."
sudo swapon $SWAP_FILE

echo "Adding swap entry to /etc/fstab to make it persistent across reboots..."
if ! grep -q "$SWAP_FILE" /etc/fstab; then
    echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab
    echo "Added entry to /etc/fstab"
else
    echo "Entry already exists in /etc/fstab"
fi

echo "Verifying active swap..."
swapon --show
free -h

echo "Swap setup successfully completed!"
