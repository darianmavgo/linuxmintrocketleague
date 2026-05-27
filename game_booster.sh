#!/usr/bin/env bash

# Game Booster Script for Rocket League / Heroic Games Launcher
# Saves memory by stopping desktop components and non-essential system services,
# and offers a way to restore them after the gaming session is complete.

# Colors for premium CLI output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if script is run as root for systemctl commands
is_root() {
    [ "$EUID" -eq 0 ]
}

check_sudo() {
    if ! is_root; then
        echo -e "${YELLOW}[!] This action requires administrative privileges to manage system services.${NC}"
        echo -e "${YELLOW}[!] Please run with: sudo $0 <action>${NC}"
        exit 1
    fi
}

start_boost() {
    echo -e "${BLUE}=== ENABLING GAMING BOOST MODE ===${NC}"
    
    # 1. Kill XFCE Desktop Components (Non-essential for fullscreen gaming)
    echo -e "${YELLOW}[*] Stopping XFCE Desktop processes...${NC}"
    
    # xfdesktop controls icons/wallpapers; safe to quit
    if pgrep xfdesktop >/dev/null; then
        xfdesktop --quit 2>/dev/null || killall xfdesktop
        echo -e "  ${GREEN}✓ Stopped xfdesktop (Desktop Icons/Wallpaper)${NC}"
    fi

    # xfce4-panel and its wrappers; safe to kill
    if pgrep xfce4-panel >/dev/null; then
        killall xfce4-panel
        echo -e "  ${GREEN}✓ Stopped xfce4-panel & wrappers${NC}"
    fi

    # xfsettingsd manages shortcuts, DPI, cursor size, and styling.
    # Killing it is safe, but you might temporarily lose custom settings until restored.
    if pgrep xfsettingsd >/dev/null; then
        killall xfsettingsd
        echo -e "  ${GREEN}✓ Stopped xfsettingsd (Desktop Settings)${NC}"
    fi

    # Note: We do NOT kill xfwm4 (Window Manager) by default, as it can cause focus issues with launcher windows.
    # We do NOT kill xfce4-session, as doing so would immediately log you out.

    # 2. Stop Core Operating System Services (Requires Sudo)
    check_sudo
    echo -e "${YELLOW}[*] Stopping non-essential systemd services...${NC}"
    
    SERVICES_TO_STOP=(
        "accounts-daemon.service"      # User account query tool
        "colord.service"               # Device color profile management
        "cron.service"                 # Background task scheduler
        "fwupd.service"                # Firmware updates
        "kerneloops.service"           # Kernel crash reporter daemon
        "rsyslog.service"              # Traditional syslog recorder (logs are still in journald)
        "udisks2.service"              # Disk partition mounting manager (safe if game is on internal drive)
        "upower.service"               # Battery and power source daemon
        "switcheroo-control.service"   # Dual-GPU router (already assigned to GPU when launched)
    )

    for service in "${SERVICES_TO_STOP[@]}"; do
        if systemctl is-active --quiet "$service"; then
            systemctl stop "$service"
            echo -e "  ${GREEN}✓ Stopped $service${NC}"
        fi
    done

    # 3. Terminate Other Swapped / Idle Processes
    echo -e "${YELLOW}[*] Cleaning up other idle processes...${NC}"
    
    # Inactive helper applets or orphan commands
    IDLE_PROCS=("nvidia-prime" "nvidia-prime-applet" "p11-kit-server" "flatpak-session-helper" "dconf-service" "cat")
    for proc in "${IDLE_PROCS[@]}"; do
        if pgrep -f "$proc" >/dev/null; then
            killall -q -f "$proc"
            echo -e "  ${GREEN}✓ Terminated $proc${NC}"
        fi
    done

    echo -e "${GREEN}[+] Boost Mode active. Rocket League now has maximum memory access!${NC}"
    echo -e "${YELLOW}[i] Run 'sudo $0 restore' to bring back all services and panels when done.${NC}"
}

restore_system() {
    echo -e "${BLUE}=== RESTORING STANDARD DESKTOP ENVIRONMENT ===${NC}"
    
    # 1. Start Core Operating System Services
    check_sudo
    echo -e "${YELLOW}[*] Starting systemd services...${NC}"
    
    SERVICES_TO_START=(
        "accounts-daemon.service"
        "colord.service"
        "cron.service"
        "fwupd.service"
        "kerneloops.service"
        "rsyslog.service"
        "udisks2.service"
        "upower.service"
        "switcheroo-control.service"
    )

    for service in "${SERVICES_TO_START[@]}"; do
        systemctl start "$service"
        echo -e "  ${GREEN}✓ Started $service${NC}"
    done

    # 2. Restart XFCE Desktop Components (Run in user space, not root/sudo)
    # If the user ran 'sudo script.sh restore', we try to run the GUI apps as the actual user
    REAL_USER=${SUDO_USER:-$USER}
    
    if [ "$REAL_USER" = "root" ]; then
        echo -e "${RED}[!] WARNING: Running GUI restoration as root. Panels might launch with root privileges.${NC}"
        xfsettingsd &
        xfce4-panel &
        xfdesktop &
    else
        echo -e "${YELLOW}[*] Restoring XFCE GUI components for user '$REAL_USER'...${NC}"
        su - "$REAL_USER" -c "DISPLAY=:0 xfsettingsd" &>/dev/null &
        su - "$REAL_USER" -c "DISPLAY=:0 xfce4-panel" &>/dev/null &
        su - "$REAL_USER" -c "DISPLAY=:0 xfdesktop" &>/dev/null &
    fi

    echo -e "${GREEN}[+] Desktop and services successfully restored!${NC}"
}

# CLI Argument parsing
case "$1" in
    boost)
        start_boost
        ;;
    restore)
        restore_system
        ;;
    *)
        echo -e "${YELLOW}Usage: sudo $0 {boost|restore}${NC}"
        exit 1
        ;;
esac
