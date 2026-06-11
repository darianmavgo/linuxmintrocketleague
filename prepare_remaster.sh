#!/usr/bin/env bash
# Script to prepare the gaming station for remastering/cloning.
# This cleans system caches, logs, and heavy temporary files to reduce image size.

set -e

echo "=== System Remaster Preparation Script ==="
echo "This script will clean up temporary files, logs, and caches to minimize your USB image size."

# 1. Check for huge RAM dumps
echo ""
echo "Checking for heavy memory dumps..."
DUMP_FILES=$(find ~/Documents -name "*_ram.dump.*" -o -name "*.dmp" || true)

if [ -n "$DUMP_FILES" ]; then
    echo "Found the following large RAM dump files:"
    echo "$DUMP_FILES"
    echo ""
    read -p "Would you like to delete these RAM dump files to save space? (y/N): " delete_dumps
    if [[ "$delete_dumps" =~ ^[Yy]$ ]]; then
        echo "Deleting RAM dumps..."
        rm -f ~/Documents/*_ram.dump.* ~/Documents/*.dmp || true
        echo "RAM dumps deleted."
    else
        echo "Skipping RAM dump deletion. Note that these files will significantly increase your image size."
    fi
else
    echo "No RAM dump files found."
fi

# 2. Clean Flatpak caches and unused runtimes
echo ""
echo "Cleaning up Flatpak applications..."
if command -v flatpak &> /dev/null; then
    echo "Removing unused Flatpak runtimes..."
    flatpak uninstall --unused -y || true
    echo "Clearing Heroic Games Launcher caches..."
    rm -rf ~/.var/app/com.heroicgameslauncher.hgl/cache/* || true
else
    echo "Flatpak not installed, skipping."
fi

# 3. Clean Package Manager caches
echo ""
echo "Cleaning APT package cache..."
sudo apt-get autoremove -y
sudo apt-get autoclean -y
sudo apt-get clean

# 4. Clean system journals and logs
echo ""
echo "Limiting journal logs to the last 24 hours..."
sudo journalctl --vacuum-time=1d || true

# 5. Clean user caches and trash
echo ""
echo "Clearing system caches and Trash..."
rm -rf ~/.cache/thumbnails/* || true
rm -rf ~/.local/share/Trash/* || true
rm -rf /tmp/* || true

echo ""
echo "=== Preparation Complete ==="
echo "Your system is clean and ready to be packaged or cloned."
df -h /
