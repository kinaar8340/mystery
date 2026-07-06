"""Brackish clock + nested Platonic heartbeat — HF Space rendering (self-contained)."""

from __future__ import annotations

import base64
import colorsys
import io
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

PHI = (1.0 + np.sqrt(5.0)) / 2.0
E = np.e
PI = np.pi
R = PHI**2 + E**2 - PI**2
W_G = 350.0 / PI
KAPPA_DOC = 0.85
E_OVER_PI = E / PI

BRACKISH_PRESETS: dict[str, dict[str, Any]] = {
    "calm_sea": {
        "label": "Calm Sea",
        "base": 1.0,
        "amplitude": 0.05,
        "freq": 0.008,
        "residual_weight": 0.10,
        "stable_mode": False,
    },
    "building_storm": {
        "label": "Building Storm",
        "base": 1.0,
        "amplitude": 0.55,
        "freq": 0.018,
        "residual_weight": 0.15,
        "stable_mode": False,
    },
    "residual_dominant": {
        "label": "Residual Dominant",
        "base": 0.80,
        "amplitude": 0.20,
        "freq": 0.012,
        "residual_weight": 0.35,
        "stable_mode": False,
    },
    "steady_gauged": {
        "label": "Steady Gauged",
        "base": 1.0,
        "amplitude": 0.0,
        "freq": 0.01,
        "residual_weight": 0.12,
        "stable_mode": True,
    },
}

DEFAULT_BRACKISH_PARAMS: dict[str, Any] = {
    "base": 1.0,
    "amplitude": 0.4,
    "freq": 0.01,
    "residual_weight": 0.15,
    "stable_mode": False,
    "visual_separation": 0.024,
    "flux_gauge_rigidness": 0.25,
    "compression_strength": 0.35,
    "base_coupling": 0.75,
    "flux_influence_on_rigidness": 0.15,
    "inner_emergent_expansion": 0.35,
    "twist_coupling_blend": 0.55,
    "flux_turbulence": 0.35,
}

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

# === VISUAL ONLY — does not affect twist, counter-twist, or breathing math ===
# Tight nesting: inner shells must stay inside the outer geodesic shield.
_DEFAULT_VISUAL_SCALES: dict[str, float] = {
    "tetrahedron": 0.20,
    "octahedron": 0.224,
    "cube": 0.248,
    "icosahedron": 0.272,
    "dodecahedron": 0.86,
}
_DEFAULT_VISUAL_SEPARATION = 0.024
_SOLID_ORDER = ("tetrahedron", "octahedron", "cube", "icosahedron", "dodecahedron")

_VIEWPORT_BG = "#0a0a0f"
_VIEWPORT_FIGSIZE = (6.0, 6.0)
_QUAD_VIEWPORT_FIGSIZE = (12.8, 6.2)  # matches HF single-viewport (~620px tall)
_QUAD_RENDER_DPI = 100
_VIEWPORT_ELEV = 26.0
_VIEWPORT_AZIM = 45.0
_NESTED_VIEWPORT_SCALE = 1.42
_QUAD_VIEWPORT_SCALE = 1.62
_QUAD_LIM_FACTOR = 1.04
_DIMMED_LINE_COLOR = "#ffffff"
_DIMMED_LINE_ALPHA = 0.3
_DIMMED_LINE_WIDTH = 0.65
_HIGHLIGHT_LINE_WIDTH = 0.65

# Demo J 2×2 — exterior | interior | interior | central (row-major)
_DEMO_J_QUAD_PANELS: tuple[tuple[int, int, int, str], ...] = (
    (0, 0, 4, "Exterior"),
    (0, 1, 3, "Interior"),
    (1, 0, 2, "Interior"),
    (1, 1, 0, "Central"),
)


_USE_GEODESIC_OUTER = True
_STABLE_OUTER_SHIELD = True
# 1-frequency: readable wireframe. freq=3 (~1280 faces) muddles inner Platonic shells.
_GEODESIC_OUTER_FREQUENCY = 1

_BRACKISH_VIEWPORT_REV = "visual-nest-tight-v3"
_GEODESIC_MESH_CACHE: dict[int, tuple[np.ndarray, list[tuple[int, ...]]]] = {}


def brackish_params_key(**kwargs: Any) -> str:
    """Cache key for rendered media."""
    parts = [
        f"{k}={kwargs.get(k, DEFAULT_BRACKISH_PARAMS.get(k))!r}"
        for k in ("base", "amplitude", "freq", "residual_weight", "stable_mode", "visual_separation")
    ]
    parts.append(f"viewport={_BRACKISH_VIEWPORT_REV!r}")
    return "|".join(parts)


def _visual_radius_scales(visual_separation: float | None = None) -> dict[str, float]:
    """Absolute render radii per shell — frontend spacing only."""
    if visual_separation is None or abs(float(visual_separation) - _DEFAULT_VISUAL_SEPARATION) < 1e-9:
        return dict(_DEFAULT_VISUAL_SCALES)
    inner = _DEFAULT_VISUAL_SCALES["tetrahedron"]
    sep = float(visual_separation)
    return {name: inner + idx * sep for idx, name in enumerate(_SOLID_ORDER)}


