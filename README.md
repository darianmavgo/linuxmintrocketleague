# RocketMode Memory & Process Diagnostics

A high-fidelity Python diagnostic utility designed to audit memory usage on Linux systems. It parses system `/proc` endpoints directly, making it completely self-contained with **zero external package dependencies**.

## Features

- **RAM Memory Distribution Summary**: Parses `/proc/meminfo` to display total, active used, available, free, buffer/cache, kernel slab, and page table memory allocations. Includes a visual terminal progress bar.
- **Temporary Filesystems (tmpfs)**: Scans `/proc/mounts` and uses `statvfs` to calculate exact RAM consumption by virtual memory drives (e.g. `/run`, `/dev/shm`).
- **Process Memory Table**: Collects all active process statistics from `/proc/[pid]` directories. Displays PID, User, Process Name, RSS (Resident Set Size), VSZ (Virtual Size), % RAM, and the full command line.
- **Sorting**: Interactive sorting by RAM usage, Virtual Memory usage, name, or PID.
- **Reporting & Exports**:
  - **CLI**: Colorized and Unicode-bordered tables.
  - **HTML**: Translucent Glassmorphism dashboard featuring live search and interactive column sorting.
  - **Markdown**: Formatted tables suitable for GitHub or Wiki pages.
  - **JSON**: Raw structured data for automated consumption.

## Usage

Navigate to the `RocketMode` folder and execute `ram_inspector.py`:

```bash
./ram_inspector.py [OPTIONS]
```

### CLI Command Options

```
options:
  -h, --help            show this help message and exit
  -n LIMIT, --limit LIMIT
                        Number of processes to list in terminal (default: 20)
  -s {rss,vsz,name,pid}, --sort {rss,vsz,name,pid}
                        Column to sort processes by (default: rss)
  -o HTML, --html HTML  Export interactive HTML report to this file path
  -m MARKDOWN, --markdown MARKDOWN
                        Export markdown report to this file path
  -j JSON, --json JSON  Export raw diagnostic data in JSON format to this file path
  -no-color             Disable terminal colors
```

### Examples

1. **Print top 15 memory-consuming processes to the terminal:**
   ```bash
   ./ram_inspector.py -n 15
   ```

2. **Sort by Process Name instead of RAM usage:**
   ```bash
   ./ram_inspector.py --sort name
   ```

3. **Export all diagnostics to terminal, HTML, Markdown, and JSON simultaneously:**
   ```bash
   ./ram_inspector.py -o report.html -m report.md -j report.json
   ```

## Output Visuals

### Terminal Table
The CLI outputs Unicode tables:
```
┌──────┬────────┬──────────────┬────────────────┬───────────────┬───────┬─────────────────┐
│  PID │ User   │ Process Name │ RSS (Resident) │ VSZ (Virtual) │ % RAM │ Command Line    │
├──────┼────────┼──────────────┼────────────────┼───────────────┼───────┼─────────────────┤
│ 1909 │ darian │ cinnamon     │      321.58 MB │       4.36 GB │ 4.10% │ cinnamon        │
└──────┴────────┴──────────────┴────────────────┴───────────────┴───────┴─────────────────┘
```

### Interactive HTML Dashboard
The exported `report.html` features:
- A responsive modern dark theme layout.
- Real-time searching/filtering.
- Sorting by column.
- Translucent backdrop blur cards (Glassmorphism).

## Repository Scripts Summary

This folder contains various scripts designed to optimize, launch, and monitor a Linux gaming environment (specifically for Rocket League). 

### Launch & Environment
- **`launch_rocket_league.sh`**: Master launch script for Rocket League via Heroic Games Launcher. Coordinates environment cleanup, telemetry, and launch flags.
- **`clean_gaming_env.py`**: Cleans up the environment before gaming by terminating non-essential processes based on a whitelist to free up memory.

### Optimization & Boosting
- **`game_booster.sh`**: Stops desktop components and non-essential system services for a gaming boost mode, with an option to restore them later.
- **`rocket_booster_daemon.sh`**: Background daemon that automatically suspends resource-hogging apps (e.g., browsers, Discord) when Rocket League is running, and resumes them when it closes.
- **`install_booster_daemon.sh`**: Registers the RocketMode Booster Daemon to start automatically on user login.
- **`optimize_autostart.sh`**: Disables non-gaming background applications from launching at login.
- **`optimize_services.sh`**: Disables background system services (CUPS, Avahi, etc.) that are unnecessary for gaming.

### Memory & Swap Management
- **`ram_inspector.py`**: Diagnostic utility to inspect system RAM, tmpfs, and process memory, with CLI, HTML, and Markdown export capabilities.
- **`cap_zram.sh`**: Limits the ZRAM swap size to 1 GB.
- **`disable_hdd_swap.sh`**: Disables and removes the HDD/SSD swap file, keeping only ZRAM for swap.
- **`setup_swap.sh`**: Creates, configures, and enables an 8GB swap file.
- **`tune_system_memory.sh`**: Optimizes system kernel parameters (e.g., `vm.swappiness`) for ZRAM and gaming workloads.
- **`take_ram_snapshot.sh`**: Captures a GPU VRAM snapshot and a RAM core dump of the running Rocket League process.

### Telemetry & Diagnostics
- **`game_logger.py`**: Telemetry logger daemon that tracks memory, ZRAM usage, game processes, and GPU usage during a gaming session.
- **`desktop_comparison.py`**: Compares Cinnamon's memory footprint against a simulated XFCE footprint to calculate memory savings.
- **`test_controller.py`**: Reads and displays raw events from a controller device (e.g., `/dev/input/js0`) for testing inputs.

### System Fixes
- **`apply_grub_patch.sh`**: Applies a GRUB patch (`pci=noaer`) to disable PCIe AER log flooding.
- **`fix_audio.sh`**: Applies temporary pin connectivity overrides to the Intel/Realtek Audio codec.
- **`make_audio_permanent.sh`**: Creates a persistent kernel firmware patch to permanently apply Realtek ALC3861 audio jack overrides.
- **`persist_audio.sh`**: Creates a systemd service to apply HDA jack overrides on boot.
- **`generate_melody.py`**: Generates a C major chord arpeggio WAV audio file (useful for testing audio output).
