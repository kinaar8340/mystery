"""Brackish clock + nested Platonic heartbeat — HF Space rendering (self-contained)."""

from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

PHI = (1.0 + np.sqrt(5.0)) / 2.0
E = np.e
PI = np.pi
R = PHI**2 + E**2 - PI**2
W_G = 350.0 / PI
KAPPA_DOC = 0.85


def brackish_dynamics(
    t: float,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
) -> float:
    if stable_mode:
        return max(0.1, float(base + residual_weight * R))
    wind = base + amplitude * np.sin(2.0 * np.pi * freq * t) + residual_weight * R
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


def _gauged_clock_angle(t: float, wind: float) -> float:
    return float(np.degrees(((2.0 * np.pi / W_G) * wind * t) % (2.0 * np.pi)))


def _integrate_effective(times, **kwargs):
    winds = np.array([brackish_dynamics(t, **kwargs) for t in times])
    dt = times[1] - times[0] if len(times) > 1 else 1.0
    return np.cumsum(winds) * dt


def build_brackish_frame(
    t: float,
    effective: float,
    *,
    base: float = 1.0,
    amplitude: float = 0.4,
    freq: float = 0.01,
    residual_weight: float = 0.15,
    stable_mode: bool = False,
    dpi: int = 80,
) -> plt.Figure:
    wind = brackish_dynamics(
        t, base=base, amplitude=amplitude, freq=freq,
        residual_weight=residual_weight, stable_mode=stable_mode,
    )
    clock_deg = _gauged_clock_angle(t, wind)
    eff_deg = float(np.degrees(effective % (2.0 * np.pi)))

    fig = plt.figure(figsize=(10, 4.5), facecolor="#0a0a0f", dpi=dpi)
    ax_c = fig.add_subplot(121)
    ax_3d = fig.add_subplot(122, projection="3d")

    ax_c.set_aspect("equal")
    ax_c.add_patch(plt.Circle((0, 0), 1, fill=False, color="#444", lw=1.2))
    ax_c.plot([0, 0], [0, 1.05], color="#c9a227", lw=2.0)
    for deg, color, ls in ((clock_deg, "#c9a227", "-"), (eff_deg, "#9b5de5", "--")):
        rad = np.radians(90 - deg)
        ax_c.plot([0, 0.7 * np.cos(rad)], [0, 0.7 * np.sin(rad)], color=color, lw=1.8, ls=ls)
    ax_c.set_xlim(-1.2, 1.2)
    ax_c.set_ylim(-1.2, 1.2)
    ax_c.axis("off")
    ax_c.set_title(f"Gauged clock · wind={wind:.2f}", fontsize=8, color="#ccc")

    lag = 0.08 * R * wind
    for name, radius, twist, color, sign in _LAYERS:
        verts, faces = _platonic_topology(name)
        scale = radius * (1.0 + 0.12 * wind**2 * np.sin(2.0 * np.pi * 0.5 * t + wind))
        freq = twist * wind
        rot = _rotation_matrix(0.25 * freq * np.sin(0.3 * t), -0.5 * sign * freq * t, freq * t + lag * sign)
        verts = (rot @ (verts * scale).T).T
        for i0, i1 in _wireframe_edges(faces):
            ax_3d.plot(*zip(verts[i0], verts[i1]), color=color, alpha=0.55, lw=0.7)
    lim = 1.1
    ax_3d.set_xlim(-lim, lim)
    ax_3d.set_ylim(-lim, lim)
    ax_3d.set_zlim(-lim, lim)
    ax_3d.view_init(elev=22, azim=38 + 0.4 * t)
    ax_3d.set_axis_off()
    fig.tight_layout()
    return fig


def _figure_to_rgb(fig: plt.Figure, dpi: int) -> np.ndarray:
    from PIL import Image

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0)
    buf.seek(0)
    img = np.asarray(Image.open(buf).convert("RGB"))
    h, w = img.shape[:2]
    return img[: h - h % 2, : w - w % 2]


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
) -> str:
    """Looping MP4 for Demo J — brackish heartbeat."""
    n_frames = max(2, int(duration * fps))
    times = np.linspace(0, duration, n_frames)
    kwargs = dict(
        base=base, amplitude=amplitude, freq=freq,
        residual_weight=residual_weight, stable_mode=stable_mode,
    )
    effective = _integrate_effective(times, **kwargs)
    rgb_frames = []
    for idx, t in enumerate(times):
        fig = build_brackish_frame(t, effective[idx], dpi=dpi, **kwargs)
        rgb_frames.append(_figure_to_rgb(fig, dpi=dpi))
        plt.close(fig)
    path = _encode_mp4(rgb_frames, fps=fps)
    print(f"[brackish] render_brackish_clock_video: {len(rgb_frames)} frames -> {path}", flush=True)
    return path