#!/usr/bin/env python3
import os
import sys
import re
import pwd
import json
import argparse
from datetime import datetime

# ANSI Escape Codes for Colors
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREY = "\033[90m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_MAGENTA = "\033[35m"
COLOR_CYAN = "\033[36m"
COLOR_WHITE = "\033[37m"

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def format_size(bytes_val):
    if bytes_val is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def make_bar(percentage, width=30, color_code=COLOR_GREEN, no_color=False):
    percentage = max(0.0, min(100.0, percentage))
    filled = int(round(percentage * width / 100))
    empty = width - filled
    bar_str = "█" * filled + "░" * empty
    if no_color:
        return f"[{bar_str}] {percentage:.1f}%"
    return f"[{color_code}{bar_str}{COLOR_RESET}] {COLOR_BOLD}{percentage:.1f}%{COLOR_RESET}"

def get_rl_relationship(name, cmdline):
    name_lower = name.lower()
    cmd_lower = cmdline.lower()
    
    # Rocket League game itself
    if "rocketleague" in name_lower or "rocketleague" in cmd_lower:
        return (
            "Runs the main Rocket League game client (physics, matchmaking, rendering, gameplay loop).",
            "The game closes immediately, ending your session."
        )
    
    # Heroic Games Launcher
    if "heroic" in name_lower or "heroic" in cmd_lower:
        return (
            "The graphical interface of Heroic Games Launcher; manages installs, settings, and wine prefixes.",
            "You cannot browse your library, launch games, sync cloud saves, or configure settings."
        )
        
    # Legendary (backend for Epic Games)
    if "legendary" in name_lower:
        return (
            "Heroic's CLI backend for Epic Games Store; handles authentication, ownership checks, and game downloads.",
            "Game launch authorization fails, updates cannot download, and offline mode sync is disabled."
        )
        
    # Wine Server
    if "wineserver" in name_lower:
        return (
            "Core Wine daemon coordinating inter-process communication, registry emulation, and Wine threads.",
            "All Wine/Proton processes (Rocket League, Epic Online Services) will crash instantly."
        )
        
    # Wine / Proton loaders
    if "wine" in name_lower or "proton" in name_lower or "winedevice" in name_lower or "plugplay.exe" in name_lower or "explorer.exe" in name_lower:
        if "winedevice" in name_lower:
            return (
                "Emulates Windows plug-and-play device drivers, handling controller inputs, audio routing, and system devices.",
                "Game controller input, audio playback, and USB device detection within the game will fail."
            )
        elif "explorer" in name_lower:
            return (
                "Emulates the Windows Explorer shell for basic window management and tray integration required by game launch scripts.",
                "Window focusing, fullscreen-to-background transitions, and system tray integrations may hang."
            )
        else:
            return (
                "Provides the compatibility layer (Wine/Proton) executing the Windows-compiled Rocket League binary on Linux.",
                "Rocket League will fail to start, or crash if currently running."
            )

    # Epic Online Services (EOS)
    if "eosbind" in name_lower or "eos" in name_lower or "epic" in cmd_lower:
        return (
            "Handles Epic Online Services (EOS) authentication, cross-play matchmaking, friends list sync, and multiplayer stats.",
            "Multiplayer matchmaking, invite system, and sync with Epic Games servers will be disabled."
        )
        
    # Audio Servers
    if any(k in name_lower for k in ["pipewire", "pulseaudio", "wireplumber", "sndiod"]):
        return (
            "Manages the Linux system audio server, routing Rocket League's sound output and mic input.",
            "The game will be completely silent, and voice chat will not function."
        )
        
    # Display Servers / Window Managers
    if any(k in name_lower for k in ["xorg", "wayland", "mutter", "kwin", "cinnamon", "gnome-shell", "weston"]):
        return (
            "The display server and window manager rendering Rocket League's graphics on your monitor and capturing inputs.",
            "The graphical session terminates, immediately closing Heroic, Rocket League, and all open windows."
        )
        
    # GPU Driver processes or Vulkan loaders
    if any(k in name_lower for k in ["nvidia", "intel-gpu", "radeontop", "amdgpu"]):
        return (
            "Underlying GPU driver/monitoring daemon providing low-level hardware access for Vulkan/OpenGL rendering.",
            "Rocket League will drop to software rendering (unplayable slideshow), fail to start, or crash."
        )

    # Controller / Input mapping daemons (e.g. joycond, ds4drv, xboxdrv, antimicro, input-remapper)
    if any(k in name_lower for k in ["joycond", "ds4drv", "xboxdrv", "antimicro", "input-remapper"]):
        return (
            "Input mapper/driver translating your game controller (Xbox/PlayStation/Switch) signals into standard game inputs.",
            "Your game controller will become unresponsive or button mappings will be scrambled inside Rocket League."
        )

    # Steam (if used as runner/runner provider)
    if "steam" in name_lower or "steamwebhelper" in name_lower:
        return (
            "Provides Steam overlay, Proton runtime containers, and Steam Input controller configuration libraries.",
            "Controller layouts mapped via Steam Input will fail, and Steam Proton compatibility runs may error."
        )
        
    # Antigravity (AI Coding Assistant)
    if "antigravity" in name_lower or "antigravity" in cmd_lower:
        return (
            "The Antigravity AI pair programmer agent context (currently performing system diagnostics).",
            "This interactive AI development session will terminate immediately."
        )
        
    # General System utilities
    if any(k in name_lower for k in ["systemd", "dbus", "udevd", "journald", "cron", "rsyslogd", "login", "getty", "bash", "sh", "python"]):
        return (
            "Linux system daemon/shell providing basic OS infrastructure, hardware polling, and environment capabilities.",
            "The operating system will become unstable or crash, taking Rocket League and Heroic Launcher down with it."
        )

    # Default fallback
    return (
        "Non-critical background system process or application running concurrently with your game session.",
        "No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance."
    )

def get_meminfo():
    meminfo = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    val = int(parts[1]) * 1024  # convert kB to bytes
                    meminfo[key] = val
    except IOError as e:
        print(f"Error reading /proc/meminfo: {e}", file=sys.stderr)
    return meminfo

def get_tmpfs_mounts():
    tmpfs_mounts = []
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3:
                    dev, mount_point, fstype = parts[0], parts[1], parts[2]
                    if fstype == 'tmpfs':
                        try:
                            stat = os.statvfs(mount_point)
                            total = stat.f_blocks * stat.f_frsize
                            free = stat.f_bfree * stat.f_frsize
                            used = total - free
                            tmpfs_mounts.append({
                                'mount_point': mount_point,
                                'total': total,
                                'used': used,
                                'free': free,
                                'percent_used': (used / total * 100) if total > 0 else 0.0
                            })
                        except OSError:
                            # Permission denied or mount point inaccessible
                            continue
    except IOError as e:
        print(f"Error reading /proc/mounts: {e}", file=sys.stderr)
    return tmpfs_mounts

def get_processes():
    processes = []
    # Cache username lookups to speed up execution
    user_cache = {}
    
    for pid_dir in os.listdir('/proc'):
        if pid_dir.isdigit():
            pid = int(pid_dir)
            try:
                status_path = os.path.join('/proc', pid_dir, 'status')
                cmdline_path = os.path.join('/proc', pid_dir, 'cmdline')
                
                name = None
                uid = None
                rss = 0
                vsz = 0
                
                if not os.path.exists(status_path):
                    continue
                    
                with open(status_path, 'r') as f:
                    for line in f:
                        if line.startswith('Name:'):
                            name = line.split(None, 1)[1].strip()
                        elif line.startswith('Uid:'):
                            uid = int(line.split()[1])
                        elif line.startswith('VmRSS:'):
                            rss = int(line.split()[1]) * 1024  # kB to bytes
                        elif line.startswith('VmSize:'):
                            vsz = int(line.split()[1]) * 1024  # kB to bytes
                
                # Retrieve command line
                cmdline = ""
                if os.path.exists(cmdline_path):
                    with open(cmdline_path, 'rb') as f:
                        cmd_bytes = f.read()
                        if cmd_bytes:
                            cmdline = cmd_bytes.replace(b'\x00', b' ').decode('utf-8', errors='ignore').strip()
                
                if not cmdline and name:
                    cmdline = f"[{name}]"
                elif not cmdline:
                    cmdline = "unknown"
                
                # Resolve username
                username = "unknown"
                if uid is not None:
                    if uid in user_cache:
                        username = user_cache[uid]
                    else:
                        try:
                            username = pwd.getpwuid(uid).pw_name
                        except KeyError:
                            username = str(uid)
                        user_cache[uid] = username
                
                role, breaks = get_rl_relationship(name or 'unknown', cmdline)
                processes.append({
                    'pid': pid,
                    'user': username,
                    'name': name or 'unknown',
                    'rss': rss,
                    'vsz': vsz,
                    'cmdline': cmdline,
                    'rl_role': role,
                    'what_breaks': breaks
                })
            except (IOError, OSError, ValueError):
                # Handle process terminated or permission errors gracefully
                continue
    return processes

def print_table(headers, rows, alignments=None, no_color=False):
    if not rows:
        print("No data available.")
        return
        
    widths = [len(strip_ansi(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(strip_ansi(str(val))))
            
    if not alignments:
        alignments = ['L'] * len(headers)
        
    c_top_left, c_top_mid, c_top_right = "┌", "┬", "┐"
    c_mid_left, c_mid_mid, c_mid_right = "├", "┼", "┤"
    c_bot_left, c_bot_mid, c_bot_right = "└", "┴", "┘"
    c_horiz, c_vert = "─", "│"
    
    # Top border
    print(c_top_left + c_top_mid.join(c_horiz * (w + 2) for w in widths) + c_top_right)
    
    # Header row
    hdr_parts = []
    for i, h in enumerate(headers):
        w = widths[i]
        val = h.ljust(w) if alignments[i] == 'L' else h.rjust(w)
        if not no_color:
            val = f"{COLOR_BOLD}{COLOR_CYAN}{val}{COLOR_RESET}"
        hdr_parts.append(f" {val} ")
    print(c_vert + c_vert.join(hdr_parts) + c_vert)
    
    # Header separator
    print(c_mid_left + c_mid_mid.join(c_horiz * (w + 2) for w in widths) + c_mid_right)
    
    # Data rows
    for row in rows:
        row_parts = []
        for i, val in enumerate(row):
            w = widths[i]
            val_str = str(val)
            # Alignment needs to calculate padding using raw length without ANSI escape codes
            raw_len = len(strip_ansi(val_str))
            padding = " " * (w - raw_len)
            aligned = (val_str + padding) if alignments[i] == 'L' else (padding + val_str)
            row_parts.append(f" {aligned} ")
        print(c_vert + c_vert.join(row_parts) + c_vert)
        
    # Bottom border
    print(c_bot_left + c_bot_mid.join(c_horiz * (w + 2) for w in widths) + c_bot_right)

def generate_markdown(meminfo, tmpfs_mounts, processes, limit):
    total = meminfo.get('MemTotal', 0)
    free = meminfo.get('MemFree', 0)
    avail = meminfo.get('MemAvailable', 0)
    buffers = meminfo.get('Buffers', 0)
    cached = meminfo.get('Cached', 0)
    slab = meminfo.get('Slab', 0)
    page_tables = meminfo.get('PageTables', 0)
    
    used = total - avail
    cache_buf = buffers + cached
    
    md = []
    md.append(f"# RocketMode RAM & Process Report")
    md.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    md.append("## 1. System Memory Summary")
    md.append(f"- **Total Memory**: {format_size(total)}")
    md.append(f"- **Used Memory (Active + Kernel)**: {format_size(used)} ({used/total*100:.1f}%)")
    md.append(f"- **Available Memory**: {format_size(avail)} ({avail/total*100:.1f}%)")
    md.append(f"- **Free Memory**: {format_size(free)} ({free/total*100:.1f}%)")
    md.append(f"- **Cache & Buffers**: {format_size(cache_buf)} ({cache_buf/total*100:.1f}%)")
    md.append(f"- **Kernel Slab Cache**: {format_size(slab)} ({slab/total*100:.1f}%)")
    md.append(f"- **Page Tables**: {format_size(page_tables)} ({page_tables/total*100:.1f}%)\n")
    
    md.append("## 2. Temporary Filesystems (tmpfs in RAM)")
    if tmpfs_mounts:
        md.append("| Mount Point | Used | Total | % Used |")
        md.append("| :--- | :---: | :---: | :---: |")
        for t in tmpfs_mounts:
            md.append(f"| `{t['mount_point']}` | {format_size(t['used'])} | {format_size(t['total'])} | {t['percent_used']:.1f}% |")
    else:
        md.append("No active tmpfs mounts detected.\n")
    md.append("")
    
    md.append(f"## 3. Top {limit} Processes occupying RAM")
    md.append("| PID | User | Process Name | RSS (Resident) | VSZ (Virtual) | % RAM | Role in Rocket League / Heroic | What Breaks if Missing | Command Line |")
    md.append("| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |")
    
    sorted_procs = sorted(processes, key=lambda x: x['rss'], reverse=True)[:limit]
    for p in sorted_procs:
        p_pct = (p['rss'] / total * 100) if total > 0 else 0.0
        # Escape pipe symbols in cmdline to prevent breaking markdown tables
        safe_cmd = p['cmdline'].replace('|', '\\|')
        md.append(f"| {p['pid']} | {p['user']} | {p['name']} | {format_size(p['rss'])} | {format_size(p['vsz'])} | {p_pct:.2f}% | {p['rl_role']} | {p['what_breaks']} | `{safe_cmd[:100]}` |")
        
    return "\n".join(md)

def generate_html(meminfo, tmpfs_mounts, processes):
    total = meminfo.get('MemTotal', 0)
    free = meminfo.get('MemFree', 0)
    avail = meminfo.get('MemAvailable', 0)
    buffers = meminfo.get('Buffers', 0)
    cached = meminfo.get('Cached', 0)
    slab = meminfo.get('Slab', 0)
    page_tables = meminfo.get('PageTables', 0)
    
    used = total - avail
    cache_buf = buffers + cached
    
    used_pct = (used / total * 100) if total > 0 else 0
    avail_pct = (avail / total * 100) if total > 0 else 0
    free_pct = (free / total * 100) if total > 0 else 0
    cache_pct = (cache_buf / total * 100) if total > 0 else 0
    slab_pct = (slab / total * 100) if total > 0 else 0
    page_tables_pct = (page_tables / total * 100) if total > 0 else 0
    
    # Sort processes for table
    sorted_procs = sorted(processes, key=lambda x: x['rss'], reverse=True)
    
    proc_rows_html = []
    for p in sorted_procs:
        p_pct = (p['rss'] / total * 100) if total > 0 else 0.0
        # Skip 0 RSS processes to make HTML report focus on actual users
        if p['rss'] == 0:
            continue
        proc_rows_html.append(f"""
        <tr>
            <td><strong>{p['pid']}</strong></td>
            <td><span class="user-badge">{p['user']}</span></td>
            <td><span class="proc-name">{p['name']}</span></td>
            <td data-value="{p['rss']}">{format_size(p['rss'])}</td>
            <td data-value="{p['vsz']}">{format_size(p['vsz'])}</td>
            <td data-value="{p_pct}"><span class="percentage-pill">{p_pct:.2f}%</span></td>
            <td>{p['rl_role']}</td>
            <td>{p['what_breaks']}</td>
            <td class="cmd-cell"><code>{p['cmdline']}</code></td>
        </tr>
        """)
        
    tmpfs_rows_html = []
    for t in tmpfs_mounts:
        tmpfs_rows_html.append(f"""
        <tr>
            <td><code>{t['mount_point']}</code></td>
            <td>{format_size(t['used'])}</td>
            <td>{format_size(t['total'])}</td>
            <td>
                <div class="progress-container">
                    <div class="progress-bar-fill" style="width: {t['percent_used']}%;"></div>
                </div>
                <span class="percent-label">{t['percent_used']:.1f}%</span>
            </td>
        </tr>
        """)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RocketMode - System Memory Diagnostics</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #080c14;
            --card-bg: rgba(17, 24, 39, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-cyan: #06b6d4;
            --accent-blue: #3b82f6;
            --accent-purple: #a855f7;
            --accent-pink: #ec4899;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 10% 20%, rgba(59, 130, 246, 0.05) 0px, transparent 50%),
                radial-gradient(at 90% 80%, rgba(168, 85, 247, 0.05) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            line-height: 1.5;
            padding: 2rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            margin-bottom: 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .logo h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }}

        .badge {{
            background: rgba(6, 182, 212, 0.1);
            color: var(--accent-cyan);
            border: 1px solid rgba(6, 182, 212, 0.2);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .timestamp {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        /* Grid Layout */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        @media (max-width: 1024px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.75rem;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            transition: transform 0.2s, border-color 0.2s;
        }}

        .card:hover {{
            border-color: rgba(255, 255, 255, 0.15);
        }}

        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* Memory Distribution Bar */
        .memory-bar {{
            display: flex;
            height: 28px;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .bar-segment {{
            height: 100%;
            transition: width 0.3s ease;
            position: relative;
        }}

        .bar-used {{ background: linear-gradient(90deg, #3b82f6, #06b6d4); }}
        .bar-cache {{ background: #f59e0b; }}
        .bar-slab {{ background: #a855f7; }}
        .bar-pagetable {{ background: #ec4899; }}
        .bar-free {{ background: #10b981; }}

        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
        }}

        .legend-item {{
            display: flex;
            flex-direction: column;
            padding: 10px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }}

        .legend-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }}

        .legend-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}

        .dot-used {{ background-color: var(--accent-cyan); }}
        .dot-cache {{ background-color: var(--accent-yellow); }}
        .dot-slab {{ background-color: var(--accent-purple); }}
        .dot-pagetable {{ background-color: var(--accent-pink); }}
        .dot-free {{ background-color: var(--accent-green); }}

        .legend-value {{
            font-size: 1.1rem;
            font-weight: 600;
        }}

        .legend-sub {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        /* Table Styling */
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}

        th {{
            padding: 12px 16px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            user-select: none;
        }}

        th:hover {{
            color: var(--text-primary);
        }}

        td {{
            padding: 12px 16px;
            font-size: 0.9rem;
            border-bottom: 1px solid var(--border-color);
            vertical-align: middle;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .progress-container {{
            background: rgba(255, 255, 255, 0.05);
            height: 6px;
            border-radius: 3px;
            width: 80px;
            display: inline-block;
            margin-right: 8px;
            overflow: hidden;
        }}

        .progress-bar-fill {{
            background: var(--accent-cyan);
            height: 100%;
            border-radius: 3px;
        }}

        .percent-label {{
            font-size: 0.8rem;
            font-weight: 500;
        }}

        .user-badge {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: monospace;
        }}

        .proc-name {{
            font-weight: 500;
            color: #ffffff;
        }}

        .percentage-pill {{
            background: rgba(6, 182, 212, 0.1);
            color: var(--accent-cyan);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.8rem;
        }}

        .cmd-cell {{
            font-family: monospace;
            font-size: 0.8rem;
            color: var(--text-secondary);
            max-width: 400px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .cmd-cell code {{
            background: rgba(0, 0, 0, 0.2);
            padding: 2px 4px;
            border-radius: 4px;
        }}

        /* Search Panel */
        .table-controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
            gap: 1rem;
        }}

        .search-wrapper {{
            position: relative;
            flex-grow: 1;
            max-width: 400px;
        }}

        .search-input {{
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            padding: 10px 16px;
            border-radius: 8px;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}

        .search-input:focus {{
            border-color: var(--accent-cyan);
            box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2);
        }}

        .stats-count {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .process-section {{
            margin-top: 1.5rem;
        }}

        .table-container {{
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }}

        /* Scrollbar Styling */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.1);
        }}

        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <h1>RocketMode RAM Diagnostics</h1>
                <span class="badge">SYSTEM RAM REPORT</span>
            </div>
            <div class="timestamp">
                Last checked: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong>
            </div>
        </header>

        <div class="dashboard-grid">
            <!-- Summary card -->
            <div class="card">
                <div class="card-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent-cyan)"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>
                    Physical Memory Distribution
                </div>
                <div class="memory-bar">
                    <div class="bar-segment bar-used" style="width: {used_pct}%;" title="Used: {format_size(used)}"></div>
                    <div class="bar-segment bar-cache" style="width: {cache_pct}%;" title="Cache/Buffers: {format_size(cache_buf)}"></div>
                    <div class="bar-segment bar-slab" style="width: {slab_pct}%;" title="Kernel Slab: {format_size(slab)}"></div>
                    <div class="bar-segment bar-pagetable" style="width: {page_tables_pct}%;" title="Page Tables: {format_size(page_tables)}"></div>
                    <div class="bar-segment bar-free" style="width: {free_pct}%;" title="Free: {format_size(free)}"></div>
                </div>

                <div class="legend">
                    <div class="legend-item">
                        <span class="legend-label"><span class="legend-dot dot-used"></span>Used RAM</span>
                        <span class="legend-value">{format_size(used)}</span>
                        <span class="legend-sub">{used_pct:.1f}% of total</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-label"><span class="legend-dot dot-cache"></span>Cache & Buffers</span>
                        <span class="legend-value">{format_size(cache_buf)}</span>
                        <span class="legend-sub">{cache_pct:.1f}% of total</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-label"><span class="legend-dot dot-slab"></span>Kernel Slab</span>
                        <span class="legend-value">{format_size(slab)}</span>
                        <span class="legend-sub">{slab_pct:.1f}% of total</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-label"><span class="legend-dot dot-pagetable"></span>Page Tables</span>
                        <span class="legend-value">{format_size(page_tables)}</span>
                        <span class="legend-sub">{page_tables_pct:.1f}% of total</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-label"><span class="legend-dot dot-free"></span>Free RAM</span>
                        <span class="legend-value">{format_size(free)}</span>
                        <span class="legend-sub">{free_pct:.1f}% of total</span>
                    </div>
                </div>
            </div>

            <!-- Tmpfs RAM Card -->
            <div class="card">
                <div class="card-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent-yellow)"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    RAM Temporary Filesystems (tmpfs)
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Mount Point</th>
                            <th>Used</th>
                            <th>Total Size</th>
                            <th>Usage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(tmpfs_rows_html) if tmpfs_rows_html else "<tr><td colspan='4' style='text-align: center;'>No active tmpfs mounts detected.</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Processes Card -->
        <div class="card process-section">
            <div class="card-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent-purple)"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>
                Running Processes Memory Usage
            </div>
            
            <div class="table-controls">
                <div class="search-wrapper">
                    <input type="text" id="proc-search" class="search-input" placeholder="Search processes by PID, Name, User, or Command...">
                </div>
                <div class="stats-count">
                    Showing <strong id="visible-count">{len(sorted_procs)}</strong> processes consuming memory out of <strong>{len(processes)}</strong> total processes.
                </div>
            </div>

            <div class="table-container">
                <table id="proc-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)">PID</th>
                            <th onclick="sortTable(1)">User</th>
                            <th onclick="sortTable(2)">Process Name</th>
                            <th onclick="sortTable(3, true)">RSS (Resident)</th>
                            <th onclick="sortTable(4, true)">VSZ (Virtual)</th>
                            <th onclick="sortTable(5, true)">% RAM</th>
                            <th onclick="sortTable(6)">Role in Rocket League / Heroic</th>
                            <th onclick="sortTable(7)">What Breaks if Missing</th>
                            <th>Command Line</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(proc_rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Live search filtering
        const searchInput = document.getElementById('proc-search');
        const rows = document.querySelectorAll('#proc-table tbody tr');
        const countDisplay = document.getElementById('visible-count');

        searchInput.addEventListener('input', function() {{
            const query = this.value.toLowerCase().trim();
            let visibleCount = 0;
            
            rows.forEach(row => {{
                const cells = Array.from(row.getElementsByTagName('td'));
                const match = cells.some(cell => cell.textContent.toLowerCase().includes(query));
                if (match) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});
            countDisplay.textContent = visibleCount;
        }});

        // Sort table columns
        let sortDirections = {{}};
        function sortTable(columnIndex, isNumeric = false) {{
            const table = document.getElementById("proc-table");
            const tbody = table.querySelector("tbody");
            const rowsArray = Array.from(tbody.querySelectorAll("tr"));
            
            // Toggle direction
            const currentDir = sortDirections[columnIndex] || 'desc';
            const nextDir = currentDir === 'asc' ? 'desc' : 'asc';
            sortDirections[columnIndex] = nextDir;
            
            rowsArray.sort((a, b) => {{
                let valA = a.getElementsByTagName("td")[columnIndex];
                let valB = b.getElementsByTagName("td")[columnIndex];
                
                let textA = valA.getAttribute("data-value") || valA.textContent.trim();
                let textB = valB.getAttribute("data-value") || valB.textContent.trim();
                
                if (isNumeric) {{
                    return nextDir === 'asc' 
                        ? parseFloat(textA) - parseFloat(textB) 
                        : parseFloat(textB) - parseFloat(textA);
                }} else {{
                    return nextDir === 'asc' 
                        ? textA.localeCompare(textB) 
                        : textB.localeCompare(textA);
                }}
            }});
            
            // Re-append sorted rows
            rowsArray.forEach(row => tbody.appendChild(row));
            
            // Reset indicators (visually highlight the sorted column if desired)
            const headers = table.querySelectorAll("th");
            headers.forEach((th, idx) => {{
                if (idx === columnIndex) {{
                    th.innerHTML = th.textContent.replace(/[▲▼]/g, '') + (nextDir === 'asc' ? ' ▲' : ' ▼');
                }} else {{
                    th.innerHTML = th.textContent.replace(/[▲▼]/g, '');
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    return html_template

def main():
    parser = argparse.ArgumentParser(description="RocketMode RAM and Process Inspector")
    parser.add_argument("-n", "--limit", type=int, default=20, help="Number of processes to list in terminal (default: 20)")
    parser.add_argument("-s", "--sort", choices=["rss", "vsz", "name", "pid"], default="rss", help="Column to sort processes by (default: rss)")
    parser.add_argument("-o", "--html", type=str, help="Export interactive HTML report to this file path")
    parser.add_argument("-m", "--markdown", type=str, help="Export markdown report to this file path")
    parser.add_argument("-j", "--json", type=str, help="Export raw diagnostic data in JSON format to this file path")
    parser.add_argument("--no-color", action="store_true", help="Disable terminal colors")
    args = parser.parse_args()

    # Collect data
    meminfo = get_meminfo()
    tmpfs = get_tmpfs_mounts()
    processes = get_processes()

    if not meminfo:
        print("Fatal error: Could not retrieve system memory statistics.")
        sys.exit(1)

    total_ram = meminfo.get('MemTotal', 0)
    free_ram = meminfo.get('MemFree', 0)
    avail_ram = meminfo.get('MemAvailable', total_ram - free_ram)
    used_ram = total_ram - avail_ram
    buffers = meminfo.get('Buffers', 0)
    cached = meminfo.get('Cached', 0)
    slab = meminfo.get('Slab', 0)
    page_tables = meminfo.get('PageTables', 0)

    # 1. Output terminal summary
    if args.no_color:
        no_color_flag = True
    else:
        # Disable colors if stdout is redirected or user chose --no-color
        no_color_flag = not sys.stdout.isatty() or args.no_color

    print(f"\n{COLOR_BOLD if not no_color_flag else ''}🚀 ROCKETMODE MEMORY DIAGNOSTICS{COLOR_RESET if not no_color_flag else ''}")
    print(f"{COLOR_GREY if not no_color_flag else ''}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{COLOR_RESET if not no_color_flag else ''}")
    print("=" * 60)
    
    # Visual memory bar
    used_pct = (used_ram / total_ram * 100) if total_ram > 0 else 0
    print(f"RAM Usage: {make_bar(used_pct, 40, COLOR_GREEN, no_color_flag)}")
    print(f"  • {COLOR_BOLD if not no_color_flag else ''}Total RAM:{COLOR_RESET if not no_color_flag else ''}  {format_size(total_ram)}")
    print(f"  • {COLOR_BOLD if not no_color_flag else ''}Used (Active):{COLOR_RESET if not no_color_flag else ''} {format_size(used_ram)} ({used_pct:.1f}%)")
    print(f"  • {COLOR_BOLD if not no_color_flag else ''}Available:{COLOR_RESET if not no_color_flag else ''} {format_size(avail_ram)} ({avail_ram/total_ram*100:.1f}%)")
    print(f"  • {COLOR_BOLD if not no_color_flag else ''}Free:{COLOR_RESET if not no_color_flag else ''}      {format_size(free_ram)} ({free_ram/total_ram*100:.1f}%)")
    
    # Buffers & Cache Details
    cache_buf = buffers + cached
    print(f"  • {COLOR_BOLD if not no_color_flag else ''}Cache/Buffers:{COLOR_RESET if not no_color_flag else ''} {format_size(cache_buf)} ({cache_buf/total_ram*100:.1f}%)")
    
    # Kernel details
    print(f"  • {COLOR_BOLD if not no_color_flag else ''}Kernel Slab:{COLOR_RESET if not no_color_flag else ''}  {format_size(slab)} ({slab/total_ram*100:.1f}%)")
    print(f"  • {COLOR_BOLD if not no_color_flag else ''}Page Tables:{COLOR_RESET if not no_color_flag else ''}  {format_size(page_tables)} ({page_tables/total_ram*100:.1f}%)")

    # 2. Tmpfs File systems
    print(f"\n{COLOR_BOLD if not no_color_flag else ''}📁 Temporary Filesystems in RAM (tmpfs){COLOR_RESET if not no_color_flag else ''}")
    tmpfs_headers = ["Mount Point", "Used Space", "Total Size", "Usage %"]
    tmpfs_rows = []
    for t in tmpfs:
        pct_str = f"{t['percent_used']:.1f}%"
        if not no_color_flag:
            color = COLOR_GREEN if t['percent_used'] < 50 else (COLOR_YELLOW if t['percent_used'] < 85 else COLOR_RED)
            pct_str = f"{color}{pct_str}{COLOR_RESET}"
        tmpfs_rows.append([
            t['mount_point'],
            format_size(t['used']),
            format_size(t['total']),
            pct_str
        ])
    print_table(tmpfs_headers, tmpfs_rows, alignments=['L', 'R', 'R', 'R'], no_color=no_color_flag)

    # 3. Running Processes Table
    print(f"\n{COLOR_BOLD if not no_color_flag else ''}Running Processes Sorted by Memory Usage{COLOR_RESET if not no_color_flag else ''}")
    
    # Sort processes
    proc_sort_key = args.sort
    if proc_sort_key == "rss":
        sorted_procs = sorted(processes, key=lambda x: x['rss'], reverse=True)
    elif proc_sort_key == "vsz":
        sorted_procs = sorted(processes, key=lambda x: x['vsz'], reverse=True)
    elif proc_sort_key == "name":
        sorted_procs = sorted(processes, key=lambda x: x['name'].lower())
    elif proc_sort_key == "pid":
        sorted_procs = sorted(processes, key=lambda x: x['pid'])
    else:
        sorted_procs = sorted(processes, key=lambda x: x['rss'], reverse=True)
        
    proc_headers = ["PID", "User", "Process Name", "RSS (Resident)", "% RAM", "RL Role", "Impact if Missing", "Command Line"]
    proc_rows = []
    for p in sorted_procs[:args.limit]:
        p_pct = (p['rss'] / total_ram * 100) if total_ram > 0 else 0.0
        
        # Colorize high memory values
        rss_str = format_size(p['rss'])
        pct_str = f"{p_pct:.2f}%"
        if not no_color_flag:
            if p_pct > 5.0:  # Occupies > 5% of RAM
                pct_str = f"{COLOR_RED}{COLOR_BOLD}{pct_str}{COLOR_RESET}"
                rss_str = f"{COLOR_RED}{COLOR_BOLD}{rss_str}{COLOR_RESET}"
            elif p_pct > 1.0: # Occupies > 1% of RAM
                pct_str = f"{COLOR_YELLOW}{pct_str}{COLOR_RESET}"
                rss_str = f"{COLOR_YELLOW}{rss_str}{COLOR_RESET}"
                
        # Trim command line to fit screen
        cmd = p['cmdline']
        if len(cmd) > 35:
            cmd = cmd[:32] + "..."
            
        role_str = p['rl_role']
        if len(role_str) > 35:
            role_str = role_str[:32] + "..."
            
        break_str = p['what_breaks']
        if len(break_str) > 35:
            break_str = break_str[:32] + "..."
            
        proc_rows.append([
            str(p['pid']),
            p['user'],
            p['name'],
            rss_str,
            pct_str,
            role_str,
            break_str,
            cmd
        ])
        
    print_table(proc_headers, proc_rows, alignments=['R', 'L', 'L', 'R', 'R', 'L', 'L', 'L'], no_color=no_color_flag)
    print(f"Showing top {min(len(sorted_procs), args.limit)} processes. Total processes running: {len(processes)}.")

    # 4. Exports
    if args.json:
        try:
            with open(args.json, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'memory_summary': {
                        'total': total_ram,
                        'free': free_ram,
                        'available': avail_ram,
                        'used': used_ram,
                        'buffers': buffers,
                        'cached': cached,
                        'slab': slab,
                        'page_tables': page_tables
                    },
                    'tmpfs_mounts': tmpfs,
                    'processes': processes
                }, f, indent=4)
            print(f"\n✅ Diagnostic JSON data successfully saved to: {args.json}")
        except IOError as e:
            print(f"❌ Failed to write JSON output: {e}", file=sys.stderr)

    if args.markdown:
        try:
            markdown_content = generate_markdown(meminfo, tmpfs, processes, args.limit)
            with open(args.markdown, 'w') as f:
                f.write(markdown_content)
            print(f"✅ Markdown report successfully written to: {args.markdown}")
        except IOError as e:
            print(f"❌ Failed to write Markdown output: {e}", file=sys.stderr)

    if args.html:
        try:
            html_content = generate_html(meminfo, tmpfs, processes)
            with open(args.html, 'w') as f:
                f.write(html_content)
            print(f"✅ Interactive HTML dashboard report successfully written to: {args.html}")
        except IOError as e:
            print(f"❌ Failed to write HTML output: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
