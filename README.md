# ROS2 AEB Simulation

Autonomous Emergency Braking simulation using ROS2 nodes, Docker, and Cyclone DDS.
Built and tested on Windows with Docker Desktop.

**Maintainer:** Mortadha Dhahri — mortatha.dhahri@enicar.ucar.tn

---

## Project structure

```
ros2_aeb_simulation/
├── Dockerfile
├── docker-compose.yml
├── cyclone_config.xml
├── .dockerignore
├── .gitignore
└── aeb_ws/
    └── src/
        └── aeb_simulation/
            ├── aeb_simulation/
            │   ├── __init__.py
            │   ├── lidar_sim_node.py
            │   ├── vehicle_state_node.py
            │   └── aeb_decision_node.py
            ├── launch/
            │   └── aeb.launch.py
            ├── config/
            │   └── params.yaml
            ├── resource/
            │   └── aeb_simulation
            ├── srv/
            ├── setup.cfg
            ├── package.xml
            └── setup.py
```

---

## Node architecture

```
lidar_sim_node ──/lidar/range──────┐
                                   ├──> aeb_decision_node ──/aeb/command
vehicle_state_node ──/vehicle/speed┘
```

| Node | Role | Topics |
|---|---|---|
| `lidar_sim_node` | Simulates a LiDAR sensor — obstacle closes at a configurable speed | publishes `/lidar/range` |
| `vehicle_state_node` | Simulates ego vehicle speed | publishes `/vehicle/speed` |
| `aeb_decision_node` | Computes TTC, decides to brake or clear | subscribes to both, publishes `/aeb/command` |

**TTC formula:** `TTC = distance / speed`
**Brake condition:** `TTC < ttc_threshold`

With default params (distance=50m, closing_speed=5m/s, vehicle_speed=15m/s, threshold=2s), braking triggers at ~4 seconds into the simulation when distance drops below 30m.

---

## Quick start

### Prerequisites

- Windows with Docker Desktop installed
- WSL2 backend enabled in Docker Desktop
- Git Bash or PowerShell

### 1 — Clone and navigate

```powershell
cd ros2_aeb_simulation
```

### 2 — Build the Docker image

```powershell
docker compose build
```

First build takes 2–3 minutes — it downloads and installs ROS2 packages.

### 3 — Start the container

```powershell
docker compose up -d
docker ps    # verify aeb_sim is running
```

### 4 — Open a shell inside the container

```powershell
docker exec -it aeb_sim bash
```

### 5 — Build the ROS2 workspace

```bash
cd /aeb_ws
colcon build
source install/setup.bash
```

### 6 — Launch the simulation

```bash
ros2 launch aeb_simulation aeb.launch.py
```

Expected output for the first ~4 seconds:
```
[aeb_decision_node] CLEAR — TTC=3.33s | dist=50.0m
[aeb_decision_node] CLEAR — TTC=2.80s | dist=42.0m
```

Then braking triggers:
```
[aeb_decision_node] BRAKE — TTC=1.98s | dist=29.7m | speed=15.0m/s
```

---

## Second terminal — monitor topics

Open a new PowerShell tab:

```powershell
docker exec -it aeb_sim bash
source /aeb_ws/install/setup.bash

ros2 topic echo /aeb/command      # watch brake commands
ros2 topic list                   # verify all topics are visible
ros2 topic hz /lidar/range        # check publish rate
ros2 node list                    # verify all nodes are running
```

---

## Tune parameters live

Without restarting or recompiling:

```bash
ros2 param set /aeb_decision_node ttc_threshold 4.0     # brake sooner
ros2 param set /lidar_sim_node closing_speed_mps 10.0   # faster obstacle
ros2 param set /vehicle_state_node speed_mps 20.0       # faster vehicle
```

Or edit `config/params.yaml` and relaunch.

---

## Parameters reference

