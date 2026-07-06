"""Brackish flux + flux_spring inter-orb coupling — two-orb minimal model, N-orb extension."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

W_G = 350.0 / np.pi
STABLE_OUTER_SHIELD = True

# Tunable reference config — override via kwargs, CLI, or HF sliders later.
FLUX_SPRING_CONFIG: dict[str, float] = {
    "flux_gauge_rigidness": 0.25,
    "compression_strength": 0.35,
    "base_coupling": 0.75,
    "flux_influence_on_rigidness": 0.15,
    "inner_emergent_expansion": 0.35,
    "twist_coupling_blend": 0.55,
    "flux_floor": 0.2,
    "flux_turbulence": 0.35,
    "burst_perturbation_strength": 0.12,
    "shield_probe_modulation": 0.015,
}


def merge_flux_spring_config(**overrides: Any) -> dict[str, float]:
    """Merge caller overrides into the reference flux_spring config."""
    cfg = dict(FLUX_SPRING_CONFIG)
    for key, value in overrides.items():
        if key in cfg and value is not None:
            cfg[key] = float(value)
    return cfg


def wg_burst_envelope(t: float, *, width: float = 0.06) -> dict[str, float | bool]:
    """
    Periodic burst gate scaled by 350/π (W_g).

    Peaks at integer multiples of W_g; strength decays Gaussian-like from each peak.
    """
    phase = float((float(t) / W_G) % 1.0)
    dist = min(phase, 1.0 - phase)
    strength = float(np.exp(-(dist / width) ** 2))
    return {"phase": phase, "strength": strength, "active": strength > 0.35}


def effective_flux_turbulence(
    flux_turbulence: float,
    burst_strength: float,
    *,
    burst_coupling: float = 0.65,
) -> float:
    """Base turbulence plus burst-derived amplification for inner oscillation."""
    return float(flux_turbulence * (1.0 + burst_coupling * burst_strength))


def lorentz_perturbation(
    t: float,
    layer_idx: int,
    n_orbs: int,
    *,
    burst_strength: float,
    turbulence: float,
    perturbation_strength: float,
) -> tuple[float, float]:
    """
    Small chaotic radius + twist offsets for inner shells during W_g bursts.

    Outer shield probes inward only — no perturbation on the outermost layer.
    """
    if layer_idx >= n_orbs - 1 or burst_strength < 1e-6:
        return 0.0, 0.0

    depth = layer_idx / max(1, n_orbs - 2)
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    dt = 0.018 * burst_strength
    x = np.sin(0.37 * t + depth * 2.1) * 0.5
    y = np.cos(0.29 * t + depth * 1.7) * 0.5
    z = np.sin(0.41 * t + depth * 3.3) * 0.5 + 0.1 * burst_strength
    for _ in range(3):
        x = x + dt * sigma * (y - x)
        y = y + dt * (x * (rho - z) - y)
        z = z + dt * (x * y - beta * z)

    scale = perturbation_strength * turbulence * burst_strength * (1.0 - 0.4 * depth)
    return float(scale * np.tanh(x)), float(scale * 1.8 * np.tanh(y))


def brackish_flux(
    t: float,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    residual_r: float | None = None,
    flux_floor: float | None = None,
) -> float:
    """Variable solar-wind-like driver (primary modulator)."""
    floor = FLUX_SPRING_CONFIG["flux_floor"] if flux_floor is None else float(flux_floor)
    r_val = 0.0 if residual_r is None else float(residual_r)
    if stable_mode:
        flux = base + residual_weight * r_val
    else:
        flux = base + amplitude * np.sin(2.0 * np.pi * freq * t) + residual_weight * r_val
    return max(floor, float(flux))


def brackish_dynamics(t: float, **kwargs: Any) -> float:
    """Backward-compatible alias for brackish_flux."""
    return brackish_flux(t, **kwargs)


def flux_spring(
    flux_value: float,
    *,
    rigidness: float | None = None,
    compression_strength: float | None = None,
    base_coupling: float | None = None,
    flux_influence_on_rigidness: float | None = None,
    **_: Any,
) -> dict[str, float]:
    """
    Minimal two-orb interaction — compression on outer orb + gauge-style coupling.

    Designed for easy tuning; reference values emerge through experimentation.
    """
    cfg = merge_flux_spring_config(
        flux_gauge_rigidness=rigidness,
        compression_strength=compression_strength,
        base_coupling=base_coupling,
        flux_influence_on_rigidness=flux_influence_on_rigidness,
    )
    rigid = float(cfg["flux_gauge_rigidness"])
    compression_strength = float(cfg["compression_strength"])
    base_coupling = float(cfg["base_coupling"])
    flux_influence = float(cfg["flux_influence_on_rigidness"])

    effective_rigidness = rigid * (1.0 + flux_influence * (float(flux_value) - 1.0))
    effective_rigidness = float(np.clip(effective_rigidness, 0.1, 1.0))

    excess_flux = max(0.0, float(flux_value) - 1.0)
    outer_compression = 1.0 - compression_strength * excess_flux
    outer_compression = max(0.55, outer_compression)

    coupling = base_coupling * (0.7 + 0.5 * effective_rigidness)

    return {
        "outer_compression": float(outer_compression),
        "coupling": float(coupling),
        "effective_rigidness": effective_rigidness,
        "excess_flux": float(excess_flux),
    }


def global_pointer_deg(
    flux_value: float,
    spring: dict[str, float],
    *,
    t: float = 0.0,
) -> float:
    """
    Compass-like alignment — dominant push (compression) vs emergent pull (coupling).

    0° = +X reference; inward compression biases toward 270° (push).
    """
    push = spring["outer_compression"]
    pull = spring["coupling"] * (float(flux_value) - push)
    wobble = 0.12 * spring["effective_rigidness"] * np.sin(2.0 * np.pi * 0.01 * t)
    angle = float(np.degrees(np.arctan2(pull + wobble, push - 1.0)))
    return angle % 360.0


@dataclass
class NestedOrbPhysics:
    """Per-orb radius + twist state derived from flux_spring (N-orb extension)."""

    radius_factors: list[float]
    twist_blend: list[float]
    global_pointer_deg: float
    spring: dict[str, float]
    metrics: dict[str, float] = field(default_factory=dict)
    flux_turbulence_effective: float = 0.0
    burst_strength: float = 0.0
    burst_active: bool = False
    outer_spiral_twist: float = 0.0
    twist_perturbations: list[float] = field(default_factory=list)


def nested_orb_physics(
    flux_value: float,
    n_orbs: int,
    *,
    t: float = 0.0,
    stable_outer_shield: bool | None = None,
    **config_overrides: Any,
) -> NestedOrbPhysics:
    """
    Extend two-orb flux_spring to nested orbs.

    Primary: outer orbs compress under stronger flux (solar-wind analogy).
    Secondary: inner orbs may expand via spring coupling (emergent).
    W_g bursts inject Lorentz-style perturbations inward; outer shield stays stable.
    """
    cfg = merge_flux_spring_config(**config_overrides)
    spring = flux_spring(flux_value, **cfg)
    n = max(1, int(n_orbs))
    stable_shield = STABLE_OUTER_SHIELD if stable_outer_shield is None else bool(stable_outer_shield)

    burst = wg_burst_envelope(t)
    burst_strength = float(burst["strength"])
    turb_base = float(cfg["flux_turbulence"])
    turb_eff = effective_flux_turbulence(turb_base, burst_strength)
    pert_strength = float(cfg["burst_perturbation_strength"])
    probe_mod = float(cfg["shield_probe_modulation"])

    radius_factors = [1.0] * n
    twist_blend = [0.0] * n
    twist_perturbations = [0.0] * n
    compression = spring["outer_compression"]
    coupling = spring["coupling"]
    rigid = spring["effective_rigidness"]
    emergent = float(cfg["inner_emergent_expansion"])
    twist_base = float(cfg["twist_coupling_blend"])

    for idx in range(n):
        exposure = idx / max(1, n - 1) if n > 1 else 1.0
        radius_factors[idx] = compression ** (exposure * (1.0 + 0.5 * (n - 1 - idx) / max(1, n - 1)))
        if idx < n - 1:
            slack = max(0.0, 1.0 - compression)
            radius_factors[idx] *= 1.0 + emergent * coupling * slack * (1.0 - exposure)

    for idx in range(1, n):
        pair_exposure = idx / max(1, n - 1)
        twist_blend[idx] = float(
            np.clip(twist_base * coupling * rigid * (0.5 + 0.5 * pair_exposure), 0.0, 0.95)
        )

    for idx in range(n):
        r_off, t_off = lorentz_perturbation(
            t,
            idx,
            n,
            burst_strength=burst_strength,
            turbulence=turb_eff,
            perturbation_strength=pert_strength,
        )
        radius_factors[idx] += r_off
        twist_perturbations[idx] = t_off

    if stable_shield and n > 0:
        outer_idx = n - 1
        radius_factors[outer_idx] = 1.0 + probe_mod * burst_strength * np.sin(
            2.0 * np.pi * float(burst["phase"])
        )
        twist_perturbations[outer_idx] = 0.0

    outer_spiral_twist = float(
        burst_strength * 2.5 * np.sin(2.0 * np.pi * 3.0 * t / W_G + float(burst["phase"]) * 2.0 * np.pi)
    )

    pointer = global_pointer_deg(flux_value, spring, t=t)
    metrics = {
        "flux": float(flux_value),
        "outer_compression": compression,
        "coupling": coupling,
        "effective_rigidness": rigid,
        "radius_min": float(min(radius_factors)),
        "radius_max": float(max(radius_factors)),
        "twist_blend_max": float(max(twist_blend)),
        "global_pointer_deg": pointer,
        "flux_turbulence": turb_base,
        "flux_turbulence_effective": turb_eff,
        "burst_strength": burst_strength,
        "burst_active": float(bool(burst["active"])),
        "outer_spiral_twist": outer_spiral_twist,
        "stable_outer_shield": float(stable_shield),
    }
    return NestedOrbPhysics(
        radius_factors=radius_factors,
        twist_blend=twist_blend,
        global_pointer_deg=pointer,
        spring=spring,
        metrics=metrics,
        flux_turbulence_effective=turb_eff,
        burst_strength=burst_strength,
        burst_active=bool(burst["active"]),
        outer_spiral_twist=outer_spiral_twist,
        twist_perturbations=twist_perturbations,
    )


def flux_spring_metrics_line(physics: NestedOrbPhysics) -> str:
    """One-line instrumentation for comparing runs."""
    m = physics.metrics
    return (
        f"flux={m['flux']:.3f} · compression={m['outer_compression']:.3f} · "
        f"coupling={m['coupling']:.3f} · rigid={m['effective_rigidness']:.3f} · "
        f"r∈[{m['radius_min']:.3f},{m['radius_max']:.3f}] · "
        f"turb={m['flux_turbulence_effective']:.3f} · burst={m['burst_strength']:.3f} · "
        f"pointer={m['global_pointer_deg']:.1f}°"
    )