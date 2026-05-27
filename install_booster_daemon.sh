#!/usr/bin/env bash
# Registers the RocketMode Daemon to start automatically on login

set -e

GREEN='\033[0;32m'
NC='\033[0m'

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat <<EOF > "$AUTOSTART_DIR/rocketmode_booster.desktop"
[Desktop Entry]
Type=Application
Exec=$HOME/Documents/RocketMode/rocket_booster_daemon.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=RocketMode Game Booster Daemon
Comment=Automatically suspends background browsers during Rocket League gameplay to free RAM and CPU.
EOF

chmod +x "$HOME/Documents/RocketMode/rocket_booster_daemon.sh"
chmod +x "$HOME/Documents/RocketMode/install_booster_daemon.sh"

echo -e "${GREEN}✅ RocketMode Booster Daemon registered to launch on login!${NC}"
echo "You can launch it manually right now by running:"
echo "  nohup ~/Documents/RocketMode/rocket_booster_daemon.sh > /dev/null 2>&1 &"