def _visual_render_multiplier(
    layer_name: str,
    base_radius: float,
    *,
    layer_index: int,
    visual_separation: float | None = None,
) -> float:
    """Scale physics vertices to visual radius without changing backend geometry."""
    scales = _visual_radius_scales(visual_separation)
    visual_radius = scales.get(layer_name, base_radius)
    return visual_radius / max(float(base_radius), 1e-12)


def _merge_flux_spring_config(**overrides: Any) -> dict[str, float]:
    cfg = dict(FLUX_SPRING_CONFIG)
    for key, value in overrides.items():
        if key in cfg and value is not None:
            cfg[key] = float(value)
    return cfg


def _wg_burst_envelope(t: float, *, width: float = 0.06) -> dict[str, float | bool]:
    phase = float((float(t) / W_G) % 1.0)
    dist = min(phase, 1.0 - phase)
    strength = float(np.exp(-(dist / width) ** 2))
    return {"phase": phase, "strength": strength, "active": strength > 0.35}


def _effective_flux_turbulence(
    flux_turbulence: float,
    burst_strength: float,
    *,
    burst_coupling: float = 0.65,
) -> float:
    return float(flux_turbulence * (1.0 + burst_coupling * burst_strength))


def _lorentz_perturbation(
    t: float,
    layer_idx: int,
    n_orbs: int,
    *,
    burst_strength: float,
    turbulence: float,
    perturbation_strength: float,
) -> tuple[float, float]:
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
    kappa_coupling: float = 0.0,
    flux_floor: float | None = None,
) -> float:
    """Variable solar-wind-like driver (primary modulator)."""
    floor = FLUX_SPRING_CONFIG["flux_floor"] if flux_floor is None else float(flux_floor)
    if stable_mode:
        flux = base + residual_weight * R
    else:
        flux = base + amplitude * np.sin(2.0 * np.pi * freq * t) + residual_weight * R
    if kappa_coupling:
        flux *= 1.0 + kappa_coupling * (KAPPA_DOC - E_OVER_PI)
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
    """Minimal two-orb interaction — outer compression + gauge coupling."""
    cfg = _merge_flux_spring_config(
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
    outer_compression = max(0.55, 1.0 - compression_strength * excess_flux)
    coupling = base_coupling * (0.7 + 0.5 * effective_rigidness)
    return {
        "outer_compression": float(outer_compression),
        "coupling": float(coupling),
        "effective_rigidness": effective_rigidness,
        "excess_flux": float(excess_flux),
    }


def _global_pointer_deg(flux_value: float, spring: dict[str, float], *, t: float = 0.0) -> float:
    push = spring["outer_compression"]
    pull = spring["coupling"] * (float(flux_value) - push)
    wobble = 0.12 * spring["effective_rigidness"] * np.sin(2.0 * np.pi * 0.01 * t)
    return float(np.degrees(np.arctan2(pull + wobble, push - 1.0)) % 360.0)


def _nested_orb_physics(
    flux_value: float,
    n_orbs: int,
    *,
    t: float = 0.0,
    stable_outer_shield: bool | None = None,
    **config_overrides: Any,
) -> dict[str, Any]:
    """N-orb extension of flux_spring — radius factors + twist blend per orb."""
    cfg = _merge_flux_spring_config(**config_overrides)
    spring = flux_spring(flux_value, **cfg)
    n = max(1, int(n_orbs))
    stable_shield = _STABLE_OUTER_SHIELD if stable_outer_shield is None else bool(stable_outer_shield)

    burst = _wg_burst_envelope(t)
    burst_strength = float(burst["strength"])
    turb_base = float(cfg["flux_turbulence"])
    turb_eff = _effective_flux_turbulence(turb_base, burst_strength)
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
        radius_factors[idx] = compression ** (
            exposure * (1.0 + 0.5 * (n - 1 - idx) / max(1, n - 1))
        )
        if idx < n - 1:
            slack = max(0.0, 1.0 - compression)
            radius_factors[idx] *= 1.0 + emergent * coupling * slack * (1.0 - exposure)

    for idx in range(1, n):
        pair_exposure = idx / max(1, n - 1)
        twist_blend[idx] = float(
            np.clip(twist_base * coupling * rigid * (0.5 + 0.5 * pair_exposure), 0.0, 0.95)
        )

    for idx in range(n):
        r_off, t_off = _lorentz_perturbation(
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

    pointer = _global_pointer_deg(flux_value, spring, t=t)
    return {
        "radius_factors": radius_factors,
        "twist_blend": twist_blend,
        "twist_perturbations": twist_perturbations,
        "global_pointer_deg": pointer,
        "spring": spring,
        "flux_turbulence_effective": turb_eff,
        "burst_strength": burst_strength,
        "burst_active": bool(burst["active"]),
        "outer_spiral_twist": outer_spiral_twist,
    }


def _blended_twist(
    twist: float,
    sign: int,
    t: float,
    flux: float,
    lag: float,
    *,
    twist_blend: float,
    inner_twist: tuple[float, float, float] | None,
) -> tuple[float, float, float]:
    freq = twist * flux
    rz = freq * t + lag * sign
    ry = -0.5 * sign * freq * t
    rx = 0.25 * freq * np.sin(0.3 * t)
    if inner_twist is not None and twist_blend > 0.0:
        irx, iry, irz = inner_twist
        blend = float(np.clip(twist_blend, 0.0, 0.95))
        rx = irx * blend + rx * (1.0 - blend)
        ry = iry * blend + ry * (1.0 - blend)
        rz = irz * blend + rz * (1.0 - blend)
    return float(rx), float(ry), float(rz)


def _generate_geodesic_sphere(frequency: int = _GEODESIC_OUTER_FREQUENCY) -> tuple[np.ndarray, list[tuple[int, ...]]]:
    """Geodesic sphere — render-only; physics topology unchanged."""
    freq = max(0, int(frequency))
    if freq in _GEODESIC_MESH_CACHE:
        return _GEODESIC_MESH_CACHE[freq]

    verts, faces = _icosahedron_topology()
    vert_list = [tuple(v) for v in np.asarray(verts, dtype=float)]
    face_list = [tuple(int(x) for x in f) for f in faces]
    cache: dict[tuple[int, int], int] = {}

    def _key(a: int, b: int) -> tuple[int, int]:
        return (a, b) if a < b else (b, a)

    def _project(row: np.ndarray) -> tuple[float, float, float]:
        norm = max(float(np.linalg.norm(row)), 1e-12)
        return (float(row[0] / norm), float(row[1] / norm), float(row[2] / norm))

    def _midpoint(i: int, j: int) -> int:
        k = _key(i, j)
        if k in cache:
            return cache[k]
        mid = _project((np.asarray(vert_list[i]) + np.asarray(vert_list[j])) * 0.5)
        idx = len(vert_list)
        vert_list.append(mid)
        cache[k] = idx
        return idx

    for _ in range(freq):
        next_faces: list[tuple[int, int, int]] = []
        for a, b, c in face_list:
            ab = _midpoint(a, b)
            bc = _midpoint(b, c)
            ca = _midpoint(c, a)
            next_faces.extend([(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)])
        face_list = next_faces

    vert_array = np.asarray(vert_list, dtype=float)
    norms = np.maximum(np.linalg.norm(vert_array, axis=1, keepdims=True), 1e-12)
    result = (vert_array / norms, face_list)
    _GEODESIC_MESH_CACHE[freq] = result
    return result


def _icosahedron_topology():
    tau = (1.0 + np.sqrt(5.0)) / 2.0
    vertices = [
        (-1.0, tau, 0.0), (1.0, tau, 0.0), (-1.0, -tau, 0.0), (1.0, -tau, 0.0),
        (0.0, -1.0, tau), (0.0, 1.0, tau), (0.0, -1.0, -tau), (0.0, 1.0, -tau),
        (tau, 0.0, -1.0), (tau, 0.0, 1.0), (-tau, 0.0, -1.0), (-tau, 0.0, 1.0),
    ]
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]
    return vertices, faces


def _platonic_topology(name: str):
    solid = name.lower()
    if solid == "tetrahedron":
        v = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
        f = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]
    elif solid == "octahedron":
        v = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        f = [(4, 2, 0), (4, 0, 3), (4, 3, 1), (4, 1, 2), (5, 0, 2), (5, 3, 0), (5, 1, 3), (5, 2, 1)]
    elif solid == "cube":
        v = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
        f = [(4, 5, 6, 7), (0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 7, 6), (0, 4, 7, 3), (1, 2, 6, 5)]
    elif solid == "icosahedron":
        v, f = _icosahedron_topology()
    else:
        v, f = _icosahedron_topology()
        vert = np.asarray(v, float)
        dual_v = [tuple(vert[list(face)].mean(axis=0)) for face in f]
        v, f = dual_v, f
    arr = np.asarray(v, float)
    arr /= max(abs(arr).max(), 1e-12)
    return arr, f


