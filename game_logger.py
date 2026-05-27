#!/usr/bin/env python3
import os
import sys
import time
import signal
import json
import re
import subprocess
from datetime import datetime

# Paths
BASE_DIR = "/home/darian/Documents/RocketMode"
PID_FILE = os.path.join(BASE_DIR, ".game_logger.pid")
DATA_FILE = os.path.join(BASE_DIR, ".last_session.json")
LOG_FILE = os.path.join(BASE_DIR, "game_session.log")
KILLED_LOG = os.path.join(BASE_DIR, "killed_processes.log")

# Globals for daemon
running = True
session_data = {
    "start_time": "",
    "end_time": "",
    "zram_start": {},
    "zram_end": {},
    "zram_peaks": {},    # pid -> {name, cmdline, peak_kb}
    "gpu_processes": {},   # pid -> {name, type, peak_memory_str, peak_memory_mib}
    "game_processes": {},  # pid -> {name, cmdline, first_seen}
    "killed_processes": []
}

def sigterm_handler(signum, frame):
    global running
    running = False

def get_zram_usage():
    zram_usage = {}
    for pid_name in os.listdir('/proc'):
        if not pid_name.isdigit():
            continue
        pid = int(pid_name)
        try:
            with open(f"/proc/{pid}/status", "r") as f:
                swap_kb = 0
                name = ""
                for line in f:
                    if line.startswith("Name:"):
                        name = line.split(None, 1)[1].strip()
                    elif line.startswith("VmSwap:"):
                        swap_kb = int(line.split()[1])
                        break
                if swap_kb > 0:
                    try:
                        with open(f"/proc/{pid}/cmdline", "r") as cf:
                            cmdline = cf.read().replace('\x00', ' ').strip()
                    except:
                        cmdline = name
                    zram_usage[pid] = {
                        "name": name or "unknown",
                        "cmdline": cmdline or name,
                        "swap_kb": swap_kb
                    }
        except:
            continue
    return zram_usage

def get_gpu_processes():
    gpu_procs = []
    try:
        output = subprocess.check_output(["nvidia-smi"], stderr=subprocess.DEVNULL).decode("utf-8")
        in_process_section = False
        for line in output.split('\n'):
            if "Processes:" in line:
                in_process_section = True
                continue
            if in_process_section:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    inner = parts[1]
                    cols = inner.split()
                    if len(cols) >= 6 and cols[0].isdigit() and cols[3].isdigit():
                        gpu_procs.append({
                            "pid": int(cols[3]),
                            "name": " ".join(cols[5:-1]),
                            "type": cols[4],
                            "memory": cols[-1]
                        })
    except Exception:
        pass
    return gpu_procs

def get_killed_processes_since():
    if not os.path.exists(KILLED_LOG):
        return []
    killed = []
    try:
        with open(KILLED_LOG, "r") as f:
            lines = f.readlines()
        
        last_block_idx = -1
        for i in range(len(lines)-1, -1, -1):
            if "Gaming Environment Cleanup:" in lines[i]:
                last_block_idx = i
                break
        
        if last_block_idx != -1:
            for line in lines[last_block_idx+1:]:
                if " - PID " in line and " - Command: " in line:
                    match = re.search(r'PID (\d+) \((.*?)\) - (.*?) - Command: (.*)', line)
                    if match:
                        killed.append({
                            "pid": int(match.group(1)),
                            "name": match.group(2),
                            "reason": match.group(3),
                            "cmdline": match.group(4).strip()
                        })
                elif "Cleanup finished" in line or "Dry-run completed" in line:
                    # Reached the end of this block
                    break
    except Exception:
        pass
    return killed

