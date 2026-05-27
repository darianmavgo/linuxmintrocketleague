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