def _rotation_matrix(rx, ry, rz):
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    rx_m = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry_m = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz_m = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz_m @ ry_m @ rx_m


_LAYERS = (
    ("tetrahedron", 0.22, 1.20, "#e63946", 1),
    ("octahedron", 0.38, 0.85, "#457b9d", -1),
    ("cube", 0.55, 0.62, "#c9a227", 1),
    ("icosahedron", 0.72, 0.45, "#2a9d8f", -1),
    ("dodecahedron", 0.90, 0.30, "#9b5de5", 1),
)


def _wireframe_edges(faces):
    seen, edges = set(), []
    for face in faces:
        for i in range(len(face)):
            a, b = face[i], face[(i + 1) % len(face)]
            key = (min(a, b), max(a, b))
            if key not in seen:
                seen.add(key)
                edges.append(key)
    return edges


def _hand_xy(deg: float, length: float) -> tuple[float, float]:
    rad = np.radians(90.0 - deg)
    return float(length * np.cos(rad)), float(length * np.sin(rad))


def _gauged_hour_angle(t: float, wind: float) -> float:
    return float(np.degrees(((2.0 * np.pi / W_G) * wind * t) % (2.0 * np.pi)))


def _gauged_minute_angle(t: float, wind: float) -> float:
    return float(np.degrees(((2.0 * np.pi * 12.0 / W_G) * wind * t) % (2.0 * np.pi)))