def update_tracked_processes(game_roots, seen_game_processes):
    ppid_map = {}
    proc_info = {}
    
    for pid_name in os.listdir('/proc'):
        if not pid_name.isdigit():
            continue
        pid = int(pid_name)
        try:
            with open(f"/proc/{pid}/status", "r") as f:
                ppid = None
                name = ""
                for line in f:
                    if line.startswith("Name:"):
                        name = line.split(None, 1)[1].strip()
                    elif line.startswith("PPid:"):
                        ppid = int(line.split()[1])
                        break
            
            with open(f"/proc/{pid}/cmdline", "r") as cf:
                cmdline = cf.read().replace('\x00', ' ').strip()
            if not cmdline:
                cmdline = name
                
            proc_info[pid] = {"name": name, "cmdline": cmdline}
            if ppid is not None:
                ppid_map[pid] = ppid
        except:
            continue
            
    # Identify any new game roots based on signature keywords
    for pid, info in proc_info.items():
        cmd_lower = info["cmdline"].lower()
        name_lower = info["name"].lower()
        if "heroicgameslauncher" in cmd_lower or "heroic" in name_lower or "heroic-run" in name_lower or \
           "rocketleague" in cmd_lower or "rocketleague" in name_lower or \
           "wineserver" in name_lower or "wineserver" in cmd_lower:
            if pid not in game_roots:
                game_roots.add(pid)
                
    # Propagate parentage to find all children recursively
    for pid, info in proc_info.items():
        if pid in seen_game_processes:
            continue
            
        curr = pid
        is_descendant = False
        visited = set()
        while curr in ppid_map:
            if curr in visited:
                break
            visited.add(curr)
            parent = ppid_map[curr]
            if parent in game_roots:
                is_descendant = True
                break
            curr = parent
            
        if is_descendant:
            game_roots.add(pid)
            seen_game_processes[pid] = {
                "name": info["name"],
                "cmdline": info["cmdline"],
                "first_seen": datetime.now().strftime("%H:%M:%S")
            }

def update_zram_peaks(zram_peaks):
    current_zram = get_zram_usage()
    for pid, info in current_zram.items():
        if pid not in zram_peaks:
            zram_peaks[pid] = {
                "name": info["name"],
                "cmdline": info["cmdline"],
                "peak_kb": info["swap_kb"]
            }
        else:
            if info["swap_kb"] > zram_peaks[pid]["peak_kb"]:
                zram_peaks[pid]["peak_kb"] = info["swap_kb"]

def update_gpu_processes(gpu_processes):
    current_gpu = get_gpu_processes()
    for proc in current_gpu:
        pid = proc["pid"]
        mem_str = proc["memory"]
        mem_val = 0
        if "MiB" in mem_str:
            try:
                mem_val = int(mem_str.replace("MiB", "").strip())
            except:
                pass
                
        if pid not in gpu_processes:
            gpu_processes[pid] = {
                "name": proc["name"],
                "type": proc["type"],
                "peak_memory_str": mem_str,
                "peak_memory_mib": mem_val,
                "first_seen": datetime.now().strftime("%H:%M:%S")
            }
        else:
            if mem_val > gpu_processes[pid]["peak_memory_mib"]:
                gpu_processes[pid]["peak_memory_mib"] = mem_val
                gpu_processes[pid]["peak_memory_str"] = mem_str

def write_to_history_log():
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"\n========================================\n")
            f.write(f"🎮 ROCKET LEAGUE SESSION TELEMETRY\n")
            f.write(f"Start Time: {session_data['start_time']}\n")
            f.write(f"End Time:   {session_data['end_time']}\n")
            f.write(f"========================================\n\n")
            
            f.write(f"1. KILLED PROCESSES DURING CLEANUP ({len(session_data['killed_processes'])})\n")
            for proc in session_data['killed_processes']:
                f.write(f"   - PID {proc['pid']}: {proc['name']} (Reason: {proc['reason']}) -> {proc['cmdline'][:100]}\n")
            if not session_data['killed_processes']:
                f.write(f"   None\n")
                
            f.write(f"\n2. PROCESSES THAT USED ZRAM (PEAK SWAP)\n")
            zram_sorted = sorted(session_data['zram_peaks'].items(), key=lambda x: x[1]['peak_kb'], reverse=True)
            for pid, info in zram_sorted:
                f.write(f"   - PID {pid}: {info['name']} (Peak: {info['peak_kb']} kB) -> {info['cmdline'][:100]}\n")
            if not zram_sorted:
                f.write(f"   None\n")
                
            f.write(f"\n3. PROCESSES LAUNCHED BY HEROIC / ROCKET LEAGUE ({len(session_data['game_processes'])})\n")
            for pid, info in sorted(session_data['game_processes'].items(), key=lambda x: x[1]['first_seen']):
                f.write(f"   - PID {pid}: {info['name']} (First seen: {info['first_seen']}) -> {info['cmdline'][:100]}\n")
            if not session_data['game_processes']:
                f.write(f"   None\n")
                
            f.write(f"\n4. PROCESSES UTILIZING NVIDIA GPU\n")
            gpu_sorted = sorted(session_data['gpu_processes'].items(), key=lambda x: x[1].get('peak_memory_mib', 0), reverse=True)
            for pid, info in gpu_sorted:
                f.write(f"   - PID {pid}: {info['name']} (Type: {info['type']}, Peak GPU Memory: {info['peak_memory_str']})\n")
            if not gpu_sorted:
                f.write(f"   None\n")
            f.write(f"\n\n")
    except Exception as e:
        sys.stderr.write(f"Error writing to history log: {e}\n")

