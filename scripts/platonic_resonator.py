"""Platonic solid topology, rotation, twist, and breathing for nested resonator animations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from geodesic import (
    GEODESIC_OUTER_FREQUENCY,
    STABLE_OUTER_SHIELD,
    USE_GEODESIC_OUTER,
    generate_geodesic_sphere,
)

SOLID_NAMES = ("tetrahedron", "octahedron", "cube", "icosahedron", "dodecahedron")
FACE_COUNTS = {"tetrahedron": 4, "octahedron": 8, "cube": 6, "icosahedron": 20, "dodecahedron": 12}

# === VISUAL ONLY — does not affect twist, counter-twist, or breathing math ===
# Tight nesting: stay inside outer geodesic even with inner breathing/turbulence.
DEFAULT_VISUAL_SCALES: dict[str, float] = {
    "tetrahedron": 0.22,
    "octahedron": 0.36,
    "cube": 0.50,
    "icosahedron": 0.64,
    "dodecahedron": 0.92,
}
DEFAULT_VISUAL_SEPARATION = 0.16


def _polyhedron_dual(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vert_array = np.asarray(vertices, dtype=float)
    dual_vertices = [tuple(vert_array[list(face)].mean(axis=0)) for face in faces]
    vert_faces: list[list[int]] = [[] for _ in range(len(vertices))]
    for fi, face in enumerate(faces):
        for vi in face:
            vert_faces[vi].append(fi)

    dual_faces: list[tuple[int, ...]] = []
    for vi, adjacent in enumerate(vert_faces):
        if len(adjacent) < 3:
            continue
        center = vert_array[vi]
        normal = center / max(np.linalg.norm(center), 1e-12)
        ref = np.array([1.0, 0.0, 0.0])
        if abs(float(np.dot(normal, ref))) > 0.9:
            ref = np.array([0.0, 1.0, 0.0])
        tangent_a = np.cross(normal, ref)
        tangent_a /= max(np.linalg.norm(tangent_a), 1e-12)
        tangent_b = np.cross(normal, tangent_a)
        angles: list[tuple[float, int]] = []
        for fi in adjacent:
            delta = np.asarray(dual_vertices[fi]) - center
            angle = float(np.arctan2(np.dot(delta, tangent_b), np.dot(delta, tangent_a)))
            angles.append((angle, fi))
        angles.sort(key=lambda item: item[0])
        dual_faces.append(tuple(fi for _, fi in angles))
    return dual_vertices, dual_faces


def _icosahedron_topology() -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    tau = (1.0 + np.sqrt(5.0)) / 2.0
    vertices = [
        (-1.0, tau, 0.0),
        (1.0, tau, 0.0),
        (-1.0, -tau, 0.0),
        (1.0, -tau, 0.0),
        (0.0, -1.0, tau),
        (0.0, 1.0, tau),
        (0.0, -1.0, -tau),
        (0.0, 1.0, -tau),
        (tau, 0.0, -1.0),
        (tau, 0.0, 1.0),
        (-tau, 0.0, -1.0),
        (-tau, 0.0, 1.0),
    ]
    faces = [
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1),
    ]
    return vertices, faces


def platonic_topology(name: str) -> tuple[np.ndarray, list[tuple[int, ...]]]:
    """Return unit-scale vertices and face index loops for a named Platonic solid."""
    solid = str(name).strip().lower()
    if solid == "tetrahedron":
        vertices = [(1.0, 1.0, 1.0), (1.0, -1.0, -1.0), (-1.0, 1.0, -1.0), (-1.0, -1.0, 1.0)]
        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]
    elif solid == "octahedron":
        vertices = [
            (1.0, 0.0, 0.0),
            (-1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, -1.0),
        ]
        faces = [
            (4, 2, 0),
            (4, 0, 3),
            (4, 3, 1),
            (4, 1, 2),
            (5, 0, 2),
            (5, 3, 0),
            (5, 1, 3),
            (5, 2, 1),
        ]
    elif solid == "cube":
        vertices = [
            (-1.0, -1.0, -1.0),
            (1.0, -1.0, -1.0),
            (1.0, 1.0, -1.0),
            (-1.0, 1.0, -1.0),
            (-1.0, -1.0, 1.0),
            (1.0, -1.0, 1.0),
            (1.0, 1.0, 1.0),
            (-1.0, 1.0, 1.0),
        ]
        faces = [
            (4, 5, 6, 7),
            (0, 3, 2, 1),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (0, 4, 7, 3),
            (1, 2, 6, 5),
        ]
    elif solid == "icosahedron":
        raw_vertices, faces = _icosahedron_topology()
        vertices = raw_vertices
    elif solid == "dodecahedron":
        raw_vertices, faces = _polyhedron_dual(*_icosahedron_topology())
        vertices = raw_vertices
    else:
        raise ValueError(f"unknown Platonic solid: {name}")
    vert_array = np.asarray(vertices, dtype=float)
    max_abs = max(abs(c) for vtx in vert_array for c in vtx)
    if max_abs > 1e-12:
        vert_array = vert_array / max_abs
    return vert_array, faces


def rotation_matrix_xyz(rx: float, ry: float, rz: float) -> np.ndarray:
    """Compose intrinsic rotations about x, y, z axes."""
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    rx_mat = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=float)
    ry_mat = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=float)
    rz_mat = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=float)
    return rz_mat @ ry_mat @ rx_mat


def breathing_scale(
    t: float,
    wind: float,
    depth: float = 0.12,
    *,
    turbulence: float = 0.0,
    is_outer_shield: bool = False,
) -> float:
    """Radius oscillation — turbulence scales inner breathing; outer shield stays nearly fixed."""
    if is_outer_shield and STABLE_OUTER_SHIELD:
        return 1.0 + 0.008 * wind * np.sin(2.0 * np.pi * 0.5 * t)
    eff_depth = depth * (1.0 + turbulence)
    return 1.0 + eff_depth * (wind**2) * np.sin(2.0 * np.pi * 0.5 * t + wind)


def visual_radius_scales(visual_separation: float | None = None) -> dict[str, float]:
    """Absolute render radii per shell — frontend spacing only."""
    if visual_separation is None or abs(float(visual_separation) - DEFAULT_VISUAL_SEPARATION) < 1e-9:
        return dict(DEFAULT_VISUAL_SCALES)
    inner = DEFAULT_VISUAL_SCALES["tetrahedron"]
    sep = float(visual_separation)
    return {name: inner + idx * sep for idx, name in enumerate(SOLID_NAMES)}


def visual_render_multiplier(
    layer_name: str,
    base_radius: float,
    *,
    layer_index: int | None = None,
    visual_separation: float | None = None,
) -> float:
    """Scale physics vertices to visual radius without changing backend geometry."""
    scales = visual_radius_scales(visual_separation)
    visual_radius = scales.get(layer_name, base_radius)
    return visual_radius / max(float(base_radius), 1e-12)


def apply_visual_layer_scale(vertices: np.ndarray, multiplier: float) -> np.ndarray:
    """Element-wise radius remap for plotting — preserves rotation and breathing phase."""
    return vertices * float(multiplier)


@dataclass
class ResonatorLayer:
    """One concentric Platonic shell in the nested heartbeat."""

    name: str
    base_radius: float
    base_twist_freq: float
    harmonic_factor: float = 1.0
    color: str = "#5eb3ff"
    alpha: float = 0.55
    counter_twist_sign: int = 1

    def twist_angles(self, t: float, flux: float, residual_lag: float) -> tuple[float, float, float]:
        """Rotation + counter-twist driven by brackish_flux."""
        freq = self.base_twist_freq * flux * self.harmonic_factor
        lag = residual_lag * self.counter_twist_sign
        rz = freq * t + lag
        ry = -0.5 * self.counter_twist_sign * freq * t
        rx = 0.25 * freq * np.sin(0.3 * t)
        return float(rx), float(ry), float(rz)

    def blended_twist_angles(
        self,
        t: float,
        flux: float,
        residual_lag: float,
        *,
        twist_blend: float = 0.0,
        inner_twist: tuple[float, float, float] | None = None,
    ) -> tuple[float, float, float]:
        rx, ry, rz = self.twist_angles(t, flux, residual_lag)
        if inner_twist is not None and twist_blend > 0.0:
            irx, iry, irz = inner_twist
            blend = float(np.clip(twist_blend, 0.0, 0.95))
            rx = irx * blend + rx * (1.0 - blend)
            ry = iry * blend + ry * (1.0 - blend)
            rz = irz * blend + rz * (1.0 - blend)
        return float(rx), float(ry), float(rz)

    def transformed_vertices(
        self,
        t: float,
        flux: float,
        residual_lag: float,
        *,
        radius_factor: float = 1.0,
        twist_blend: float = 0.0,
        inner_twist: tuple[float, float, float] | None = None,
        geodesic_frequency: int | None = None,
        turbulence: float = 0.0,
        twist_perturbation: float = 0.0,
        outer_spiral_twist: float = 0.0,
    ) -> tuple[np.ndarray, list[tuple[int, ...]]]:
        if geodesic_frequency is not None:
            verts, faces = generate_geodesic_sphere(geodesic_frequency)
        else:
            verts, faces = platonic_topology(self.name)
        is_outer_shield = geodesic_frequency is not None
        scale = (
            self.base_radius
            * float(radius_factor)
            * breathing_scale(
                t,
                flux,
                turbulence=turbulence,
                is_outer_shield=is_outer_shield,
            )
        )
        rx, ry, rz = self.blended_twist_angles(
            t, flux, residual_lag, twist_blend=twist_blend, inner_twist=inner_twist,
        )
        rz += float(twist_perturbation)
        if is_outer_shield and outer_spiral_twist:
            rz += float(outer_spiral_twist)
            ry += 0.35 * float(outer_spiral_twist)
            rx += 0.15 * np.sin(float(outer_spiral_twist))
        rot = rotation_matrix_xyz(rx, ry, rz)
        return (rot @ (verts * scale).T).T, faces


DEFAULT_LAYERS: tuple[ResonatorLayer, ...] = (
    ResonatorLayer("tetrahedron", 0.22, 1.20, harmonic_factor=1.0, color="#e63946", counter_twist_sign=1),
    ResonatorLayer("octahedron", 0.38, 0.85, harmonic_factor=np.e / np.pi, color="#457b9d", counter_twist_sign=-1),
    ResonatorLayer("cube", 0.55, 0.62, harmonic_factor=(1 + np.sqrt(5)) / 2, color="#c9a227", counter_twist_sign=1),
    ResonatorLayer("icosahedron", 0.72, 0.45, harmonic_factor=np.pi / np.e, color="#2a9d8f", counter_twist_sign=-1),
    ResonatorLayer("dodecahedron", 0.90, 0.30, harmonic_factor=1.618, color="#9b5de5", counter_twist_sign=1),
)


def transform_nested_orbs(
    layers: list[ResonatorLayer],
    t: float,
    flux: float,
    residual_lag: float,
    physics: Any,
) -> list[tuple[np.ndarray, list[tuple[int, ...]]]]:
    """Apply flux_spring radius + twist coupling across nested orbs."""
    results: list[tuple[np.ndarray, list[tuple[int, ...]]]] = []
    inner_twist: tuple[float, float, float] | None = None
    n_layers = len(layers)
    for idx, layer in enumerate(layers):
        geo_freq = (
            GEODESIC_OUTER_FREQUENCY
            if USE_GEODESIC_OUTER and idx == n_layers - 1
            else None
        )
        verts, faces = layer.transformed_vertices(
            t,
            flux,
            residual_lag,
            radius_factor=physics.radius_factors[idx],
            twist_blend=physics.twist_blend[idx],
            inner_twist=inner_twist,
            geodesic_frequency=geo_freq,
            turbulence=getattr(physics, "flux_turbulence_effective", 0.0),
            twist_perturbation=(
                physics.twist_perturbations[idx]
                if getattr(physics, "twist_perturbations", None)
                else 0.0
            ),
            outer_spiral_twist=(
                physics.outer_spiral_twist
                if geo_freq is not None
                else 0.0
            ),
        )
        results.append((verts, faces))
        inner_twist = layer.blended_twist_angles(
            t,
            flux,
            residual_lag,
            twist_blend=physics.twist_blend[idx],
            inner_twist=inner_twist,
        )
    return results


def active_layers(
    solids: Iterable[str] | None = None,
) -> list[ResonatorLayer]:
    """Filter default nested shells by name."""
    if solids is None:
        return list(DEFAULT_LAYERS)
    wanted = {s.strip().lower() for s in solids}
    return [layer for layer in DEFAULT_LAYERS if layer.name in wanted]


def wireframe_edges(faces: list[tuple[int, ...]]) -> list[tuple[int, int]]:
    """Unique undirected edges for face loops."""
    seen: set[tuple[int, int]] = set()
    edges: list[tuple[int, int]] = []
    for face in faces:
        for i in range(len(face)):
            a, b = face[i], face[(i + 1) % len(face)]
            key = (min(a, b), max(a, b))
            if key not in seen:
                seen.add(key)
                edges.append(key)
    return edges