def _integrate_effective(times: np.ndarray, **kwargs) -> np.ndarray:
    winds = np.array([brackish_dynamics(t, **kwargs) for t in times])
    dt = float(times[1] - times[0]) if len(times) > 1 else 1.0
    return np.cumsum(winds) * dt


def _angle_delta_deg(clock_deg: float, effective_deg: float) -> float:
    """Shortest angular separation on the clock manifold."""
    return float(abs((clock_deg - effective_deg + 180.0) % 360.0 - 180.0))


def _brackish_render_kwargs(**kwargs: Any) -> dict[str, Any]:
    keys = (
        "base",
        "amplitude",
        "freq",
        "residual_weight",
        "stable_mode",
        "visual_separation",
        "flux_gauge_rigidness",
        "compression_strength",
        "base_coupling",
        "flux_influence_on_rigidness",
        "inner_emergent_expansion",
        "twist_coupling_blend",
    )
    return {k: kwargs.get(k, DEFAULT_BRACKISH_PARAMS[k]) for k in keys}


def _brackish_physics_kwargs(**kwargs: Any) -> dict[str, Any]:
    return {
        k: kwargs.get(k, DEFAULT_BRACKISH_PARAMS[k])
        for k in ("base", "amplitude", "freq", "residual_weight", "stable_mode")
    }


def _flux_spring_kwargs(**kwargs: Any) -> dict[str, float]:
    return {
        k: float(kwargs.get(k, DEFAULT_BRACKISH_PARAMS[k]))
        for k in (
            "flux_gauge_rigidness",
            "compression_strength",
            "base_coupling",
            "flux_influence_on_rigidness",
            "inner_emergent_expansion",
            "twist_coupling_blend",
            "flux_turbulence",
        )
    }


def _build_sync_series(times: np.ndarray, **kwargs) -> dict[str, Any]:
    """Precompute clock, resonator wind, and divergence tracks for frame-synced animation."""
    params = _brackish_render_kwargs(**kwargs)
    physics = _brackish_physics_kwargs(**kwargs)
    winds = np.array([brackish_flux(float(t), **physics) for t in times])
    clock = np.array([_gauged_hour_angle(float(t), float(w)) for t, w in zip(times, winds)])
    effective = np.degrees(_integrate_effective(times, **physics) % (2.0 * np.pi))
    delta_inst = np.array([_angle_delta_deg(c, e) for c, e in zip(clock, effective)])
    idx = np.arange(1, len(times) + 1)
    divergence_mean = np.cumsum(delta_inst) / idx
    return {
        "times": times,
        "duration": float(times[-1]) if len(times) else 0.0,
        "winds": winds,
        "clock": clock,
        "effective": effective,
        "delta_inst": delta_inst,
        "divergence_mean": divergence_mean,
        **params,
    }


def _series_index_at_t(series: dict[str, Any], t: float) -> int:
    times = series["times"]
    if len(times) == 0:
        return 0
    return int(np.argmin(np.abs(times - float(t))))


def _wireframe_edge_color_hex(
    edge_index: int,
    total_edges: int,
    *,
    layer_index: int = 0,
    t_along: float = 0.5,
) -> str:
    """Gold → rainbow gradient — matches Demo B platonic wireframe aesthetic."""
    span = (edge_index + layer_index * 0.06 + float(t_along) * 0.35) / max(1.0, float(total_edges))
    hue = 0.11 + span * 0.78
    red, green, blue = colorsys.hsv_to_rgb(hue % 1.0, 0.92, 1.0)
    return f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"


