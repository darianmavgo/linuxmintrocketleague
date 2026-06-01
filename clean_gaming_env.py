#!/usr/bin/env python3
import os
import sys
import pwd
import getpass
from datetime import datetime

# Whitelist definition for process names to keep alive
WHITELIST_NAMES = {
    "systemd", "sd-pam", "dbus-daemon", "dconf-service",
    "xfce4-session", "xfwm4", "xfsettingsd", "xfce4-panel", "xfdesktop", "xfconfd",
    "pipewire", "pipewire-pulse", "wireplumber",
    "flatpak-session-helper", "pkcs11-flatpak", "xdg-dbus-proxy", "flatpak-portal", "bwrap", "zypak-helper",
    "xdg-desktop-portal", "xdg-permission-store", "xdg-document-portal", "xdg-desktop-portal-gtk", "xdg-desktop-portal-xapp", "fusermount3",
    "nvidia-persistenced", "nvidia-prime", "nvidia-smi",
    "gamemoded", "gamemoderun",
    "heroic", "heroic-run", "legendary",
    "wineserver", "services.exe", "winedevice.exe", "plugplay.exe", "rpcss.exe", "explorer.exe", "svchost.exe",
    "rocketleague.exe", "launcher.exe", "gamescope"
}

# Whitelist patterns for process command lines to keep alive
WHITELIST_PATTERNS = [
    "wine", "proton", "umu", "pressure-vessel", "pv-adverb",
    "rocketleague", "legendary", "heroic", "gamemode", ".exe",
    "rocket_booster", "game_logger", "gamescope"
]

# Only these processes are allowed to pass their whitelisted status down to descendants
PROPAGATING_KEYWORDS = [
    "heroic", "flatpak", "wineserver", "gamemoded", 
    "pressure-vessel", "umu-shim", "bwrap", "gamescope"
]

def get_ancestor_pids():
    ancestors = set()
    pid = os.getpid()
    while pid > 1:
        ancestors.add(pid)
        try:
            with open(f"/proc/{pid}/status", "r") as f:
                ppid = None
                for line in f:
                    if line.startswith("PPid:"):
                        ppid = int(line.split()[1])
                        break
                if ppid is None or ppid <= 1:
                    break
                pid = ppid
        except Exception:
            break
    return ancestors

def get_process_ancestors(pid):
    ancestors = []
    curr = pid
    while curr > 1:
        try:
            with open(f"/proc/{curr}/status", "r") as f:
                ppid = None
                for line in f:
                    if line.startswith("PPid:"):
                        ppid = int(line.split()[1])
                        break
                if ppid is None or ppid <= 1 or ppid in ancestors:
                    break
                ancestors.append(ppid)
                curr = ppid
        except Exception:
            break
    return ancestors

def find_user_ssh_processes(target_user):
    ssh_processes = []
    for pid_dir in os.listdir('/proc'):
        if pid_dir.isdigit():
            pid = int(pid_dir)
            try:
                with open(f"/proc/{pid_dir}/status", "r") as f:
                    uid = None
                    name = None
                    for line in f:
                        if line.startswith("Name:"):
                            name = line.split(None, 1)[1].strip()
                        elif line.startswith("Uid:"):
                            uid = int(line.split()[1])
                            break
                if uid is None:
                    continue
                try:
                    username = pwd.getpwuid(uid).pw_name
                except KeyError:
                    username = str(uid)
                
                if username != target_user:
                    continue
                
                with open(f"/proc/{pid_dir}/cmdline", "rb") as f:
                    cmdline = f.read().replace(b'\x00', b' ').decode('utf-8', errors='ignore').strip()
                
                if "sshd" in name.lower() or "sshd:" in cmdline.lower():
                    ssh_processes.append({'pid': pid, 'name': name, 'cmdline': cmdline})
            except Exception:
                continue
    return ssh_processes

def is_whitelisted(name, cmdline):
    name_lower = name.lower()
    cmdline_lower = cmdline.lower()
    
    # Check name matches or truncated prefix
    for wl_name in WHITELIST_NAMES:
        if wl_name in name_lower or wl_name in cmdline_lower:
            return True
            
    for pattern in WHITELIST_PATTERNS:
        if pattern in cmdline_lower or pattern in name_lower:
            return True
            
    if "panel-" in name_lower and "wrapper-2.0" in cmdline_lower:
        return True
        
    return False

def is_propagating(name, cmdline):
    name_lower = name.lower()
    cmdline_lower = cmdline.lower()
    for prop in PROPAGATING_KEYWORDS:
        if prop in name_lower or prop in cmdline_lower:
            return True
    return False

