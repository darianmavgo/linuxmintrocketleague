#!/usr/bin/env bash
# Diagnostics script to capture RAM core dump and GPU VRAM snapshot of Rocket League manually.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GAME_PID=$(pgrep -u "$USER" -f -i "RocketLeague.exe" | head -n 1 || true)

if [ -z "$GAME_PID" ]; then
    echo "❌ Rocket League is not running!"
    exit 1
fi

echo "📸 Capturing GPU VRAM allocation snapshot..."
nvidia-smi -q -d MEMORY,PIDS > "$SCRIPT_DIR/nvidia_vram_snapshot.txt" 2>&1 || true
echo "✓ VRAM snapshot saved to $SCRIPT_DIR/nvidia_vram_snapshot.txt"

echo "📸 Capturing RAM core dump of Rocket League (PID: $GAME_PID) via gcore..."
gcore -o "$SCRIPT_DIR/rocketleague_ram.dump" "$GAME_PID" || true
echo "✓ RAM core dump saved to $SCRIPT_DIR/rocketleague_ram.dump.$GAME_PID"
