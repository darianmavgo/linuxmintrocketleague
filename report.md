# RocketMode RAM & Process Report
Generated on: 2026-05-23 08:42:18

## 1. System Memory Summary
- **Total Memory**: 7.66 GB
- **Used Memory (Active + Kernel)**: 2.35 GB (30.6%)
- **Available Memory**: 5.31 GB (69.4%)
- **Free Memory**: 2.43 GB (31.8%)
- **Cache & Buffers**: 3.14 GB (41.0%)
- **Kernel Slab Cache**: 230.27 MB (2.9%)
- **Page Tables**: 40.50 MB (0.5%)

## 2. Temporary Filesystems (tmpfs in RAM)
| Mount Point | Used | Total | % Used |
| :--- | :---: | :---: | :---: |
| `/run` | 1.87 MB | 784.25 MB | 0.2% |
| `/dev/shm` | 46.00 MB | 3.83 GB | 1.2% |
| `/run/lock` | 12.00 KB | 5.00 MB | 0.2% |
| `/run/user/1000` | 204.00 KB | 784.24 MB | 0.0% |

## 3. Top 20 Processes occupying RAM
| PID | User | Process Name | RSS (Resident) | VSZ (Virtual) | % RAM | Role in Rocket League / Heroic | What Breaks if Missing | Command Line |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| 3009 | darian | chrome | 388.98 MB | 48.98 GB | 4.96% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome /home/darian/Documents/RocketMode/report.html` |
| 1909 | darian | cinnamon | 322.03 MB | 4.38 GB | 4.11% | The display server and window manager rendering Rocket League's graphics on your monitor and capturing inputs. | The graphical session terminates, immediately closing Heroic, Rocket League, and all open windows. | `cinnamon --replace` |
| 3054 | darian | chrome | 270.19 MB | 48.89 GB | 3.45% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=gpu-process --ozone-platform=x11 --crashpad-handler-pid=3017 --enab` |
| 2765 | darian | antigravity | 262.09 MB | 1.36 TB | 3.34% | The Antigravity AI pair programmer agent context (currently performing system diagnostics). | This interactive AI development session will terminate immediately. | `/home/darian/Documents/Antigravity-x64/antigravity --type=zygote` |
| 2314 | darian | antigravity | 253.84 MB | 48.74 GB | 3.24% | The Antigravity AI pair programmer agent context (currently performing system diagnostics). | This interactive AI development session will terminate immediately. | `/home/darian/Documents/Antigravity-x64/antigravity --type=zygote --no-zygote-sandbox` |
| 2409 | darian | language_server | 235.86 MB | 4.59 GB | 3.01% | The Antigravity AI pair programmer agent context (currently performing system diagnostics). | This interactive AI development session will terminate immediately. | `/home/darian/Documents/Antigravity-x64/resources/bin/language_server --standalone --override_ide_nam` |
| 2263 | darian | antigravity | 231.46 MB | 1.36 TB | 2.95% | The Antigravity AI pair programmer agent context (currently performing system diagnostics). | This interactive AI development session will terminate immediately. | `/home/darian/Documents/Antigravity-x64/antigravity` |
| 3119 | darian | chrome | 230.24 MB | 1.42 TB | 2.94% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=3017 --enable-crash-reporter=919aea` |
| 1342 | root | Xorg | 204.75 MB | 24.96 GB | 2.61% | The display server and window manager rendering Rocket League's graphics on your monitor and capturing inputs. | The graphical session terminates, immediately closing Heroic, Rocket League, and all open windows. | `/usr/lib/xorg/Xorg -core :0 -seat seat0 -auth /var/run/lightdm/root/:0 -nolisten tcp vt7 -novtswitch` |
| 3232 | darian | chrome | 188.83 MB | 1.42 TB | 2.41% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=3017 --enable-crash-reporter=919aea` |
| 3094 | darian | chrome | 145.72 MB | 1.41 TB | 1.86% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=renderer --top-chrome-webui --crashpad-handler-pid=3017 --enable-cr` |
| 3101 | darian | chrome | 134.32 MB | 1.41 TB | 1.71% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=3017 --enable-crash-reporter=919aea` |
| 3222 | darian | chrome | 124.83 MB | 1.42 TB | 1.59% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=3017 --enable-crash-reporter=919aea` |
| 3055 | darian | chrome | 120.92 MB | 48.42 GB | 1.54% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=utility --utility-sub-type=network.mojom.NetworkService --lang=en-U` |
| 2322 | darian | antigravity | 80.75 MB | 48.35 GB | 1.03% | Handles Epic Online Services (EOS) authentication, cross-play matchmaking, friends list sync, and multiplayer stats. | Multiplayer matchmaking, invite system, and sync with Epic Games servers will be disabled. | `/proc/self/exe --type=utility --utility-sub-type=network.mojom.NetworkService --lang=en-US --service` |
| 3255 | darian | chrome | 77.14 MB | 1.41 TB | 0.98% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=3017 --enable-crash-reporter=919aea` |
| 2980 | darian | nemo | 70.24 MB | 770.74 MB | 0.90% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/usr/bin/nemo` |
| 2473 | darian | antigravity | 66.27 MB | 48.39 GB | 0.85% | Handles Epic Online Services (EOS) authentication, cross-play matchmaking, friends list sync, and multiplayer stats. | Multiplayer matchmaking, invite system, and sync with Epic Games servers will be disabled. | `/proc/self/exe --type=utility --utility-sub-type=audio.mojom.AudioService --lang=en-US --service-san` |
| 3025 | darian | chrome | 64.86 MB | 48.40 GB | 0.83% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=zygote --no-zygote-sandbox --crashpad-handler-pid=3017 --enable-cra` |
| 3026 | darian | chrome | 64.81 MB | 48.40 GB | 0.83% | Non-critical background system process or application running concurrently with your game session. | No direct impact on Rocket League or Heroic, though reclaiming its RAM might slightly improve game performance. | `/opt/google/chrome/chrome --type=zygote --crashpad-handler-pid=3017 --enable-crash-reporter=919aeacf` |