def stop_systemd_services(dry_run=False):
    services = [
        "gnome-keyring-daemon.service",
        "gvfs-daemon.service",
        "gvfs-mtp-volume-monitor.service",
        "gvfs-udisks2-volume-monitor.service",
        "xfce4-notifyd.service",
        "at-spi-dbus-bus.service",
        "gpg-agent.service"
    ]
    import subprocess
    if dry_run:
        print("\n[DRY-RUN] Would stop systemd user services:")
        for s in services:
            print(f"  systemctl --user stop {s}")
    else:
        print("\nStopping background systemd user services...")
        for s in services:
            try:
                subprocess.run(["systemctl", "--user", "stop", s], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  Stopped: {s}")
            except Exception as e:
                print(f"  Failed to stop {s}: {e}")

def main():
    dry_run = "--dry-run" in sys.argv
    target_user = os.environ.get("SUDO_USER") or os.environ.get("USER") or getpass.getuser()
    try:
        target_uid = pwd.getpwnam(target_user).pw_uid
    except KeyError:
        print(f"Error: user {target_user} not found.")
        sys.exit(1)
        
    log_file_path = "/home/darian/Documents/RocketMode/killed_processes.log"
    
    # Stop background systemd user services first to prevent auto-restart loops
    stop_systemd_services(dry_run)
    
    ancestor_pids = get_ancestor_pids()
    ssh_processes = find_user_ssh_processes(target_user)
    
    current_ssh_pid = None
    for p in ssh_processes:
        if p['pid'] in ancestor_pids:
            current_ssh_pid = p['pid']
            break
            
    ssh_to_keep = None
    if current_ssh_pid:
        ssh_to_keep = current_ssh_pid
    elif ssh_processes:
        ssh_processes.sort(key=lambda x: x['pid'])
        ssh_to_keep = ssh_processes[0]['pid']
        
    ssh_pids_to_kill = {p['pid'] for p in ssh_processes if p['pid'] != ssh_to_keep}
    
    # Gather all processes and cache status info for parentage checks
    all_user_processes = {}
    processes_to_check = []
    
    for pid_dir in os.listdir('/proc'):
        if pid_dir.isdigit():
            pid = int(pid_dir)
            try:
                with open(f"/proc/{pid_dir}/status", "r") as f:
                    uid = None
                    name = None
                    for line in f:
                        if line.startswith("Name:"):
                            name = line.split(None, 1)[1].strip()
                        elif line.startswith("Uid:"):
                            uid = int(line.split()[1])
                            break
                if uid != target_uid:
                    continue
                    
                with open(f"/proc/{pid_dir}/cmdline", "rb") as f:
                    cmdline = f.read().replace(b'\x00', b' ').decode('utf-8', errors='ignore').strip()
                
                all_user_processes[pid] = (name or 'unknown', cmdline)
                processes_to_check.append((pid, name or 'unknown', cmdline))
            except Exception:
                continue
                
    # Track actions
    to_kill = []
    to_keep = []
    
    for pid, name, cmdline in processes_to_check:
        if pid in ancestor_pids:
            to_keep.append((pid, "Ancestor process (protected)"))
            continue
        if pid == ssh_to_keep:
            to_keep.append((pid, "Active SSH session (protected)"))
            continue
            
        # Check duplicate SSH
        if pid in ssh_pids_to_kill:
            to_kill.append((pid, name, cmdline, "Duplicate SSH Session"))
            continue
            
        # Check direct whitelist
        if is_whitelisted(name, cmdline):
            to_keep.append((pid, f"Whitelisted (Direct): {name}"))
            continue
            
        # Check parentage/ancestor whitelist inheritance (only from propagating processes)
        inherited_whitelist = False
        ancestors = get_process_ancestors(pid)
        for p_ancestor in ancestors:
            if p_ancestor in all_user_processes:
                anc_name, anc_cmdline = all_user_processes[p_ancestor]
                if is_whitelisted(anc_name, anc_cmdline) and is_propagating(anc_name, anc_cmdline):
                    to_keep.append((pid, f"Whitelisted (Inherited from '{anc_name}' PID {p_ancestor}): {name}"))
                    inherited_whitelist = True
                    break
        if inherited_whitelist:
            continue
            
        to_kill.append((pid, name, cmdline, "Not whitelisted"))
                
    # Logging and output
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode_str = "DRY-RUN" if dry_run else "ACTIVE"
    log_lines = [f"\n--- Gaming Environment Cleanup: {timestamp} (Mode: {mode_str}) ---"]
    
    print(f"\n=== RocketMode Environment Cleanup ({mode_str} Mode) ===")
    print(f"Targeting User: {target_user} (UID: {target_uid})")
    print(f"Protecting PIDs: {sorted(list(ancestor_pids))}")
    if ssh_to_keep:
        print(f"Protecting active SSH Session PID: {ssh_to_keep}")
        
    print("\nProcesses to keep alive:")
    for pid, reason in sorted(to_keep, key=lambda x: x[0]):
        print(f"  [KEEP] PID {pid:5d}: {reason}")
        
    print("\nProcesses to terminate:")
    for pid, name, cmdline, reason in sorted(to_kill, key=lambda x: x[0]):
        print(f"  [KILL] PID {pid:5d} ({name}): {reason} - Command: {cmdline[:80]}")
        log_lines.append(f"{timestamp} - PID {pid} ({name}) - {reason} - Command: {cmdline}")
        
    if not dry_run:
        # Actually kill processes
        killed_count = 0
        for pid, name, cmdline, reason in to_kill:
            try:
                os.kill(pid, 9)
                killed_count += 1
            except Exception as e:
                log_lines.append(f"{timestamp} - FAILED to kill PID {pid} ({name}): {str(e)}")
        log_lines.append(f"{timestamp} - Cleanup finished. Successfully killed {killed_count} processes.")
        print(f"\nCleanup finished. Successfully killed {killed_count} processes.")
    else:
        log_lines.append(f"{timestamp} - Dry-run completed. No processes were killed.")
        print("\nDry-run completed. No processes were killed.")
        
    # Write to log file
    try:
        with open(log_file_path, "a") as log_f:
            for line in log_lines:
                log_f.write(line + "\n")
    except Exception as e:
        print(f"Error writing to log file: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    main()
