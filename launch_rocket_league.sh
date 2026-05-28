#!/usr/bin/env bash
# Master launcher for Rocket League with performance optimization.
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to kill all flatpak, wine, proton, and heroic processes
terminate_game_and_compatibility_layers() {
    echo "🛑 Terminating any lingering Flatpak, Heroic, and Wine/Proton processes..."
    flatpak kill com.heroicgameslauncher.hgl || true
    pkill -u "$USER" -9 -f "wineserver" || true
    pkill -u "$USER" -9 -f "wine64" || true
    pkill -u "$USER" -9 -f "winedevice.exe" || true
    pkill -u "$USER" -9 -f "services.exe" || true
    pkill -u "$USER" -9 -f "explorer.exe /desktop" || true
    pkill -u "$USER" -9 -f "rpcss.exe" || true
    pkill -u "$USER" -9 -f "plugplay.exe" || true
    pkill -u "$USER" -9 -f "svchost.exe" || true
    pkill -u "$USER" -9 -f "tabtip.exe" || true
    pkill -u "$USER" -9 -f "RocketLeague.exe" || true
    pkill -u "$USER" -9 -f "umu_run" || true
    pkill -u "$USER" -9 -f "umu-shim" || true
    pkill -u "$USER" -9 -f "pressure-vessel" || true
    pkill -u "$USER" -9 -f "pv-adverb" || true
    pkill -u "$USER" -9 -f "legendary" || true
    pkill -u "$USER" -9 -f "/app/bin/heroic" || true
}

# Clean up any leftover processes from previous crashes/runs before starting
terminate_game_and_compatibility_layers

# Check if GUI mode is requested
GUI_MODE=false
for arg in "$@"; do
    if [ "$arg" = "--gui" ]; then
        GUI_MODE=true
    fi
done

echo "🧹 Running gaming environment cleanup..."
python3 "$SCRIPT_DIR/clean_gaming_env.py" "$@"


# If dry-run was requested, exit here
for arg in "$@"; do
    if [ "$arg" = "--dry-run" ]; then
        echo "🧹 Dry-run complete. Skipping telemetry logger and game launch."
        exit 0
    fi
done

# Check if wired ethernet has link/carrier and actual internet access
ETHERNET_STATUS=$(cat /sys/class/net/enp4s0/carrier 2>/dev/null || echo "0")
WIRED_INTERNET=false
if [ "$ETHERNET_STATUS" = "1" ]; then
    if ping -c 1 -W 2 -I enp4s0 1.1.1.1 >/dev/null 2>&1; then
        WIRED_INTERNET=true
    fi
fi

if [ "$WIRED_INTERNET" = true ]; then
    echo "🔌 Active wired internet connection detected on enp4s0! Temporarily disabling WiFi to force wired-only connection..."
    nmcli radio wifi off >/dev/null 2>&1 || true
    WIFI_DISABLED_BY_US=true
else
    echo "⚠️ WARNING: Wired connection (enp4s0) is not active or has no internet access. Keeping WiFi enabled to prevent going offline."
    WIFI_DISABLED_BY_US=false
    # Auto-restore WiFi if it was left disabled by a crashed run
    if [ "$(nmcli radio wifi)" = "disabled" ]; then
        echo "📡 WiFi was disabled. Re-enabling WiFi to ensure internet access..."
        nmcli radio wifi on >/dev/null 2>&1 || true
    fi
fi

# Start the telemetry logger
python3 "$SCRIPT_DIR/game_logger.py" --start

# Ensure we always stop the logger, terminate game/Wine, and restore systemd user services on exit
cleanup() {
    echo "📊 Compiling performance telemetry report..."
    python3 "$SCRIPT_DIR/game_logger.py" --stop
    
    terminate_game_and_compatibility_layers
    
    if [ "$WIFI_DISABLED_BY_US" = true ]; then
        echo "📡 Re-enabling WiFi..."
        nmcli radio wifi on >/dev/null 2>&1 || true
    fi
    
    echo "♻️ Restoring background systemd user services..."
    systemctl --user start gvfs-daemon.service gvfs-mtp-volume-monitor.service gvfs-udisks2-volume-monitor.service gnome-keyring-daemon.service xfce4-notifyd.service at-spi-dbus-bus.service gpg-agent.service || true
}
trap cleanup EXIT

echo "🎮 Launching Rocket League via Heroic Games Launcher (with FSR, DXVK, and low-latency audio optimizations)..."
# Run Flatpak in the foreground but spawn a monitor in the background first
(
    # Monitor for the game starting (timeout: 120 seconds)
    GAME_PID=""
    for i in {1..150}; do
        GAME_PID=$(pgrep -u "$USER" -f -i "RocketLeague.exe" | head -n 1 || true)
        if [ -n "$GAME_PID" ]; then
            break
        fi
        sleep 2
    done

    if [ -z "$GAME_PID" ]; then
        echo "⚠️ Rocket League failed to start within 300 seconds."
        flatpak kill com.heroicgameslauncher.hgl || true
        exit 1
    fi

    # Wait for Main Menu / Authentication completion in game logs
    echo "⏳ Game started (PID: $GAME_PID). Waiting for Main Menu login to complete..."
    LOG_FILE="/home/darian/Games/Heroic/Prefixes/Rocket League/drive_c/users/steamuser/Documents/My Games/Rocket League/TAGame/Logs/Launch.log"
    
    # Wait for log file creation
    for i in {1..30}; do
        if [ -f "$LOG_FILE" ]; then
            break
        fi
        sleep 1
    done
    
    if [ -f "$LOG_FILE" ]; then
        echo "⏳ Monitoring game log for Main Menu load..."
        # Avoid hanging forever if the game crashes/exits before loading the menu
        while kill -0 "$GAME_PID" 2>/dev/null; do
            if grep -q -E "m_uiState:MainMenu|LoadMap: MENU_Main_p" "$LOG_FILE"; then
                echo "🎮 Main Menu loaded and authenticated!"
                break
            fi
            sleep 1
        done
        
        # RAM/VRAM snapshots have been moved to the standalone take_ram_snapshot.sh script
        # nvidia-smi -q -d MEMORY,PIDS > "/home/darian/Documents/RocketMode/nvidia_vram_snapshot.txt" 2>&1 || true
        # gcore -o "/home/darian/Documents/RocketMode/rocketleague_ram.dump" "$GAME_PID" || true
    fi
    
    # Terminate Heroic UI to reclaim ~400MB RAM (disabled: terminating Heroic kills the Flatpak sandbox/game)
    # echo "🧹 Reclaiming RAM: Terminating Heroic Games Launcher UI..."
    # pkill -u "$USER" -f "/app/bin/heroic/heroic" || true

    # Now block/wait until the game PID exits
    echo "🎮 Rocket League session active. Monitoring game process..."
    while kill -0 "$GAME_PID" 2>/dev/null; do
        sleep 2
    done

    echo "🚀 Rocket League has closed."
    flatpak kill com.heroicgameslauncher.hgl || true
) &

# Run Flatpak in the foreground
FLATPAK_ARGS=()

flatpak run \
    --env=WINE_FULLSCREEN_FSR=1 \
    --env=WINE_FULLSCREEN_FSR_STRENGTH=2 \
    --env=DXVK_CONFIG="dxvk.numCompilerThreads = 4; dxgi.maxDeviceMemory = 2048; dxgi.maxSharedMemory = 4096" \
    --env=PIPEWIRE_LATENCY="128/48000" \
    com.heroicgameslauncher.hgl "${FLATPAK_ARGS[@]}" --launch Sugar

echo "🚀 Workstation session remains active."
