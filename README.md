# ROS2 AEB Simulation

Autonomous Emergency Braking simulation built with ROS2 Jazzy, Docker, and Cyclone DDS.
Developed and tested on Windows with Docker Desktop.

**Maintainer:** Mortadha Dhahri — mortatha.dhahri@enicar.ucar.tn

---

## What this is

A physics-based simulation of an Autonomous Emergency Braking system implemented
as a ROS2 multi-node pipeline. The system models a vehicle approaching a stationary
obstacle, computes Time To Collision in real time, and autonomously applies emergency
braking when thresholds are crossed.

See [simulation_physics.md](simulation_physics.md) for the full physics and logic reference.

---

## Architecture

```
lidar_sim_node ──/lidar/range──────────────────────────────────────────► (monitor)
lidar_sim_node ──/ttc──────────────────────────────────────────────────► aeb_decision_node
vehicle_state_node ──/vehicle/speed──► lidar_sim_node
vehicle_state_node ──/vehicle/speed──► aeb_decision_node
                                       aeb_decision_node ──/brake_cmd──► vehicle_state_node
                                       aeb_decision_node ──/brake_cmd──► brake_actuator_node
                                       aeb_decision_node ──/brake_cmd──► logger_node
                                       brake_actuator_node ──/brake/pressure──► logger_node
                                       aeb_decision_node ──/simulation/shutdown──► all nodes
```

| Node | Role |
|---|---|
| `lidar_sim_node` | Simulates LiDAR sensor, computes TTC from distance and vehicle speed |
| `vehicle_state_node` | Models ego vehicle speed, applies normal and emergency deceleration |
| `aeb_decision_node` | Three-state machine (IDLE→WARNING→BRAKING→STOPPED), publishes brake commands |
| `brake_actuator_node` | Models hydraulic brake pressure ramp (500ms to full pressure) |
| `logger_node` | Records all milestone events with timestamps and elapsed time |
| `shutdown_node` | Receives shutdown signal, exits cleanly to trigger launch teardown |

---

## Project structure

```
ros2_aeb_simulation/
├── Dockerfile
├── docker-compose.yml
├── cyclone_config.xml
├── .dockerignore
├── .gitignore
├── README.md
├── simulation_physics.md
└── aeb_ws/
    └── src/
        ├── aeb_interfaces/
        │   ├── srv/
        │   │   └── AebStatus.srv
        │   ├── CMakeLists.txt
        │   └── package.xml
        └── aeb_simulation/
            ├── aeb_simulation/
            │   ├── __init__.py
            │   ├── lidar_sim_node.py
            │   ├── vehicle_state_node.py
            │   ├── aeb_decision_node.py
            │   ├── brake_actuator_node.py
            │   ├── logger_node.py
            │   └── shutdown_node.py
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

## Quick start

### Prerequisites

- Windows with Docker Desktop + WSL2 backend
- Git Bash or PowerShell

### 1 — Build the image

```powershell
cd ros2_aeb_simulation
docker compose build
```

### 2 — Start the container

```powershell
docker compose up -d
docker exec -it aeb_sim bash
```

### 3 — Build the workspace

```bash
cd /aeb_ws
colcon build
source install/setup.bash
```

### 4 — Run the simulation

```bash
ros2 launch aeb_simulation aeb.launch.py
```

The simulation runs to completion and shuts down all nodes cleanly on its own.

---

## Monitoring (second terminal)

```powershell
docker exec -it aeb_sim bash
source /aeb_ws/install/setup.bash

ros2 topic echo /aeb/command          # brake commands
ros2 topic echo /ttc                  # live TTC values
ros2 topic echo /brake/pressure       # hydraulic pressure ramp
ros2 topic hz /lidar/range            # sensor publish rate
ros2 node list                        # verify all nodes running
```

---

## Parameters

| Node | Parameter | Default | Description |
|---|---|---|---|
| `lidar_sim_node` | `initial_distance_m` | 300.0 | Starting distance to obstacle in metres |
| `lidar_sim_node` | `publish_rate_hz` | 10.0 | Sensor publish rate |
| `vehicle_state_node` | `initial_speed_mps` | 33.3 | Initial vehicle speed (120 km/h) |
| `vehicle_state_node` | `normal_decel_mps2` | 0.3 | Coasting deceleration before AEB |
| `vehicle_state_node` | `aeb_decel_mps2` | 9.0 | Emergency braking deceleration (~0.9g) |
| `aeb_decision_node` | `TTC_WARN` | 3.0s | Warning threshold |
| `aeb_decision_node` | `TTC_BRAKE` | 1.5s | Emergency brake threshold |

---

## Tune parameters live

```bash
ros2 param set /aeb_decision_node ttc_threshold 2.0
ros2 param set /vehicle_state_node initial_speed_mps 20.0
```

Or edit `config/params.yaml` and relaunch.

---

## Windows-specific notes

### Why Cyclone DDS

Docker Desktop on Windows runs inside a Hyper-V/WSL2 VM. Fast DDS multicast
is blocked by the NAT layer. Cyclone DDS with a custom `cyclone_config.xml`
handles bridge networking correctly.

### Volume mount performance

For faster `colcon build`, clone the project inside WSL2:

```bash
cd ~
git clone <repo> ros2_aeb_simulation
```

Avoids NTFS → WSL2 filesystem translation (2–3× speedup).

---

## Known issues and fixes

### `colcon build` — no Python modules to install
Add `setup.cfg` to `src/aeb_simulation/`:
```ini
[develop]
script_dir=$base/lib/aeb_simulation
[install]
install_scripts=$base/lib/aeb_simulation
```

### `libexec directory does not exist` on launch
Missing `setup.cfg` — add it and clean rebuild:
```bash
rm -rf build/ install/ log/
colcon build
```

### `Waiting for sensor data...` — nodes not communicating
Restart the container to pick up Cyclone DDS environment:
```powershell
docker compose down && docker compose up -d
```

### Broken filenames like `lidar_sim_[node.py](http://node.py)`
Always create files via VS Code New File or `touch filename.py`.
Never copy filenames from a rendered markdown page.

### `FROM osrf/ros:jazzy-ros-core` not found
Use the official Docker library image:
```dockerfile
FROM ros:jazzy-ros-core
```

---

## Next steps

- Add sensor noise to `lidar_sim_node` for more realistic detection
- Model a dynamic obstacle (leading vehicle braking)
- Add lateral dynamics for cut-in scenarios
- Record a ROS2 bag: `ros2 bag record -a`
- Add GitHub Actions CI to build and test on every push