| Node | Parameter | Default | Description |
|---|---|---|---|
| `lidar_sim_node` | `initial_distance_m` | 50.0 | Starting distance to obstacle in metres |
| `lidar_sim_node` | `closing_speed_mps` | 5.0 | How fast the obstacle closes in m/s |
| `lidar_sim_node` | `publish_rate_hz` | 10.0 | Publish frequency |
| `vehicle_state_node` | `speed_mps` | 15.0 | Ego vehicle speed in m/s |
| `vehicle_state_node` | `publish_rate_hz` | 10.0 | Publish frequency |
| `aeb_decision_node` | `ttc_threshold` | 2.0 | Brake if TTC drops below this value in seconds |
| `aeb_decision_node` | `publish_rate_hz` | 10.0 | Decision rate |

---

## Windows-specific notes

### Why `network_mode: host` is not used

Docker Desktop on Windows runs inside a Hyper-V/WSL2 VM. `network_mode: host` maps to the VM's network, not the Windows host — DDS multicast gets blocked by the NAT layer. The project uses Cyclone DDS with a custom config instead.

### Why Cyclone DDS instead of Fast DDS

Fast DDS relies heavily on UDP multicast which Docker Desktop blocks on Windows. Cyclone DDS handles Docker's NAT-ed bridge networking better and is configured via `cyclone_config.xml`.

### Volume mount performance

If `colcon build` is slow, move the project inside WSL2 instead of keeping it on your Windows drive:

```bash
# in WSL2 terminal
cd ~
git clone <your-repo> ros2_aeb_simulation
cd ros2_aeb_simulation
docker compose up -d
```

This avoids the NTFS → WSL2 filesystem translation layer which can make builds 2–3x slower.

---

## Known issues and fixes

### `colcon build` — no Python modules to install

**Cause:** `setup.cfg` was missing, so `setuptools` didn't know where to put executable scripts.

**Fix:** Add `setup.cfg` to `src/aeb_simulation/`:
```ini
[develop]
script_dir=$base/lib/aeb_simulation

[install]
install_scripts=$base/lib/aeb_simulation
```

### `libexec directory does not exist` on launch

**Cause:** Entry point scripts weren't generated into `lib/aeb_simulation/` during build.

**Fix:** Add `setup.cfg` above, then clean rebuild:
```bash
rm -rf build/ install/ log/
colcon build
```

### `Waiting for sensor data...` — nodes not communicating

**Cause:** DDS discovery failing due to Windows Docker Desktop networking.

**Fix:** Ensure `cyclone_config.xml` is present at the project root and `docker-compose.yml` has:
```yaml
environment:
  - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  - CYCLONEDDS_URI=file:///cyclone_config.xml
volumes:
  - ./cyclone_config.xml:/cyclone_config.xml:ro
```

Then restart the container:
```powershell
docker compose down
docker compose up -d
```

### Broken filenames like `lidar_sim_[node.py](http://node.py)`

**Cause:** Copying filenames from a rendered markdown interface converts `node.py` into a hyperlink, which becomes part of the actual filename on disk.

**Fix:** Always create files using your editor (VS Code New File) or `touch filename.py` in the terminal. Never copy filenames from a rendered markdown page.

### `osrf/ros:jazzy-ros-core` not found

**Cause:** The `osrf/` prefix points to a different Docker Hub organisation that doesn't have this tag.

**Fix:** Use the official Docker library image instead:
```dockerfile
FROM ros:jazzy-ros-core    # not osrf/ros:jazzy-ros-core
```

---

## Next steps

Once the core pipeline is validated:

- Add `brake_actuator_node` — subscribes to `/aeb/command`, simulates brake state machine
- Add `logger_node` — records state change events with timestamps
- Add `/aeb/status` service — system health check using ROS2 services
- Record a ROS2 bag: `ros2 bag record -a` for post-run analysis
- Add CI with GitHub Actions to build and test the workspace on every push
