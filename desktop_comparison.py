#!/usr/bin/env python3
import os
import pwd
import sys

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

def main():
    cinnamon_patterns = [
        'cinnamon', 'nemo', 'csd-', 'muffin', 'polkit-cinnamon', 
        'evolution-alarm', 'evolution-source-registry', 
        'evolution-calendar-factory', 'evolution-addressbook-factory'
    ]
    
    matched_processes = []
    
    for pid_dir in os.listdir('/proc'):
        if pid_dir.isdigit():
            pid = int(pid_dir)
            try:
                status_path = os.path.join('/proc', pid_dir, 'status')
                cmdline_path = os.path.join('/proc', pid_dir, 'cmdline')
                
                if not os.path.exists(status_path):
                    continue
                    
                name = None
                rss = 0
                cmdline = ""
                
                with open(status_path, 'r') as f:
                    for line in f:
                        if line.startswith('Name:'):
                            name = line.split(None, 1)[1].strip()
                        elif line.startswith('VmRSS:'):
                            rss = int(line.split()[1]) * 1024  # kB to B
                            
                if os.path.exists(cmdline_path):
                    with open(cmdline_path, 'rb') as f:
                        cmd_bytes = f.read()
                        if cmd_bytes:
                            cmdline = cmd_bytes.replace(b'\x00', b' ').decode('utf-8', errors='ignore').strip()
                
                if not name:
                    continue
                
                name_lower = name.lower()
                cmd_lower = cmdline.lower()
                
                is_cinnamon = any(pat in name_lower or pat in cmd_lower for pat in cinnamon_patterns)
                
                if is_cinnamon:
                    matched_processes.append({
                        'pid': pid,
                        'name': name,
                        'rss': rss,
                        'cmdline': cmdline or name
                    })
                    
            except (IOError, OSError, ValueError):
                continue
                
    # Sort by memory descending
    matched_processes.sort(key=lambda x: x['rss'], reverse=True)
    
    total_cinnamon_rss = sum(p['rss'] for p in matched_processes)
    
    # XFCE Estimates based on standard clean desktop environments
    xfce_components = [
        {"name": "xfce4-session", "est_rss": 20 * 1024 * 1024, "desc": "Session Manager"},
        {"name": "xfwm4", "est_rss": 25 * 1024 * 1024, "desc": "Window Manager"},
        {"name": "xfce4-panel", "est_rss": 35 * 1024 * 1024, "desc": "Desktop Panel"},
        {"name": "xfdesktop", "est_rss": 30 * 1024 * 1024, "desc": "Desktop Manager (Wallpaper & Icons)"},
        {"name": "xfsettingsd", "est_rss": 20 * 1024 * 1024, "desc": "Settings Daemon"},
        {"name": "xfconfd", "est_rss": 8 * 1024 * 1024, "desc": "Configuration Daemon"},
        {"name": "thunar", "est_rss": 25 * 1024 * 1024, "desc": "XFCE File Manager (Idle)"},
    ]
    
    total_xfce_est = sum(c['est_rss'] for c in xfce_components)
    freed_ram = total_cinnamon_rss - total_xfce_est
    
    # Build report
    report = []
    report.append("# RocketMode Desktop Environment Memory Assessment")
    report.append("Comparing active **Cinnamon** session components to standard **XFCE** alternatives.\n")
    
    report.append("## 1. Currently Active Cinnamon & Evolution Helper Processes")
    report.append("| PID | Process Name | RAM Usage (RSS) | Role / Command |")
    report.append("| :--- | :--- | :---: | :--- |")
    for p in matched_processes:
        report.append(f"| {p['pid']} | `{p['name']}` | {format_size(p['rss'])} | `{p['cmdline'][:60]}` |")
    
    report.append(f"\n**Total Active Cinnamon Memory Footprint**: **{format_size(total_cinnamon_rss)}**\n")
    
    report.append("## 2. Estimated XFCE Memory Footprint (Baseline)")
    report.append("| Component | Estimated RSS | Description |")
    report.append("| :--- | :---: | :--- |")
    for c in xfce_components:
        report.append(f"| `{c['name']}` | {format_size(c['est_rss'])} | {c['desc']} |")
    
    report.append(f"\n**Estimated Total XFCE Memory Footprint**: **{format_size(total_xfce_est)}**\n")
    
    report.append("## 3. Memory Savings Analysis")
    report.append(f"- **Cinnamon Memory Footprint**: {format_size(total_cinnamon_rss)}")
    report.append(f"- **XFCE Memory Footprint (Est.)**: {format_size(total_xfce_est)}")
    report.append(f"- **Potential RAM Freed**: **{format_size(freed_ram)}**")
    
    savings_pct = (freed_ram / total_cinnamon_rss * 100) if total_cinnamon_rss > 0 else 0
    report.append(f"- **Desktop Environment Footprint Reduction**: **{savings_pct:.1f}%**\n")
    
    report.append("### Why XFCE saves memory compared to Cinnamon:")
    report.append("1. **Window Manager & Compositing**: XFCE's `xfwm4` uses lightweight CPU-based or simple OpenGL compositing, whereas Cinnamon's built-in window manager (`muffin`, based on Clutter/Mutter) maintains large high-resolution textures for windows, workspaces, and system effects.")
    report.append("2. **Desktop Shell & Javascript**: Cinnamon is built with Javascript bindings (`cjs` / Cinnamon Javascript) running on top of GObject, which adds garbage collector overhead and larger runtime memory tables. XFCE is written entirely in pure C (`GTK3`), utilizing zero runtime interpreter wrappers.")
    report.append("3. **Reduced Service Overhead**: Cinnamon boots up multiple background setting daemons (`csd-background`, `csd-keyboard`, etc.) and GNOME/Evolution calendar synchronizers. XFCE consolidates system configuration into a single lightweight daemon (`xfsettingsd`).")
    
    report_text = "\n".join(report)
    
    # Save report to file
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'desktop_assessment.md')
    try:
        with open(report_path, 'w') as f:
            f.write(report_text)
        print(f"✅ Desktop memory assessment report successfully saved to: {report_path}\n")
    except IOError as e:
        print(f"Error saving report: {e}", file=sys.stderr)
        
    # Print summary to stdout
    print(report_text)

if __name__ == "__main__":
    main()
