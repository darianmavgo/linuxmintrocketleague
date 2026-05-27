#!/usr/bin/env bash
# RocketMode Linux Gaming Service Optimizer
# Disables background services that are unnecessary for gaming (Rocket League & Heroic)

set -e

# Formatting colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 ROCKETMODE SERVICE OPTIMIZER${NC}"
echo -e "This script disables background services that are unnecessary for gaming."
echo -e "No files are deleted, and rollback commands are provided at the end.\n"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: Please run the script with sudo to modify system services:${NC}"
  echo "sudo ./optimize_services.sh"
  exit 1
fi

# Store the actual non-root user (since script runs with sudo)
SUDO_USER_NAME="${SUDO_USER:-$USER}"
USER_ID=$(id -u "$SUDO_USER_NAME")

# 1. System Services (CUPS, Avahi, ModemManager, Touchegg, Colord)
echo -e "${YELLOW}[1/3] Optimizing System Services...${NC}"

# CUPS (Printing)
echo "Disabling CUPS Printer Spooler & Autodiscovery..."
systemctl disable --now cups.service cups-browsed.service 2>/dev/null || true

# Avahi (Network Autodiscovery)
echo "Disabling Avahi Local Network Service Autodiscovery..."
systemctl disable --now avahi-daemon.service avahi-daemon.socket 2>/dev/null || true

# ModemManager (Mobile Broadband)
echo "Disabling Mobile Broadband Modem Manager..."
systemctl disable --now ModemManager.service 2>/dev/null || true

# Touchegg (Touchpad Gestures - not needed on desktops)
echo "Disabling Touchegg Multitouch Gestures..."
systemctl disable --now touchegg.service 2>/dev/null || true

# Colord (Color Profile Manager)
echo "Disabling Color Profile Manager..."
systemctl disable --now colord.service 2>/dev/null || true

# 2. Bluetooth Query (Interactive/Conditional)
echo ""
read -p "Do you use Bluetooth controllers (e.g. Xbox/PS4) or Bluetooth headphones? [y/N]: " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "Disabling Bluetooth Services..."
    systemctl disable --now bluetooth.service 2>/dev/null || true
else
    echo -e "${GREEN}Keeping Bluetooth enabled for your controllers/audio.${NC}"
fi

# 3. User Services (Evolution Sync, OBEX, Mobile Volume Monitors)
echo -e "\n${YELLOW}[2/3] Optimizing User Session Services (for user: $SUDO_USER_NAME)...${NC}"

# Define command wrapper to execute systemctl --user as the login user
run_as_user() {
    sudo -i -u "$SUDO_USER_NAME" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$USER_ID/bus" "$@"
}

# Evolution Calendar Sync (Not needed in XFCE)
echo "Masking GNOME Evolution Calendar and Contact synchronization engines..."
run_as_user systemctl --user mask evolution-addressbook-factory.service evolution-calendar-factory.service evolution-source-registry.service evolution-calendar-factory 2>/dev/null || true
run_as_user systemctl --user stop evolution-addressbook-factory.service evolution-calendar-factory.service evolution-source-registry.service evolution-calendar-factory 2>/dev/null || true

# Obex Bluetooth file transfer
echo "Stopping OBEX Bluetooth file transfer service..."
run_as_user systemctl --user disable --now obex.service 2>/dev/null || true

# Apple Device and Camera Autodetect volume monitors
echo "Masking GVFS Apple Device and Digital Camera volume monitors..."
run_as_user systemctl --user mask gvfs-afc-volume-monitor.service gvfs-gphoto2-volume-monitor.service gvfs-goa-volume-monitor.service 2>/dev/null || true
run_as_user systemctl --user stop gvfs-afc-volume-monitor.service gvfs-gphoto2-volume-monitor.service gvfs-goa-volume-monitor.service 2>/dev/null || true

echo -e "\n${GREEN}✅ OPTIMIZATIONS APPLIED SUCCESSFULLY!${NC}"
echo "System memory footprint has been optimized."

# 4. Rollback commands documentation
echo -e "\n${YELLOW}------------------------------------------------------------${NC}"
echo -e "${YELLOW}REVERSION / ROLLBACK COMMANDS:${NC}"
echo "If you ever need to restore these services, run the following commands:"
echo ""
echo "Restore System Services (Printing, Network discovery, etc.):"
echo "  sudo systemctl enable --now cups.service cups-browsed.service avahi-daemon.service colord.service ModemManager.service bluetooth.service"
echo ""
echo "Restore User Session Services (Evolution, GVFS Monitors):"
echo "  systemctl --user unmask evolution-addressbook-factory.service evolution-calendar-factory.service evolution-source-registry.service gvfs-afc-volume-monitor.service gvfs-gphoto2-volume-monitor.service gvfs-goa-volume-monitor.service"
echo "  systemctl --user enable --now obex.service"
echo -e "${YELLOW}------------------------------------------------------------${NC}"
