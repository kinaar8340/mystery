#!/usr/bin/env python3
"""
Gauged clock + brackish_dynamics-modulated nested Platonic solids heartbeat.

Combines the stable zero-point manifold (W_g-scaled clock, 3-6-9 axis) with
variable wind (brackish_dynamics) driving twist, counter-twist, and breathing
of concentric Platonic shells.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report
from hopf_constant_bridge import W_G
from platonic_resonator import DEFAULT_LAYERS, ResonatorLayer, active_layers, wireframe_edges
from vortex_369_clock import digital_root, map_angles_to_369_tens

R = PHI**2 + E**2 - PI**2
KAPPA_DOC = 0.85


def brackish_dynamics(
    t: float,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    kappa: float = KAPPA_DOC,
    kappa_coupling: float = 0.0,
) -> float:
    """
    Modulating 'wind' — base + slow sinusoid + persistent residual influence.

    stable_mode forces near-constant wind for baseline comparisons.
    """
    if stable_mode:
        wind = base + residual_weight * R
        return max(0.1, float(wind))

    wind = base + amplitude * np.sin(2.0 * np.pi * freq * t)
    wind += residual_weight * R
    if kappa_coupling:
        wind *= 1.0 + kappa_coupling * (kappa - E / PI)
    return max(0.1, float(wind))


def integrate_effective_time(
    times: np.ndarray,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
) -> np.ndarray:
    """Cumulative integral of brackish_dynamics — the non-linear progress track."""
    winds = np.array(
        [
            brackish_dynamics(
                t,
                base=base,
                amplitude=amplitude,
                freq=freq,
                residual_weight=residual_weight,
                stable_mode=stable_mode,
            )
            for t in times
        ]
    )
    return np.cumsum(winds) * (times[1] - times[0] if len(times) > 1 else 1.0)


def gauged_clock_angle(t: float, wind: float) -> float:
    """Clock hand angle (degrees) — steady W_g ticks modulated by instantaneous wind."""
    tick_rate = (2.0 * np.pi / W_G) * wind
    return float(np.degrees((tick_rate * t) % (2.0 * np.pi)))


def draw_zero_point_manifold(ax: plt.Axes, mapping: dict) -> None:
    """Fixed unit circle + 12 o'clock zero-point + 3-6-9 axis markers."""
    ax.set_aspect("equal")
    circle = plt.Circle((0, 0), 1, fill=False, color="#333", lw=1.5)
    ax.add_patch(circle)
    ax.plot([0, 0], [0, 1.05], color="#c9a227", lw=2.5, zorder=5, label="zero-point")
    for hour in (3, 6, 9):
        angle_rad = np.radians(90 - hour * 30)
        x, y = np.cos(angle_rad), np.sin(angle_rad)
        ax.plot([0, x], [0, y], color="#e63946", alpha=0.5, lw=1.2)
        ax.text(1.12 * x, 1.12 * y, str(hour), ha="center", va="center", fontsize=9, color="#e63946")
    for label, key, color in (
        ("φ", "phi", "#e63946"),
        ("e", "e", "#457b9d"),
        ("π", "pi", "#2a9d8f"),
    ):
        tens = mapping[key]["tens_unit"]
        angle_deg = 90 - tens * 10.0
        rad = np.radians(angle_deg)
        ax.plot(
            [0, 0.85 * np.cos(rad)],
            [0, 0.85 * np.sin(rad)],
            color=color,
            lw=1.0,
            alpha=0.7,
        )
        ax.text(
            0.95 * np.cos(rad),
            0.95 * np.sin(rad),
            label,
            ha="center",
            va="center",
            fontsize=8,
            color=color,
        )
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.axis("off")
    ax.set_title("Zero-point manifold\n(W_g gauged · 3-6-9 axis)", fontsize=9)


def draw_clock_hands(ax: plt.Axes, clock_deg: float, effective_deg: float) -> None:
    """Steady clock hand vs integrated effective-time hand."""
    for deg, color, label in (
        (clock_deg, "#c9a227", "clock"),
        (effective_deg, "#9b5de5", "effective"),
    ):
        rad = np.radians(90 - deg)
        ax.plot(
            [0, 0.75 * np.cos(rad)],
            [0, 0.75 * np.sin(rad)],
            color=color,
            lw=2.0 if label == "clock" else 1.5,
            alpha=0.9 if label == "clock" else 0.65,
            linestyle="-" if label == "clock" else "--",
        )


