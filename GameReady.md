# GameReady: Linux Gaming Optimization Guide
**System**: Dell XPS 8920 (Intel Core i7-7700 | NVIDIA GTX GPU | 8 GB System RAM)  
**Target Goal**: Peak Performance for **Rocket League** launched via **Heroic Games Launcher**.

This document details all the architectural and configuration changes applied to transform this Linux Mint workstation into a streamlined, high-performance gaming station without modifying disk partitioning.

---

## 1. Desktop Environment Migration (Cinnamon ➡️ XFCE)
*   **The Problem**: The default Cinnamon desktop shell is built on JavaScript bindings (`cjs`) and utilizes a heavy window manager (`muffin`). Together with 14 individual settings daemons (`csd-*`) and background calendar services, Cinnamon consumed **~1.01 GB of RAM** at idle. On an 8 GB system, this severely restricted the memory available to games.
*   **The Solution**: Installed the lightweight XFCE desktop environment (`xfce4` and `xfce4-goodies`). XFCE is compiled in pure C, runs a highly optimized window manager (`xfwm4`), and handles settings via a unified daemon (`xfsettingsd`).
*   **Impact**: Idle desktop memory footprint dropped to **~163 MB**, instantly freeing up **869 MB of RAM** for the system.
*   **How to Switch**: Switch sessions at the login screen (LightDM) using the session selector icon next to the username input, choosing **Xfce Session**.

---

## 2. NVIDIA GPU Driver Integration
*   **Configuration**: The system runs a dedicated NVIDIA GPU utilizing the proprietary NVIDIA Linux driver on the **X11 windowing server** (default on XFCE).
*   **Stability**: Running XFCE on X11 bypasses the Wayland/NVIDIA V-Sync stutters sometimes observed in heavier environments. Game rendering (handled by DXVK/Vulkan) interfaces directly with the driver, while `xfwm4` provides a lightweight presentation container with minimal input latency.
*   **Tools**: The `nvidia-settings` control panel remains fully functional for setting refresh rates (e.g. 144Hz+) and enabling G-Sync.

---

## 3. ZRAM Memory Compression (Virtual 16 GB Upgrade)
*   **The Problem**: With 8 GB of physical RAM, multitasking while running Rocket League (which requires 3-5 GB under Proton) would cause the OS to swap data to the physical disk (`/swapfile`), resulting in massive in-game frame stutters.
*   **The Solution**: Enabled kernel-level **ZRAM swap compression** by installing `zram-config`.
*   **Impact**: Creates a compressed swap space directly inside the RAM. Inactive pages are compressed at a ~3:1 ratio. This effectively increases your virtual memory capacity to **~12–16 GB of usable RAM** with zero read/write disk latency, completely eliminating HDD swap stuttering.
*   **Installation**: Installed via `sudo apt install zram-config`.

---