def _hide_3d_scene_axes(ax) -> None:
    """Hide panes/ticks — pure black viewport like Demo B."""
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_zlabel("")
    ax.grid(False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor((0.0, 0.0, 0.0, 0.0))
        axis.pane.set_alpha(0.0)
        axis._axinfo["grid"].update({"linewidth": 0})
        axis.line.set_color((0.0, 0.0, 0.0, 0.0))
        axis.set_tick_params(
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labeltop=False,
            labelleft=False,
            labelright=False,
        )


def _nested_layer_vertices(
    t: float,
    wind: float,
    *,
    viewport_scale: float = 1.0,
    visual_separation: float | None = None,
    spring_config: dict[str, float] | None = None,
) -> list[tuple[np.ndarray, list[tuple[int, ...]], int]]:
    """Transformed vertices per shell — (verts, faces, layer_index)."""
    flux = float(wind)
    lag = 0.08 * R * flux
    breath_sync = np.sin(2.0 * np.pi * 0.5 * t + flux)
    spring_cfg = _merge_flux_spring_config(**(spring_config or {}))
    physics = _nested_orb_physics(flux, len(_LAYERS), t=t, **spring_cfg)
    turb_eff = float(physics["flux_turbulence_effective"])
    layers: list[tuple[np.ndarray, list[tuple[int, ...]], int]] = []
    inner_twist: tuple[float, float, float] | None = None
    outer_idx = len(_LAYERS) - 1
    for layer_idx, (name, radius, twist, _color, sign) in enumerate(_LAYERS):
        is_outer_shield = _USE_GEODESIC_OUTER and layer_idx == outer_idx
        if is_outer_shield:
            verts, faces = _generate_geodesic_sphere(_GEODESIC_OUTER_FREQUENCY)
        else:
            verts, faces = _platonic_topology(name)
        if is_outer_shield and _STABLE_OUTER_SHIELD:
            breath = 1.0 + 0.008 * flux * np.sin(2.0 * np.pi * 0.5 * t)
        else:
            breath = 1.0 + 0.14 * (1.0 + turb_eff) * flux**2 * breath_sync
        scale = radius * physics["radius_factors"][layer_idx] * breath
        rx, ry, rz = _blended_twist(
            twist,
            sign,
            t,
            flux,
            lag,
            twist_blend=physics["twist_blend"][layer_idx],
            inner_twist=inner_twist,
        )
        rz += physics["twist_perturbations"][layer_idx]
        if is_outer_shield:
            spiral = float(physics["outer_spiral_twist"])
            rz += spiral
            ry += 0.35 * spiral
            rx += 0.15 * np.sin(spiral)
        rot = _rotation_matrix(rx, ry, rz)
        physics_verts = (rot @ (verts * scale).T).T
        inner_twist = (rx, ry, rz)
        visual_mult = _visual_render_multiplier(
            name,
            radius,
            layer_index=layer_idx,
            visual_separation=visual_separation,
        )
        layers.append((physics_verts * visual_mult * viewport_scale, faces, layer_idx))
    return layers


def _draw_zero_point_clock(ax, t: float, wind: float, effective_deg: float, *, stable_mode: bool):
    ax.set_facecolor("#0a0a0f")
    ax.set_aspect("equal")
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, color="#555", lw=1.4))
    ax.plot([0, 0], [0, 1.08], color="#c9a227", lw=2.8, zorder=6, solid_capstyle="round")
    for hour in range(1, 13):
        angle = np.radians(90 - hour * 30)
        x, y = np.cos(angle), np.sin(angle)
        is_369 = hour in (3, 6, 9, 12)
        ax.plot([0.88 * x, x], [0.88 * y, y], color="#e63946" if is_369 else "#444", lw=1.0 if is_369 else 0.6)
        if hour % 3 == 0:
            ax.text(1.14 * x, 1.14 * y, str(hour), ha="center", va="center", fontsize=7, color="#e63946" if is_369 else "#888")

    hour_deg = _gauged_hour_angle(t, wind)
    minute_deg = _gauged_minute_angle(t, wind)
    eff_deg = float(effective_deg % 360.0)

    for deg, length, color, lw, ls, label in (
        (hour_deg, 0.50, "#c9a227", 3.0, "-", "hour"),
        (minute_deg, 0.72, "#f4d35e", 1.4, "-", "minute"),
        (eff_deg, 0.62, "#9b5de5", 1.8, (0, (4, 3)), "effective"),
    ):
        hx, hy = _hand_xy(deg, length)
        ax.plot([0, hx], [0, hy], color=color, lw=lw, ls=ls, solid_capstyle="round", zorder=5)

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.axis("off")
    mode = "Stable" if stable_mode else "Dynamic"
    ax.set_title(f"Gauged clock ({mode}) · wind={wind:.2f}", fontsize=9, color="#ddd", pad=4)
    ax.text(
        -1.25, -1.18,
        "gold=hour · thin gold=minute · purple dashed=∫wind",
        fontsize=6.5, color="#888",
    )


def _draw_divergence_strip_live(ax, series: dict[str, Any], frame_idx: int, wind: float) -> None:
    """Row 2 — clock, ∫wind, and running mean |Δ| grow in sync with the animation."""
    ax.set_facecolor(_VIEWPORT_BG)
    end = min(frame_idx + 1, len(series["times"]))
    if end < 1:
        return
    sl = slice(0, end)
    times = series["times"][sl]
    clock = series["clock"][sl]
    effective = series["effective"][sl]
    div_mean = series["divergence_mean"][sl]

    ax.plot(times, clock, color="#c9a227", lw=1.3, label="clock", zorder=3)
    ax.plot(times, effective, color="#9b5de5", lw=1.1, ls="--", label="∫wind", zorder=3)
    ax.plot(times, div_mean, color="#2ec4b6", lw=1.4, label="mean |Δ|", zorder=4)
    ax.fill_between(times, clock, effective, alpha=0.10, color="#457b9d", zorder=1)

    ax.scatter(times[-1], clock[-1], color="#c9a227", s=18, zorder=6, edgecolors="white", linewidths=0.3)
    ax.scatter(times[-1], effective[-1], color="#9b5de5", s=18, zorder=6, edgecolors="white", linewidths=0.3)
    ax.scatter(times[-1], div_mean[-1], color="#2ec4b6", s=18, zorder=6, edgecolors="white", linewidths=0.3)

    current_mean = float(div_mean[-1])
    ax.set_title(
        f"Divergence · mean |Δ|={current_mean:.1f}° · wind={wind:.2f}",
        fontsize=8,
        color="#ccc",
    )
    ax.set_xlim(0.0, max(series["duration"], 0.5))
    y_vals = np.concatenate([clock, effective, div_mean])
    y_pad = max(12.0, 0.08 * (float(y_vals.max()) - float(y_vals.min()) + 1.0))
    ax.set_ylim(float(y_vals.min()) - y_pad, float(y_vals.max()) + y_pad)
    ax.tick_params(colors="#777", labelsize=6)
    ax.set_xlabel("t", fontsize=7, color="#777")
    ax.set_ylabel("°", fontsize=7, color="#777")
    for spine in ax.spines.values():
        spine.set_color("#333")
    ax.grid(True, alpha=0.15, color="#444")
    ax.legend(loc="upper right", fontsize=6, framealpha=0.3)


