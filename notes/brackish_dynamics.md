# Brackish Dynamics — Visual Heartbeat Architecture

The brackish heartbeat extends Mystery's existing φ-e-π probes into a living
visual system: a **gauged clock** (stable reference) modulated by
**brackish_dynamics** (variable wind) driving a **nested Platonic resonator**
(responsive heartbeat).

## Conceptual Map

| Element | Name | Role | Ties to Mystery |
|---------|------|------|-----------------|
| Stable reference | Zero-point manifold | Fixed clock face + 12 o'clock line + 3-6-9 axis | `vortex_369_clock.py`, W_g = 350/π |
| Modulator ("wind") | `brackish_dynamics(t)` | Variable drive / conditions | Residual R, κ sweeps |
| Living heartbeat | Nested resonator | Twist, counter-twist, breathing | Platonic solids, Hopf geometry |
| Observed time | Effective-time track | ∫ brackish_dynamics dt | Long-horizon divergence from clock |

## brackish_dynamics

```python
def brackish_dynamics(t, base=1.0, amplitude=0.4, freq=0.01, residual_weight=0.15):
    wind = base + amplitude * sin(2π · freq · t)
    wind += residual_weight * R   # R = φ² + e² − π²
    return max(0.1, wind)
```

"Brackish" captures the transitional zone: neither pure ideal (φ, e, π) nor
fully chaotic — the fertile middle where emergence happens.

## Operating Modes

- **Stable conditions** — `stable_mode=True`: near-constant wind, regular heartbeat.
- **Dynamic / storm** — varying amplitude: irregular twisting, visible layer lag.

## Scripts

| File | Purpose |
|------|---------|
| `scripts/platonic_resonator.py` | Solid topology, rotation, twist, breathing |
| `scripts/brackish_clock.py` | Combined 2D clock + 3D animation, GIF/PNG export |

Regenerate:

```bash
cd mystery && .venv/bin/python scripts/brackish_clock.py
# or full suite:
.venv/bin/python run_all.py
```

## HF Space

Demo **J** on the Gravity tab — "Brackish Heartbeat" — loops a pre-rendered
animation with the same parameter family as the local script.

## Presets (future)

| Preset | base | amplitude | residual_weight | Mode |
|--------|------|-----------|-----------------|------|
| Calm Sea | 1.0 | 0.05 | 0.10 | stable |
| Building Storm | 1.0 | 0.55 | 0.15 | dynamic |
| Residual Dominant | 0.8 | 0.20 | 0.35 | dynamic |