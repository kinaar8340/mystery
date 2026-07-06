"""Geodesic sphere mesh — render-only; physics uses Platonic topology unchanged."""

from __future__ import annotations

import numpy as np

# === VISUAL ONLY ===
USE_GEODESIC_OUTER = True
STABLE_OUTER_SHIELD = True
# 1-frequency: clean wireframe (~80 faces). 3-frequency reads as solid diffusion.
GEODESIC_OUTER_FREQUENCY = 1

_MESH_CACHE: dict[int, tuple[np.ndarray, list[tuple[int, ...]]]] = {}


def _icosahedron_base() -> tuple[np.ndarray, list[tuple[int, int, int]]]:
    tau = (1.0 + np.sqrt(5.0)) / 2.0
    vertices = np.asarray(
        [
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
        ],
        dtype=float,
    )
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
    vertices /= np.maximum(np.linalg.norm(vertices, axis=1, keepdims=True), 1e-12)
    return vertices, faces


def _project_unit(vertices: np.ndarray) -> np.ndarray:
    out = np.asarray(vertices, dtype=float)
    norms = np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)
    return out / norms


def generate_geodesic_sphere(
    frequency: int = GEODESIC_OUTER_FREQUENCY,
) -> tuple[np.ndarray, list[tuple[int, ...]]]:
    """
    Geodesic sphere from icosahedron + midpoint subdivision.

    frequency = subdivision passes (0 = icosahedron, 1 = light geodesic, 3 = dense).
    Returns unit-radius vertices and triangular faces.
    """
    freq = max(0, int(frequency))
    if freq in _MESH_CACHE:
        return _MESH_CACHE[freq]

    verts, faces = _icosahedron_base()
    vert_list = [tuple(v) for v in verts]
    face_list = [tuple(f) for f in faces]
    cache: dict[tuple[int, int], int] = {}

    def _key(a: int, b: int) -> tuple[int, int]:
        return (a, b) if a < b else (b, a)

    def _midpoint(i: int, j: int) -> int:
        k = _key(i, j)
        if k in cache:
            return cache[k]
        mid_vec = (np.asarray(vert_list[i]) + np.asarray(vert_list[j])) * 0.5
        norm = max(float(np.linalg.norm(mid_vec)), 1e-12)
        mid = tuple((mid_vec / norm).tolist())
        idx = len(vert_list)
        vert_list.append(tuple(mid))
        cache[k] = idx
        return idx

    for _ in range(freq):
        next_faces: list[tuple[int, int, int]] = []
        for a, b, c in face_list:
            ab = _midpoint(a, b)
            bc = _midpoint(b, c)
            ca = _midpoint(c, a)
            next_faces.extend(
                [
                    (a, ab, ca),
                    (b, bc, ab),
                    (c, ca, bc),
                    (ab, bc, ca),
                ]
            )
        face_list = next_faces

    vert_array = _project_unit(np.asarray(vert_list, dtype=float))
    result = (vert_array, face_list)
    _MESH_CACHE[freq] = result
    return result