def _configure_resonator_axes(
    ax,
    *,
    t: float,
    viewport_scale: float,
    visual_separation: float | None,
    full_viewport: bool,
    quad_panel: bool = False,
) -> None:
    visual_scales = _visual_radius_scales(visual_separation)
    max_visual_r = max(visual_scales.values())
    lim_factor = _QUAD_LIM_FACTOR if quad_panel else 1.28
    lim = max_visual_r * viewport_scale * lim_factor
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    elev = _VIEWPORT_ELEV if full_viewport else 22.0
    azim = (_VIEWPORT_AZIM if full_viewport else 38.0) + 0.35 * t
    ax.view_init(elev=elev, azim=azim)
    _hide_3d_scene_axes(ax)


def _plot_resonator_layer_edges(
    ax,
    verts: np.ndarray,
    faces: list[tuple[int, ...]],
    *,
    layer_idx: int,
    edge_color: str,
    linewidth: float,
    alpha: float,
    zorder: int,
) -> None:
    for i0, i1 in _wireframe_edges(faces):
        p0, p1 = verts[i0], verts[i1]
        ax.plot(
            [p0[0], p1[0]],
            [p0[1], p1[1]],
            [p0[2], p1[2]],
            color=edge_color,
            linewidth=linewidth,
            solid_capstyle="round",
            alpha=alpha,
            zorder=zorder,
        )


def _draw_nested_resonator(
    ax,
    t: float,
    wind: float,
    *,
    layers: list[tuple[np.ndarray, list[tuple[int, ...]], int]] | None = None,
    viewport_scale: float = 1.0,
    visual_separation: float | None = None,
    full_viewport: bool = False,
    color_mode: str = "layer",
    highlight_layer_idx: int | None = None,
    panel_label: str | None = None,
) -> None:
    """Nested Platonic wireframe — full color, rainbow, or single-layer highlight."""
    ax.set_facecolor(_VIEWPORT_BG)
    if layers is None:
        layers = _nested_layer_vertices(
            t,
            wind,
            viewport_scale=viewport_scale,
            visual_separation=visual_separation,
        )
    n_layers = max(1, len(_LAYERS))
    base_line_w = 2.6 if full_viewport else 1.8
    base_line_w *= 0.85 + 0.15 * min(1.3, wind / 1.2)
    if highlight_layer_idx is not None:
        for verts, faces, layer_idx in layers:
            name, _radius, _twist, layer_color, _sign = _LAYERS[layer_idx]
            is_highlight = layer_idx == highlight_layer_idx
            if is_highlight:
                edge_color = layer_color
                line_w = _DIMMED_LINE_WIDTH
                line_alpha = 1.0
                zorder = 20 + layer_idx
            else:
                edge_color = _DIMMED_LINE_COLOR
                line_w = _DIMMED_LINE_WIDTH
                line_alpha = _DIMMED_LINE_ALPHA
                zorder = 5 + layer_idx
            _plot_resonator_layer_edges(
                ax,
                verts,
                faces,
                layer_idx=layer_idx,
                edge_color=edge_color,
                linewidth=line_w,
                alpha=line_alpha,
                zorder=zorder,
            )
        if panel_label:
            _name, _radius, _twist, accent, _sign = _LAYERS[highlight_layer_idx]
            ax.text2D(
                0.5,
                0.03,
                f"{panel_label} · {_name.title()}",
                transform=ax.transAxes,
                ha="center",
                va="bottom",
                fontsize=6,
                color=accent,
                zorder=30,
            )
    else:
        use_rainbow = str(color_mode).strip().lower() == "rainbow"
        total_edges = max(
            1,
            sum(len(_wireframe_edges(faces)) for _, faces, _ in layers),
        )
        edge_idx = 0
        for verts, faces, layer_idx in layers:
            _name, _radius, _twist, layer_color, _sign = _LAYERS[layer_idx]
            depth = layer_idx / max(1, n_layers - 1)
            line_w = base_line_w * (0.96 + 0.12 * depth)
            line_alpha = 0.90 + 0.10 * depth
            for i0, i1 in _wireframe_edges(faces):
                p0, p1 = verts[i0], verts[i1]
                if use_rainbow:
                    edge_color = _wireframe_edge_color_hex(
                        edge_idx, total_edges, layer_index=layer_idx,
                    )
                else:
                    edge_color = layer_color
                ax.plot(
                    [p0[0], p1[0]],
                    [p0[1], p1[1]],
                    [p0[2], p1[2]],
                    color=edge_color,
                    linewidth=line_w,
                    solid_capstyle="round",
                    alpha=line_alpha,
                    zorder=5 + layer_idx,
                )
                edge_idx += 1
        if not full_viewport:
            ax.set_title("Nested resonator · wind-synced twist/breath", fontsize=9, color="#ddd", pad=4)

    _configure_resonator_axes(
        ax,
        t=t,
        viewport_scale=viewport_scale,
        visual_separation=visual_separation,
        full_viewport=full_viewport,
        quad_panel=highlight_layer_idx is not None,
    )