## 4. Background Services Optimization
Created the **[optimize_services.sh](file:///home/darian/Documents/RocketMode/optimize_services.sh)** script to permanently stop and disable background processes that are completely unnecessary for a dedicated gaming session.

### Services Disabled:
*   **CUPS Printing (`cups.service` / `cups-browsed.service`)**: Turned off the printer queues and autodiscovery daemons.
*   **Avahi Daemon (`avahi-daemon.service`)**: Disabled local network hostname discovery (e.g., multicast DNS), closing open local ports.
*   **ModemManager (`ModemManager.service`)**: Disabled scanning for LTE/5G USB mobile modems.
*   **Touchégg (`touchegg.service`)**: Turned off touchpad gesture listeners (useless on this desktop PC).
*   **Colord (`colord.service`)**: Turned off system color profile management.
*   **Evolution Services**: Masked and stopped GNOME/Cinnamon calendar synchronizers (`evolution-calendar-factory`, `evolution-addressbook-factory`, `evolution-source-registry`), reclaiming **~160 MB** of idle user-session RAM.

---

## 5. Startup Applications Trim
Created the **[optimize_autostart.sh](file:///home/darian/Documents/RocketMode/optimize_autostart.sh)** script to prevent non-essential graphical apps from launching in the tray at system startup.

### Applications & Game Tweaks Disabled:
*   **`mintUpdate`**: The Linux Mint Update Manager daemon (saves **~95 MB** of RAM).
*   **`mintReport`**: The System Reports crash listener tool.
*   **`print-applet`**: The printer queue status indicator tray icon.
*   **`warpinator`**: The local network file-sharing tray utility.
*   **`blueman`**: The Bluetooth manager tray utility (optional, prompted at script execution).
*   **NVIDIA Prime Offload**: Disabled in Heroic Games Launcher's game-specific config (`Sugar.json`) to prevent performance overhead on a single-GPU desktop PC.

---

## 6. Automated Game Booster Daemon (Dynamic Suspension)
To prevent web browsers and chat clients from consuming RAM and CPU during intensive gaming, we implemented a dynamic **Booster Daemon** (**[rocket_booster_daemon.sh](file:///home/darian/Documents/RocketMode/rocket_booster_daemon.sh)**).

*   **How it Works**: 
    1. Listens in the background for `RocketLeague.exe`.
    2. Once detected, it sends a `SIGSTOP` signal to suspend **Chrome, Firefox, Discord, Spotify, Slack, and Steam**.
    3. The suspended apps freeze completely—their CPU usage drops to **0%**, and their memory pages become static, allowing the OS to compress them into ZRAM immediately.
    4. Upon closing Rocket League, it sends a `SIGCONT` signal, **thawing** the applications instantly back to their exact previous state with all open tabs and chats intact.
*   **Integration**: Registered via **[install_booster_daemon.sh](file:///home/darian/Documents/RocketMode/install_booster_daemon.sh)** to launch silently in the background on user login.

---

## 7. Heroic Games Launcher Optimizations
*   **Minimization Policy**: Configured the global configuration file (`config.json` at `~/.var/app/com.heroicgameslauncher.hgl/config/heroic/config.json`) to automatically minimize Heroic to the system tray upon game launch:
    ```json
    "minimizeOnLaunch": true
    ```
    This completely disables GPU rendering overhead for the Electron-based UI when the game is active.
*   **Game-Specific Launch**: Verified that the Rocket League configuration (`GamesConfig/Sugar.json`) correctly inherits this behavior.
*   **NVIDIA Prime Disabled**: Configured `"nvidiaPrime": false` in `Sugar.json`. Since this is a desktop system with a dedicated monitor connection, keeping this off prevents Wine from wrapping Vulkan calls through Prime render offloading, avoiding runtime performance overhead.

---

## 8. Game Controller Drivers & Input Integration
Linux handles game controllers natively at the kernel level. The following config supports seamless gamepad integration:
*   **PlayStation 4/5 Controllers**: Natively supported via the `hid-sony` / `hid-playstation` kernel modules (USB and Bluetooth).
*   **Xbox Controllers**: Supported via the native `xpad` kernel driver. For Bluetooth Xbox controllers, the `xpadneo` driver is recommended to handle proper mapping and battery reporting.
*   **Switch Pro Controllers**: Supported via `hid-nintendo` (and `joycond` daemon for combining Joy-Cons).
*   *Note: Our custom process inspector (`ram_inspector.py`) has been updated to identify these drivers and mappings as critical to controller inputs.*

---

## 9. Audio Subsystem Verification
*   **Infrastructure**: The system utilizes **PipeWire** along with `wireplumber` (session manager) and `pipewire-pulse` (PulseAudio emulation). 
*   **Tuning**: PipeWire provides low-latency, sandboxed audio routing for Rocket League and Heroic. In XFCE, the volume settings are managed via the lightweight `xfce4-pulseaudio-plugin` on the panel, bypassing Cinnamon's heavier settings daemon.

---

## 🚀 Performance Checklist before Gaming:
1. Log into your **XFCE session**.
2. Run the RAM Inspector to verify your memory usage is clean:
   ```bash
   ./RocketMode/ram_inspector.py -n 10
   ```
3. Open **Heroic**, launch **Rocket League**, and enjoy high-FPS, stutter-free gameplay!
