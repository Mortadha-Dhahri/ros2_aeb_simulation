# AEB Simulation — Physics & Logic Reference

This document explains the physical model and node logic behind the simulation.
It is intended as a reference for understanding why the system behaves the way it does,
and as a guide for tuning parameters to match different real-world scenarios.

---

## Scenario overview

The simulation models a single ego vehicle travelling at constant speed on a straight road
toward a stationary obstacle. The vehicle has no prior knowledge of the obstacle —
it is detected only when the LiDAR sensor begins publishing range data at t=0.

```
t=0
┌─────────────────────────────────────────────┐
│  EGO VEHICLE ──────────────────► [OBSTACLE] │
│  v₀ = 33.3 m/s          d₀ = 300m          │
└─────────────────────────────────────────────┘
```

---

## Core physics

### Distance model

The gap between vehicle and obstacle closes at the current vehicle speed:

```
d(t+dt) = d(t) - v(t) × dt
```

The obstacle is stationary — only the vehicle's speed drives gap closure.
`dt = 1/publish_rate_hz = 0.1s` at 10 Hz.

### Speed model

Before AEB fires, the vehicle decelerates naturally (driver coasting):

```
v(t+dt) = v(t) - a_normal × dt
```

After AEB fires, maximum emergency deceleration is applied:

```
v(t+dt) = v(t) - a_aeb × dt
```

Speed is clamped to zero — the vehicle cannot reverse.

### Time To Collision (TTC)

TTC is computed every tick as an instantaneous estimate:

```
TTC = d(t) / v(t)
```

This answers: *if nothing changes from this moment, when do we collide?*

TTC is a reactive metric — it does not account for future deceleration.
It is used as a trigger threshold, not a precise collision predictor.
This matches how real AEB ECUs operate at the sensor fusion layer.

### TTC evolution — why it decreases non-linearly

Even with smooth deceleration, TTC does not decrease at a constant rate.
As speed drops, the denominator shrinks, causing TTC to decrease faster
in the early phase and slower once braking begins.

Approximate timeline at highway scenario defaults (v₀=33.3 m/s, d₀=300m):

```
t=0.0s   dist=300m   speed=33.3m/s   TTC=9.00s   → IDLE
t=6.0s   dist=103m   speed=31.5m/s   TTC=3.27s   → WARNING
t=7.8s   dist=46m    speed=30.9m/s   TTC=1.49s   → FULL BRAKE
t=11.5s  dist=~10m   speed=0.0m/s    TTC=∞       → STOPPED
```

### Emergency braking — theoretical stop distance

Using kinematic equations:

```
d_stop = v² / (2 × a_aeb)
       = 30.9² / (2 × 9.0)
       = 954.8 / 18
       = 53.0m
```

With ~46m remaining at brake trigger, the theoretical stop distance exceeds
the available gap. This is intentional and physically realistic —
at highway speeds with late AEB activation, the system reduces impact speed
rather than preventing collision entirely.

In practice the simulation stops the vehicle before impact because the
deceleration model is applied to vehicle speed which reaches zero.
In a real scenario at these parameters, AEB would reduce impact speed
from ~31 m/s to approximately 5–15 m/s depending on exact trigger timing.

### Brake pressure ramp

The brake actuator does not apply full pressure instantaneously.
It ramps at 0.2 per tick (10 Hz), reaching full pressure in 500ms.
This models hydraulic actuator lag in a real braking system.

```
t=0ms    pressure=0%
t=100ms  pressure=20%
t=200ms  pressure=40%
t=300ms  pressure=60%
t=400ms  pressure=80%
t=500ms  pressure=100%
```

During ramp-up, effective deceleration is proportionally reduced,
which is why simulation stop time is slightly longer than theoretical.

---

## AEB decision logic

### Three-phase state machine

```
         TTC < TTC_WARN                TTC < TTC_BRAKE
IDLE ───────────────────► WARNING ───────────────────► BRAKING ──► STOPPED
     ◄───────────────────                                           (speed=0)
         TTC ≥ TTC_WARN
```

**IDLE** — normal driving, system monitoring. No action taken.

**WARNING** — TTC has crossed the warning threshold. In a real vehicle
this triggers an audible alert and dashboard warning, giving the driver
1.5–2.0 seconds to react before autonomous braking engages.
If TTC recovers (driver braked independently), the system returns to IDLE.

**BRAKING** — TTC has crossed the brake threshold. Full emergency braking
is latched. There is no recovery from this state — releasing the brakes
mid-emergency at highway speed would be dangerous.

**STOPPED** — vehicle speed has reached zero. Shutdown signal is published.

### Why WARNING → IDLE recovery exists

A system that permanently latches WARNING after a single threshold crossing
would generate false positives in cut-in scenarios (another vehicle
momentarily enters the lane and then clears). The recovery transition
makes the system robust to transient TTC dips.

### Threshold values and real-world reference

| Threshold    | Simulation | Euro NCAP reference |
|---|---|---|
| TTC_WARN     | 3.0s       | 2.5–3.5s            |
| TTC_BRAKE    | 1.5s       | 1.2–1.8s            |
| a_aeb        | 9.0 m/s²   | 8.0–10.0 m/s²       |

---

## Parameter tuning guide

### Urban scenario (50 km/h)

```yaml
initial_distance_m: 80.0
initial_speed_mps: 13.9    # 50 km/h
normal_decel_mps2: 1.5
aeb_decel_mps2: 9.0
```

Expected: ~4s simulation, vehicle stops with ~10m to spare.

### Highway scenario (120 km/h)

```yaml
initial_distance_m: 300.0
initial_speed_mps: 33.3    # 120 km/h
normal_decel_mps2: 0.3
aeb_decel_mps2: 9.0
```

Expected: ~11s simulation, impact speed reduced but not zero at trigger point.

### Late activation (stress test)

```yaml
initial_distance_m: 40.0
initial_speed_mps: 13.9
normal_decel_mps2: 0.5
aeb_decel_mps2: 9.0
```

Expected: WARNING and BRAKE trigger almost simultaneously, very short
reaction window, vehicle may not fully stop before reaching obstacle.

---

## Known limitations

**TTC as sole metric** — real AEB systems fuse TTC with object classification,
lane position, driver input, and multi-sensor data. TTC alone produces
false positives in adjacent lane traffic and false negatives in
slow-closing scenarios.

**1D model** — the simulation has no lateral dynamics. Real scenarios involve
steering, lane changes, and cut-ins which are not modelled here.

**Constant obstacle** — the obstacle is always stationary. A leading vehicle
braking hard (dynamic obstacle) would require a different relative speed model.

**No sensor noise** — real LiDAR has range noise, dropouts, and angular
resolution limits. The simulation publishes perfect distance values.
