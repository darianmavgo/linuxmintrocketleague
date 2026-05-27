#!/usr/bin/env bash
# RocketMode Autostart Applications Optimizer
# Disables background tray apps and services that run on startup

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 ROCKETMODE AUTOSTART OPTIMIZER${NC}"
echo -e "This script disables non-gaming background applications from launching at login."
echo -e "No system files are modified; changes are made in your local user directory.\n"

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

disable_app() {
    local app_file="$1"
    local dest_path="$AUTOSTART_DIR/$app_file"
    
    # If it doesn't exist in local config, copy it from system config
    if [ ! -f "$dest_path" ]; then
        if [ -f "/etc/xdg/autostart/$app_file" ]; then
            cp "/etc/xdg/autostart/$app_file" "$dest_path"
        else
            echo -e "${YELLOW}Notice: $app_file is not installed or active on your system.${NC}"
            return 0
        fi
    fi
    
    # Remove existing Hidden= lines to prevent duplicates
    sed -i '/^Hidden=/d' "$dest_path"
    
    # Append Hidden=true
    echo "Hidden=true" >> "$dest_path"
    echo -e "${GREEN}Successfully disabled: ${NC} $app_file"
}

# 1. Update Manager (uses ~95MB of RAM at boot)
disable_app "mintupdate.desktop"

# 2. System Reports daemon (checks for crashes/reminders)
disable_app "mintreport.desktop"

# 3. Print Applet (status checker for printer queues)
disable_app "print-applet.desktop"

# 4. Warpinator (local file sharing app, runs continuously)
disable_app "warpinator-autostart.desktop"

# 5. Onboard On-Screen Keyboard (loaded by accessibility, if active)
disable_app "onboard-autostart.desktop"

# 6. Sticky Notes applet
disable_app "sticky.desktop"

# 7. Bluetooth Query
read -p "Do you want to disable the Bluetooth Manager tray icon (Blueman)? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    disable_app "blueman.desktop"
fi

# 8. Heroic Games Launcher Settings (Toggle off NVIDIA Prime)
echo -e "\n${YELLOW}[8/8] Optimizing Heroic Games Launcher settings...${NC}"
SUGAR_JSON="$HOME/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig/Sugar.json"
if [ -f "$SUGAR_JSON" ]; then
    echo "Disabling NVIDIA Prime for Rocket League in Heroic configuration..."
    python3 -c "
import json
with open('$SUGAR_JSON', 'r') as f:
    data = json.load(f)
if 'Sugar' in data:
    data['Sugar']['nvidiaPrime'] = False
with open('$SUGAR_JSON', 'w') as f:
    json.dump(data, f, indent=2)
"
    echo -e "${GREEN}Successfully disabled nvidiaPrime in Sugar.json${NC}"
else
    echo "Notice: Rocket League config ($SUGAR_JSON) not found. Skipping."
fi

echo -e "\n${GREEN}✅ STARTUP & GAME OPTIMIZATIONS CONFIGURED!${NC}"
echo "These apps will no longer start automatically when you log in."
echo "You can still launch them manually from the application menu whenever you need them."

echo -e "\n${YELLOW}------------------------------------------------------------${NC}"
echo -e "${YELLOW}REVERSION / ROLLBACK COMMANDS:${NC}"
echo "To restore any of these apps to autostart, run:"
echo "  rm ~/.config/autostart/<app_name>.desktop"
echo "This will restore the system default autostart behavior."
echo -e "${YELLOW}------------------------------------------------------------${NC}"
