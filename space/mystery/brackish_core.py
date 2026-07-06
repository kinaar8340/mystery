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
    "visual_separation": 0.40,
}

# === VISUAL ONLY — does not affect twist, counter-twist, or breathing math ===
_DEFAULT_VISUAL_SCALES: dict[str, float] = {
    "tetrahedron": 0.32,
    "octahedron": 0.72,
    "cube": 1.12,
    "icosahedron": 1.52,
    "dodecahedron": 1.92,
}
_DEFAULT_VISUAL_SEPARATION = 0.40
_SOLID_ORDER = ("tetrahedron", "octahedron", "cube", "icosahedron", "dodecahedron")

_VIEWPORT_BG = "#0a0a0f"
_VIEWPORT_FIGSIZE = (6.0, 6.0)
_VIEWPORT_ELEV = 26.0
_VIEWPORT_AZIM = 45.0
_NESTED_VIEWPORT_SCALE = 1.42


def brackish_params_key(**kwargs: Any) -> str:
    """Cache key for rendered media."""
    return "|".join(
        f"{k}={kwargs.get(k, DEFAULT_BRACKISH_PARAMS.get(k))!r}"
        for k in ("base", "amplitude", "freq", "residual_weight", "stable_mode", "visual_separation")
    )


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


def brackish_dynamics(
    t: float,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    kappa_coupling: float = 0.0,
) -> float:
    if stable_mode:
        wind = base + residual_weight * R
    else:
        wind = base + amplitude * np.sin(2.0 * np.pi * freq * t) + residual_weight * R
    if kappa_coupling:
        wind *= 1.0 + kappa_coupling * (KAPPA_DOC - E_OVER_PI)
    return max(0.1, float(wind))


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
    return {
        k: kwargs.get(k, DEFAULT_BRACKISH_PARAMS[k])
        for k in ("base", "amplitude", "freq", "residual_weight", "stable_mode", "visual_separation")
    }


def _brackish_physics_kwargs(**kwargs: Any) -> dict[str, Any]:
    return {
        k: kwargs.get(k, DEFAULT_BRACKISH_PARAMS[k])
        for k in ("base", "amplitude", "freq", "residual_weight", "stable_mode")
    }


def _build_sync_series(times: np.ndarray, **kwargs) -> dict[str, Any]:
    """Precompute clock, resonator wind, and divergence tracks for frame-synced animation."""
    params = _brackish_render_kwargs(**kwargs)
    physics = _brackish_physics_kwargs(**kwargs)
    winds = np.array([brackish_dynamics(float(t), **physics) for t in times])
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
) -> list[tuple[np.ndarray, list[tuple[int, ...]], int]]:
    """Transformed vertices per shell — (verts, faces, layer_index)."""
    lag = 0.08 * R * wind
    breath_sync = np.sin(2.0 * np.pi * 0.5 * t + wind)
    layers: list[tuple[np.ndarray, list[tuple[int, ...]], int]] = []
    for layer_idx, (name, radius, twist, _color, sign) in enumerate(_LAYERS):
        verts, faces = _platonic_topology(name)
        scale = radius * (1.0 + 0.14 * wind**2 * breath_sync)
        freq = twist * wind
        rot = _rotation_matrix(
            0.25 * freq * np.sin(0.3 * t),
            -0.5 * sign * freq * t,
            freq * t + lag * sign,
        )
        physics_verts = (rot @ (verts * scale).T).T
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