def draw_nested_resonator(
    ax: Axes3D,
    t: float,
    wind: float,
    layers: list[ResonatorLayer],
    *,
    elev: float = 22.0,
    azim: float = 38.0,
) -> None:
    """Render wireframe Platonic shells with twist, counter-twist, breathing."""
    ax.cla()
    residual_lag = 0.08 * R * wind
    for layer in layers:
        verts, faces = layer.transformed_vertices(t, wind, residual_lag)
        for i0, i1 in wireframe_edges(faces):
            p0, p1 = verts[i0], verts[i1]
            ax.plot(
                [p0[0], p1[0]],
                [p0[1], p1[1]],
                [p0[2], p1[2]],
                color=layer.color,
                alpha=layer.alpha,
                lw=0.9,
            )
    lim = max(layer.base_radius for layer in layers) * 1.25
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim + 0.4 * t)
    ax.set_axis_off()
    ax.set_title(f"Nested resonator · wind={wind:.3f}", fontsize=9, pad=2)


def plot_long_horizon(
    *,
    horizon: float = 500.0,
    n_points: int = 400,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
) -> Path:
    """Divergence between clock time and effective-time track."""
    times = np.linspace(0, horizon, n_points)
    clock_angles = np.array([gauged_clock_angle(t, brackish_dynamics(t, base=base, amplitude=amplitude, freq=freq, residual_weight=residual_weight, stable_mode=stable_mode)) for t in times])
    effective = integrate_effective_time(times, base=base, amplitude=amplitude, freq=freq, residual_weight=residual_weight, stable_mode=stable_mode)
    effective_angles = np.degrees(effective % (2.0 * np.pi))

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, clock_angles, color="#c9a227", lw=1.5, label="clock (W_g gauged)")
    ax.plot(times, effective_angles, color="#9b5de5", lw=1.2, ls="--", label="effective track (∫wind)")
    ax.fill_between(times, clock_angles, effective_angles, alpha=0.12, color="#457b9d")
    ax.set_xlabel("t")
    ax.set_ylabel("angle (deg)")
    mode = "stable" if stable_mode else "dynamic"
    ax.set_title(f"Long-horizon divergence ({mode}) · R={R:+.4f}")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    out = OUTPUT_DIR / "brackish_long_horizon.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def build_animation(
    *,
    duration: float = 12.0,
    fps: int = 12,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    solids: list[str] | None = None,
) -> tuple[FuncAnimation, plt.Figure, list[float], list[float]]:
    """Build matplotlib FuncAnimation for clock + nested solids."""
    layers = active_layers(solids)
    mapping = map_angles_to_369_tens()
    n_frames = max(2, int(duration * fps))
    times = np.linspace(0, duration, n_frames)
    effective = integrate_effective_time(
        times,
        base=base,
        amplitude=amplitude,
        freq=freq,
        residual_weight=residual_weight,
        stable_mode=stable_mode,
    )

    fig = plt.figure(figsize=(12, 5.5), facecolor="#0a0a0f")
    ax_clock = fig.add_subplot(121)
    ax_3d = fig.add_subplot(122, projection="3d")
    draw_zero_point_manifold(ax_clock, mapping)

    winds: list[float] = []
    clock_angles: list[float] = []

    def update(frame_idx: int):
        t = float(times[frame_idx])
        wind = brackish_dynamics(
            t,
            base=base,
            amplitude=amplitude,
            freq=freq,
            residual_weight=residual_weight,
            stable_mode=stable_mode,
        )
        winds.append(wind)
        clock_deg = gauged_clock_angle(t, wind)
        clock_angles.append(clock_deg)
        eff_deg = float(np.degrees(effective[frame_idx] % (2.0 * np.pi)))
        ax_clock.cla()
        draw_zero_point_manifold(ax_clock, mapping)
        draw_clock_hands(ax_clock, clock_deg, eff_deg)
        ax_clock.text(
            -1.25,
            -1.25,
            f"t={t:.1f}s  wind={wind:.3f}",
            fontsize=8,
            color="#aaa",
        )
        draw_nested_resonator(ax_3d, t, wind, layers)
        return ()

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    mode = "Stable" if stable_mode else "Dynamic"
    fig.suptitle(
        f"Brackish heartbeat ({mode}) · W_g={W_G:.3f} · R={R:+.4f}",
        fontsize=11,
        color="#ddd",
    )
    fig.tight_layout()
    return anim, fig, winds, clock_angles