def build_brackish_quad_viewport(
    t: float,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    visual_separation: float = DEFAULT_BRACKISH_PARAMS["visual_separation"],
    dpi: int = 88,
    **spring_overrides: Any,
) -> plt.Figure:
    """Demo J — 2×2 synced resonator panels with per-quadrant layer highlight."""
    render = _brackish_render_kwargs(
        base=base,
        amplitude=amplitude,
        freq=freq,
        residual_weight=residual_weight,
        stable_mode=stable_mode,
        visual_separation=visual_separation,
        **spring_overrides,
    )
    wind = brackish_flux(t, **_brackish_physics_kwargs(**render))
    spring_config = _flux_spring_kwargs(**render)
    layers = _nested_layer_vertices(
        t,
        wind,
        viewport_scale=_QUAD_VIEWPORT_SCALE,
        visual_separation=visual_separation,
        spring_config=spring_config,
    )
    fig = plt.figure(figsize=_QUAD_VIEWPORT_FIGSIZE, facecolor=_VIEWPORT_BG, dpi=dpi)
    gs = GridSpec(
        2,
        2,
        figure=fig,
        wspace=0.0,
        hspace=0.0,
        left=0.0,
        right=1.0,
        top=1.0,
        bottom=0.0,
    )
    for row, col, layer_idx, panel_label in _DEMO_J_QUAD_PANELS:
        ax = fig.add_subplot(gs[row, col], projection="3d", facecolor=_VIEWPORT_BG)
        _draw_nested_resonator(
            ax,
            t,
            wind,
            layers=layers,
            viewport_scale=_QUAD_VIEWPORT_SCALE,
            visual_separation=visual_separation,
            full_viewport=True,
            highlight_layer_idx=layer_idx,
            panel_label=panel_label,
        )
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0, wspace=0.0, hspace=0.0)
    return fig


def build_brackish_resonator_viewport(
    t: float,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    visual_separation: float = DEFAULT_BRACKISH_PARAMS["visual_separation"],
    dpi: int = 88,
    **spring_overrides: Any,
) -> plt.Figure:
    """Full-viewport nested resonator — alias for Demo J 2×2 quad layout."""
    return build_brackish_quad_viewport(
        t,
        base=base,
        amplitude=amplitude,
        freq=freq,
        residual_weight=residual_weight,
        stable_mode=stable_mode,
        visual_separation=visual_separation,
        dpi=dpi,
        **spring_overrides,
    )


def build_brackish_sync_frame(
    frame_idx: int,
    series: dict[str, Any],
    *,
    dpi: int = 90,
) -> plt.Figure:
    """
    Synchronized Demo J frame:
    row 1 — gauged clock (col 1) + rainbow nested resonator (col 2)
    row 2 — live divergence chart (mean |Δ| grows with animation)
    """
    idx = int(np.clip(frame_idx, 0, len(series["times"]) - 1))
    t_val = float(series["times"][idx])
    wind = float(series["winds"][idx])
    effective_deg = float(series["effective"][idx])
    stable_mode = bool(series["stable_mode"])

    fig = plt.figure(figsize=(11.5, 6.0), facecolor=_VIEWPORT_BG, dpi=dpi)
    gs = GridSpec(2, 2, figure=fig, height_ratios=[3.0, 1.25], width_ratios=[1, 1], hspace=0.30, wspace=0.10)
    ax_clock = fig.add_subplot(gs[0, 0])
    ax_3d = fig.add_subplot(gs[0, 1], projection="3d")
    ax_div = fig.add_subplot(gs[1, :])

    _draw_zero_point_clock(ax_clock, t_val, wind, effective_deg, stable_mode=stable_mode)
    _draw_nested_resonator(
        ax_3d, t_val, wind,
        viewport_scale=1.18,
        visual_separation=series.get("visual_separation", DEFAULT_BRACKISH_PARAMS["visual_separation"]),
        full_viewport=False,
    )
    _draw_divergence_strip_live(ax_div, series, idx, wind)

    fig.suptitle(
        f"Brackish heartbeat · W_g={W_G:.2f} · R={R:+.4f} · κ={KAPPA_DOC}",
        fontsize=10,
        color="#ddd",
        y=0.98,
    )
    fig.subplots_adjust(top=0.92, bottom=0.06, left=0.04, right=0.98)
    return fig


def build_brackish_dashboard(
    t: float | None = None,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    visual_separation: float = DEFAULT_BRACKISH_PARAMS["visual_separation"],
    dpi: int = 90,
    duration: float = 8.0,
) -> plt.Figure:
    """Static snapshot of the synced dashboard at time t."""
    t_val = 6.0 if t is None else float(t)
    times = np.linspace(0.0, max(duration, t_val), max(40, int(max(duration, t_val) * 10)))
    series = _build_sync_series(
        times,
        base=base,
        amplitude=amplitude,
        freq=freq,
        residual_weight=residual_weight,
        stable_mode=stable_mode,
        visual_separation=visual_separation,
    )
    return build_brackish_sync_frame(_series_index_at_t(series, t_val), series, dpi=dpi)