def run_daemon():
    global running
    # Setup signals
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)
    
    start_dt = datetime.now()
    session_data["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Capture initial ZRAM state
    session_data["zram_start"] = {str(k): v for k, v in get_zram_usage().items()}
    
    game_roots = set()
    seen_game_processes = {}
    zram_peaks = {}
    gpu_processes = {}
    
    # Initial scan
    update_tracked_processes(game_roots, seen_game_processes)
    update_zram_peaks(zram_peaks)
    update_gpu_processes(gpu_processes)
    
    while running:
        time.sleep(2)
        update_tracked_processes(game_roots, seen_game_processes)
        update_zram_peaks(zram_peaks)
        update_gpu_processes(gpu_processes)
        
    # Exited loop (received SIGTERM)
    end_dt = datetime.now()
    session_data["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Capture final ZRAM state
    session_data["zram_end"] = {str(k): v for k, v in get_zram_usage().items()}
    
    # Structure the collected data
    session_data["zram_peaks"] = {str(k): v for k, v in zram_peaks.items()}
    session_data["gpu_processes"] = {str(k): v for k, v in gpu_processes.items()}
    session_data["game_processes"] = {str(k): v for k, v in seen_game_processes.items()}
    
    # Parse killed processes from the pre-game cleanup
    session_data["killed_processes"] = get_killed_processes_since()
    
    # Save structured session data
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        sys.stderr.write(f"Error saving session json data: {e}\n")
        
    # Append summary to game_session.log
    write_to_history_log()

def visible_len(s):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', s))

def format_table(headers, rows, col_widths):
    def pad_string(s, width, align='left'):
        v_len = visible_len(s)
        padding = width - v_len
        if padding < 0:
            clean_s = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', s)
            if len(clean_s) > width:
                s = clean_s[:width-3] + "..."
            v_len = visible_len(s)
            padding = width - v_len
            
        if align == 'right':
            return " " * padding + s
        else:
            return s + " " * padding

    # Print top border
    out = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐\n"
    # Print headers
    out += "│" + "│".join(f" \033[1m{pad_string(headers[i], col_widths[i])}\033[0m " for i in range(len(headers))) + "│\n"
    # Print header separator
    out += "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤\n"
    # Print rows
    for row in rows:
        out += "│" + "│".join(f" {pad_string(str(row[i]), col_widths[i])} " for i in range(len(row))) + "│\n"
    # Print bottom border
    out += "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘\n"
    return out

def print_session_summary():
    if not os.path.exists(DATA_FILE):
        print("No telemetry data found for the last session.")
        return
        
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading session data: {e}")
        return
        
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    try:
        start_dt = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(data["end_time"], "%Y-%m-%d %H:%M:%S")
        duration = str(end_dt - start_dt)
    except:
        duration = "Unknown"
        
    print(f"\n{BOLD}{CYAN}========================================================================{RESET}")
    print(f"{BOLD}{CYAN}   🎮  ROCKET LEAGUE SESSION PERFORMANCE SUMMARY{RESET}")
    print(f"{BOLD}{CYAN}========================================================================{RESET}")
    print(f" {BOLD}Session Duration:{RESET} {data['start_time']} to {data['end_time']} ({duration})")
    print(f"{BOLD}{CYAN}========================================================================{RESET}\n")
    
    # 1. Killed Processes
    print(f"{BOLD}{RED}🧹 1. KILLED PROCESSES DURING CLEANUP ({len(data['killed_processes'])}){RESET}")
    if data['killed_processes']:
        headers = ["PID", "Process Name", "Reason", "Command Line"]
        rows = []
        for p in data['killed_processes']:
            rows.append([str(p['pid']), p['name'], p['reason'], p['cmdline']])
        print(format_table(headers, rows, [7, 18, 16, 40]))
    else:
        print(f"  {GREEN}No processes were killed (environment was already clean!){RESET}\n")
        
    # 2. ZRAM Usage
    print(f"{BOLD}{YELLOW}📦 2. ZRAM SWAP MEMORY DETECTED (PEAK USAGE){RESET}")
    if data['zram_peaks']:
        headers = ["PID", "Process Name", "Peak Swap Size", "Command Line"]
        rows = []
        zram_sorted = sorted(data['zram_peaks'].items(), key=lambda x: x[1]['peak_kb'], reverse=True)
        for pid, info in zram_sorted:
            swap_mb = info['peak_kb'] / 1024.0
            swap_str = f"{swap_mb:.1f} MB ({info['peak_kb']} kB)"
            rows.append([pid, info['name'], swap_str, info['cmdline']])
        print(format_table(headers, rows, [7, 18, 18, 38]))
    else:
        print(f"  {GREEN}No processes used ZRAM swap space during this session.{RESET}\n")
        
    # 3. Game Spawned Processes
    print(f"{BOLD}{GREEN}🎮 3. PROCESSES LAUNCHED BY HEROIC / ROCKET LEAGUE ({len(data['game_processes'])}){RESET}")
    if data['game_processes']:
        headers = ["PID", "Process Name", "Time Seen", "Command Line"]
        rows = []
        game_sorted = sorted(data['game_processes'].items(), key=lambda x: x[1]['first_seen'])
        for pid, info in game_sorted:
            rows.append([pid, info['name'], info['first_seen'], info['cmdline']])
        print(format_table(headers, rows, [7, 18, 12, 44]))
    else:
        print(f"  {RED}No game processes were tracked. Did the game fail to launch?{RESET}\n")
        
    # 4. GPU Processes
    print(f"{BOLD}{MAGENTA}⚡ 4. NVIDIA GPU MEMORY CONSUMPTION (PEAK USAGE){RESET}")
    if data['gpu_processes']:
        headers = ["PID", "Process Name", "Type", "Peak Memory", "Status"]
        rows = []
        gpu_sorted = sorted(data['gpu_processes'].items(), key=lambda x: x[1].get('peak_memory_mib', 0), reverse=True)
        for pid, info in gpu_sorted:
            status = f"{GREEN}Spawned by Game{RESET}" if pid in data['game_processes'] else f"{YELLOW}System Process{RESET}"
            rows.append([pid, info['name'], info['type'], info['peak_memory_str'], status])
        print(format_table(headers, rows, [7, 24, 6, 12, 22]))
    else:
        print(f"  {RED}No processes used the Nvidia GPU during this session.{RESET}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: game_logger.py [--start | --stop | --daemon | --show]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "--start":
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                print(f"Telemetry logger is already running (PID: {old_pid})")
                sys.exit(0)
            except (ProcessLookupError, ValueError, FileNotFoundError):
                pass
                
        # Spawn background daemon process
        try:
            log_out = open(os.path.join(BASE_DIR, "daemon.log"), "a")
        except:
            log_out = subprocess.DEVNULL
            
        p = subprocess.Popen(
            [sys.executable, __file__, "--daemon"],
            stdout=log_out,
            stderr=log_out,
            stdin=subprocess.DEVNULL,
            preexec_fn=os.setpgrp
        )
        
        with open(PID_FILE, "w") as f:
            f.write(str(p.pid))
        print(f"📊 Started performance telemetry logger (PID: {p.pid}).")
        sys.exit(0)
        
    elif cmd == "--daemon":
        run_daemon()
        
    elif cmd == "--stop":
        if not os.path.exists(PID_FILE):
            print("Telemetry logger is not running.")
            sys.exit(0)
            
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
        except Exception as e:
            print(f"Could not read PID file: {e}")
            sys.exit(1)
            
        print(f"Stopping telemetry logger (PID: {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            print("Logger process not found. Cleaning up PID file...")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            sys.exit(0)
            
        # Wait for process to exit
        wait_time = 0
        while True:
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
                wait_time += 0.5
                if wait_time > 10:
                    print("Logger did not stop within 10 seconds. Forcing kill...")
                    os.kill(pid, signal.SIGKILL)
                    break
            except ProcessLookupError:
                break
                
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            
        print_session_summary()
        
    elif cmd == "--show":
        print_session_summary()
        
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