def _draw_nested_resonator(
    ax,
    t: float,
    wind: float,
    *,
    viewport_scale: float = 1.0,
    visual_separation: float | None = None,
    full_viewport: bool = False,
) -> None:
    """Rainbow nested Platonic wireframe — Demo B aesthetic."""
    ax.set_facecolor(_VIEWPORT_BG)
    layers = _nested_layer_vertices(
        t,
        wind,
        viewport_scale=viewport_scale,
        visual_separation=visual_separation,
    )
    segments: list[tuple[np.ndarray, np.ndarray, int]] = []
    for verts, faces, layer_idx in layers:
        for i0, i1 in _wireframe_edges(faces):
            segments.append((verts[i0], verts[i1], layer_idx))
    total_edges = max(1, len(segments))
    n_layers = max(1, len(_LAYERS))
    base_line_w = 2.6 if full_viewport else 1.8
    base_line_w *= 0.85 + 0.15 * min(1.3, wind / 1.2)
    for edge_idx, (p0, p1, layer_idx) in enumerate(segments):
        depth = layer_idx / max(1, n_layers - 1)
        ax.plot(
            [p0[0], p1[0]],
            [p0[1], p1[1]],
            [p0[2], p1[2]],
            color=_wireframe_edge_color_hex(edge_idx, total_edges, layer_index=layer_idx),
            linewidth=base_line_w * (0.94 + 0.10 * depth),
            solid_capstyle="round",
            alpha=0.88 + 0.12 * depth,
            zorder=5 + layer_idx,
        )
    visual_scales = _visual_radius_scales(visual_separation)
    max_visual_r = max(visual_scales.values())
    lim = max_visual_r * viewport_scale * 1.28
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    elev = _VIEWPORT_ELEV if full_viewport else 22.0
    azim = (_VIEWPORT_AZIM if full_viewport else 38.0) + 0.35 * t
    ax.view_init(elev=elev, azim=azim)
    _hide_3d_scene_axes(ax)
    if not full_viewport:
        ax.set_title("Nested resonator · wind-synced twist/breath", fontsize=9, color="#ddd", pad=4)


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
) -> plt.Figure:
    """Full-viewport nested resonator loop frame — matches Demo B wireframe look."""
    wind = brackish_dynamics(
        t, base=base, amplitude=amplitude, freq=freq,
        residual_weight=residual_weight, stable_mode=stable_mode,
    )
    fig = plt.figure(figsize=_VIEWPORT_FIGSIZE, facecolor=_VIEWPORT_BG, dpi=dpi)
    ax = fig.add_subplot(111, projection="3d", facecolor=_VIEWPORT_BG)
    _draw_nested_resonator(
        ax, t, wind,
        viewport_scale=_NESTED_VIEWPORT_SCALE,
        visual_separation=visual_separation,
        full_viewport=True,
    )
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    return fig


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


def _figure_to_png_bytes(fig: plt.Figure, *, dpi: int) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def _figure_to_rgb(fig: plt.Figure, *, dpi: int) -> np.ndarray:
    from PIL import Image

    data = _figure_to_png_bytes(fig, dpi=dpi)
    img = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
    h, w = img.shape[:2]
    return img[: h - h % 2, : w - w % 2]


def _render_kwargs(**kwargs: Any) -> dict[str, Any]:
    allowed = {
        "t", "base", "amplitude", "freq", "residual_weight", "stable_mode",
        "visual_separation", "dpi",
    }
    return {k: v for k, v in kwargs.items() if k in allowed}


def brackish_dashboard_to_data_uri(**kwargs: Any) -> str:
    """Base64 data URI for Gradio HTML viewport."""
    fig = build_brackish_dashboard(**_render_kwargs(**kwargs))
    png = _figure_to_png_bytes(fig, dpi=int(kwargs.get("dpi", 88)))
    encoded = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def brackish_dashboard_viewport_html(**kwargs: Any) -> str:
    """HF-safe viewport HTML for interactive Demo J preview."""
    render = _render_kwargs(**kwargs)
    uri = brackish_dashboard_to_data_uri(**render)
    title = "Demo J — Brackish Heartbeat"
    subtitle = (
        f"base={kwargs.get('base', 1.0):.2f} · "
        f"amp={kwargs.get('amplitude', 0.4):.2f} · "
        f"freq={kwargs.get('freq', 0.01):.3f} · "
        f"R_wt={kwargs.get('residual_weight', 0.15):.2f}"
    )
    return (
        f'<div class="myst-gravity-viewport-inner myst-gravity-demo-j">'
        f'<div class="myst-gravity-viewport-title">{title}</div>'
        f'<div class="myst-gravity-viewport-sub">{subtitle}</div>'
        f'<img class="myst-brackish-dashboard-img" src="{uri}" '
        f'alt="Brackish heartbeat dashboard" style="width:100%;max-width:960px;border-radius:8px;" />'
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
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    visual_separation: float = DEFAULT_BRACKISH_PARAMS["visual_separation"],
) -> str:
    """Looping MP4 — clock + rainbow resonator + live divergence chart (frame-synced)."""
    n_frames = max(2, int(duration * fps))
    times = np.linspace(0, duration, n_frames)
    series = _build_sync_series(
        times,
        base=base,
        amplitude=amplitude,
        freq=freq,
        residual_weight=residual_weight,
        stable_mode=stable_mode,
        visual_separation=visual_separation,
    )
    rgb_frames = []
    for frame_idx in range(n_frames):
        fig = build_brackish_sync_frame(frame_idx, series, dpi=dpi)
        rgb_frames.append(_figure_to_rgb(fig, dpi=dpi))
    path = _encode_mp4(rgb_frames, fps=fps)
    print(f"[brackish] render_brackish_clock_video: {len(rgb_frames)} frames -> {path}", flush=True)
    return path


# Backward-compatible alias used during initial Demo J rollout.
def build_brackish_frame(t: float, effective: float, **kwargs) -> plt.Figure:
    return build_brackish_dashboard(t=t, **kwargs)