def _figure_to_png_bytes(
    fig: plt.Figure,
    *,
    dpi: int,
    fill_frame: bool = False,
) -> bytes:
    buf = io.BytesIO()
    save_kwargs: dict[str, Any] = {
        "format": "png",
        "dpi": dpi,
        "facecolor": fig.get_facecolor(),
        "edgecolor": "none",
    }
    if fill_frame:
        save_kwargs["bbox_inches"] = None
        save_kwargs["pad_inches"] = 0
    else:
        save_kwargs["bbox_inches"] = "tight"
        save_kwargs["pad_inches"] = 0.05
    fig.savefig(buf, **save_kwargs)
    plt.close(fig)
    return buf.getvalue()


def _figure_to_rgb(fig: plt.Figure, *, dpi: int, fill_frame: bool = False) -> np.ndarray:
    from PIL import Image

    data = _figure_to_png_bytes(fig, dpi=dpi, fill_frame=fill_frame)
    img = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
    h, w = img.shape[:2]
    return img[: h - h % 2, : w - w % 2]


def _render_kwargs(**kwargs: Any) -> dict[str, Any]:
    allowed = {
        "t", "base", "amplitude", "freq", "residual_weight", "stable_mode",
        "visual_separation", "dpi",
    }
    return {k: v for k, v in kwargs.items() if k in allowed}


def brackish_resonator_to_data_uri(**kwargs: Any) -> str:
    """Base64 data URI for Gradio HTML viewport — resonator only."""
    render = _render_kwargs(**kwargs)
    t_val = float(render.get("t", 6.0))
    fig = build_brackish_resonator_viewport(t_val, **render)
    png = _figure_to_png_bytes(
        fig,
        dpi=int(render.get("dpi", _QUAD_RENDER_DPI)),
        fill_frame=True,
    )
    encoded = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def brackish_dashboard_to_data_uri(**kwargs: Any) -> str:
    """Backward-compatible alias — Demo J viewport is resonator-only."""
    return brackish_resonator_to_data_uri(**kwargs)


def brackish_dashboard_viewport_html(**kwargs: Any) -> str:
    """HF-safe viewport HTML for interactive Demo J preview — resonator only."""
    render = _render_kwargs(**kwargs)
    uri = brackish_resonator_to_data_uri(**render)
    title = "Demo J — 2×2 Platonic Resonator"
    subtitle = (
        f"wind base={kwargs.get('base', 1.0):.2f} · "
        f"amp={kwargs.get('amplitude', 0.4):.2f} · "
        f"sep={kwargs.get('visual_separation', DEFAULT_BRACKISH_PARAMS['visual_separation']):.2f}"
    )
    return (
        f'<div class="myst-gravity-viewport-inner myst-gravity-demo-j">'
        f'<div class="myst-gravity-viewport-title">{title}</div>'
        f'<div class="myst-gravity-viewport-sub">{subtitle}</div>'
        f'<img class="myst-brackish-dashboard-img" src="{uri}" '
        f'alt="Nested Platonic resonator" style="width:100%;max-width:960px;border-radius:8px;" />'
        f"</div>"
    )


def _encode_mp4(frames: list[np.ndarray], fps: int) -> str:
    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="myst-brackish-") as tmp_dir:
        tmp = Path(tmp_dir)
        for idx, frame in enumerate(frames):
            Image.fromarray(frame).save(tmp / f"frame_{idx:05d}.png")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as out:
            mp4_path = out.name
        subprocess.run(
            [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(tmp / "frame_%05d.png"),
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-pix_fmt", "yuv420p", "-c:v", "libx264", "-movflags", "+faststart",
                mp4_path,
            ],
            check=True,
            capture_output=True,
        )
    return mp4_path


def render_brackish_clock_video(
    *,
    duration: float = 8.0,
    fps: int = 10,
    dpi: int = 72,
    **kwargs: Any,
) -> str:
    """Looping MP4 — 2×2 synced Platonic resonator panels (Demo J)."""
    render = _brackish_render_kwargs(**kwargs)
    n_frames = max(2, int(duration * fps))
    times = np.linspace(0, duration, n_frames)
    encode_dpi = max(int(kwargs.get("dpi", dpi)), _QUAD_RENDER_DPI)
    rgb_frames = []
    for t_val in times:
        fig = build_brackish_resonator_viewport(float(t_val), dpi=encode_dpi, **render)
        rgb_frames.append(_figure_to_rgb(fig, dpi=encode_dpi, fill_frame=True))
    path = _encode_mp4(rgb_frames, fps=fps)
    print(f"[brackish] render_brackish_clock_video: {len(rgb_frames)} frames -> {path}", flush=True)
    return path


# Backward-compatible alias used during initial Demo J rollout.
def build_brackish_frame(t: float, effective: float, **kwargs) -> plt.Figure:
    return build_brackish_dashboard(t=t, **kwargs)