def save_animation_gif(
    anim: FuncAnimation,
    path: Path,
    *,
    fps: int = 12,
) -> Path:
    writer = PillowWriter(fps=fps)
    anim.save(path, writer=writer)
    return path


def save_animation_mp4(anim: FuncAnimation, path: Path, *, fps: int = 12) -> Path | None:
    try:
        anim.save(path, writer="ffmpeg", fps=fps, dpi=120)
        return path
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Brackish clock + nested Platonic heartbeat")
    parser.add_argument("--duration", type=float, default=12.0)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--base", type=float, default=1.0, help="base wind")
    parser.add_argument("--amplitude", type=float, default=0.4)
    parser.add_argument("--freq", type=float, default=0.01)
    parser.add_argument("--residual-weight", type=float, default=0.15)
    parser.add_argument("--stable", action="store_true", help="stable conditions mode")
    parser.add_argument("--horizon", type=float, default=500.0, help="long-horizon plot span")
    parser.add_argument("--no-gif", action="store_true")
    parser.add_argument("--mp4", action="store_true")
    parser.add_argument(
        "--solids",
        nargs="*",
        default=None,
        help="active shells (default: all five)",
    )
    args = parser.parse_args(argv)

    mapping = map_angles_to_369_tens()
    layers = active_layers(args.solids)
    long_path = plot_long_horizon(
        horizon=args.horizon,
        base=args.base,
        amplitude=args.amplitude,
        freq=args.freq,
        residual_weight=args.residual_weight,
        stable_mode=args.stable,
    )

    anim, fig, winds, clock_angles = build_animation(
        duration=args.duration,
        fps=args.fps,
        base=args.base,
        amplitude=args.amplitude,
        freq=args.freq,
        residual_weight=args.residual_weight,
        stable_mode=args.stable,
        solids=args.solids,
    )

    gif_path = OUTPUT_DIR / "brackish_clock.gif"
    mp4_path = OUTPUT_DIR / "brackish_clock.mp4"
    static_path = OUTPUT_DIR / "brackish_clock.png"

    if not args.no_gif:
        save_animation_gif(anim, gif_path, fps=args.fps)
    if args.mp4:
        save_animation_mp4(anim, mp4_path, fps=args.fps)

    # Save a representative static frame
    fig.savefig(static_path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)

    result = {
        "constants": {
            "W_g": float(W_G),
            "R": float(R),
            "kappa_doc": KAPPA_DOC,
            "phi": float(PHI),
            "e": float(E),
            "pi": float(PI),
        },
        "brackish_dynamics": {
            "base": args.base,
            "amplitude": args.amplitude,
            "freq": args.freq,
            "residual_weight": args.residual_weight,
            "stable_mode": args.stable,
            "formula": "max(0.1, base + amp*sin(2π·freq·t) + residual_weight·R)",
        },
        "phi_e_pi_369_mapping": mapping,
        "active_solids": [layer.name for layer in layers],
        "animation": {
            "duration_s": args.duration,
            "fps": args.fps,
            "mean_wind": float(np.mean(winds)) if winds else None,
            "gif": str(gif_path) if not args.no_gif else None,
            "mp4": str(mp4_path) if args.mp4 else None,
            "static_frame": str(static_path),
            "long_horizon_plot": str(long_path),
        },
        "interpretation": (
            "Zero-point manifold = fixed gauged reference; brackish_dynamics = variable wind; "
            "nested Platonic shells = living heartbeat response; effective-time track diverges "
            "from W_g clock over long horizons when wind varies."
        ),
    }
    report_path = save_report("brackish_clock", result)

    print("=== Brackish Clock / Nested Resonator ===")
    print(f"W_g = {W_G:.6f}  (350/π)")
    print(f"R   = {R:+.8f}")
    print(f"Mode: {'stable' if args.stable else 'dynamic'}")
    print(f"Active solids: {[l.name for l in layers]}")
    print(f"Mean wind: {np.mean(winds):.4f}" if winds else "")
    print(f"Long horizon: {long_path}")
    if not args.no_gif:
        print(f"GIF:   {gif_path}")
    print(f"Frame: {static_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())