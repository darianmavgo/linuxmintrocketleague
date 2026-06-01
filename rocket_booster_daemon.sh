#!/usr/bin/env bash
# RocketMode Game Booster Daemon
# Automatically suspends background browsers and resource-hogs (reducing their CPU/RAM footprint)
# when Rocket League starts, and resumes them instantly when the game exits.

set -e

# Target applications to suspend (matching process names exactly)
TARGETS=("chrome" "firefox" "discord" "spotify" "slack" "steamwebhelper" "heroic")

echo "🚀 RocketMode Game Booster Daemon active. Listening for Rocket League..."

while true; do
    # Check if RocketLeague.exe is running (case-insensitive check on cmdline)
    GAME_PID=$(pgrep -f -i "RocketLeague.exe" | head -n 1 || true)
    
    if [ -n "$GAME_PID" ]; then
        echo "🎮 Rocket League detected (PID: $GAME_PID)! Suspending background apps to free RAM and CPU..."
        
        SUSPENDED_PIDS=()
        
        # Suspend target apps and reclaim their memory
        for app in "${TARGETS[@]}"; do
            # Get PIDs for this app belonging to current user
            PIDS=$(pgrep -u "$USER" -x "$app" || true)
            for pid in $PIDS; do
                if [ "$pid" != "$$" ] && [ "$pid" != "$GAME_PID" ]; then
                    # Send SIGSTOP to freeze the process
                    if kill -STOP "$pid" 2>/dev/null; then
                        SUSPENDED_PIDS+=("$pid")
                        
                        # Reclaim memory from the cgroup of the suspended process (cgroup v2)
                        if [ -f "/proc/$pid/cgroup" ]; then
                            CGROUP_PATH=$(grep -E '^0::' "/proc/$pid/cgroup" | cut -d: -f3 || true)
                            if [ -n "$CGROUP_PATH" ] && [ -f "/sys/fs/cgroup$CGROUP_PATH/memory.reclaim" ]; then
                                echo "❄️ Reclaiming memory from $app (PID: $pid, Cgroup: $CGROUP_PATH)..."
                                echo "999G" > "/sys/fs/cgroup$CGROUP_PATH/memory.reclaim" 2>/dev/null || true
                            fi
                        fi
                    fi
                fi
            done
        done
        
        echo "❄️ Suspended ${#SUSPENDED_PIDS[@]} process(es)."
        
        # Monitor the game process; loop until it is no longer running
        while kill -0 "$GAME_PID" 2>/dev/null; do
            sleep 1.5
        done
        
        echo "🏁 Rocket League exited. Restoring background apps..."
        
        # Send SIGCONT to resume the processes
        for pid in "${SUSPENDED_PIDS[@]}"; do
            kill -CONT "$pid" 2>/dev/null || true
        done
        
        echo "☀️ Background apps restored. Resuming listener loop..."
    fi
    
    # Check every 2 seconds when game is not running
    sleep 2
done
