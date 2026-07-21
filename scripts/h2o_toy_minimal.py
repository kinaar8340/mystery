#!/usr/bin/env python3
"""
Minimal H₂O toy — three-flywheel trimer with angle constraint.

=============================================================================
  NOT a molecular dynamics model of water. Interpretive: O (Z=8 magic) +
  2×H (Z=1 open) as three coupled quaternion flywheels.
=============================================================================

Geometry modes
  free         no angle potential
  tetrahedral  target ∠H–O–H ≈ 109.47°
  right        target 90°
  linear       target 180°

Constraint modes
  Option A soft    V = (k_θ / 2)(∠ − ∠*)²  — harmonic kicks on H flywheels
  Option B hard    exact geometric projection onto ∠* each step (best for linear)
  hybrid           soft for tetrahedral/right; hard for linear (best-of-both)
  Optional bond    soft O–H length potential on |axis_H − axis_O|

Linear 180° is singular for soft (plane normal vanishes near collinear H's);
hard mode sets H2 anti-aligned with H1 in the O-relative pointer frame.

Standalone small system — reuses quaternion flywheel primitives.

Outputs
  outputs/h2o_toy_minimal.png
  outputs/h2o_toy_minimal_<timestamp>.json

Examples
  python scripts/h2o_toy_minimal.py
  python scripts/h2o_toy_minimal.py                    # default: hybrid
  python scripts/h2o_toy_minimal.py --constraint both  # soft sweep + hard
  python scripts/h2o_toy_minimal.py --bond-stiffness 0.4
  python scripts/h2o_toy_minimal.py --quick
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import OUTPUT_DIR, PI, save_report  # noqa: E402
from flux_hopf_lib.constants import theta_crit as theta_crit_fn  # noqa: E402
from flux_hopf_lib.quaternion.core import q_conj, q_mult, q_normalize, small_rotor  # noqa: E402

# Magic-number / element anchors (kingdom elements lineage — interpretive labels only)
Z_O = 8
Z_H = 1
TETRAHEDRAL_DEG = math.degrees(math.acos(-1.0 / 3.0))  # ≈ 109.471°
GEOMETRY_TARGETS_DEG = {
    "free": None,
    "tetrahedral": TETRAHEDRAL_DEG,
    "right": 90.0,
    "linear": 180.0,
}


# ---------------------------------------------------------------------------
# Vector / angle helpers on flywheel "pointers"
# ---------------------------------------------------------------------------
def pointer_axis(q: np.ndarray) -> np.ndarray:
    """Unit axis from quaternion (vector part); fallback if pure real."""
    v = q[1:4].astype(float)
    n = float(np.linalg.norm(v))
    if n < 1e-10:
        return np.array([0.0, 0.0, 1.0])
    return v / n


def angle_between_deg(a: np.ndarray, b: np.ndarray) -> float:
    c = float(np.clip(np.dot(a, b), -1.0, 1.0))
    return float(np.degrees(np.arccos(c)))


def hoh_angle_deg(q_o: np.ndarray, q_h1: np.ndarray, q_h2: np.ndarray) -> float:
    """
    Angle at oxygen between the two H pointer axes, measured in the plane
    spanned by (H1−O, H2−O) style: angle between unit axes of H1 and H2
    as seen from O's frame (use relative axes).
    """
    o = pointer_axis(q_o)
    h1 = pointer_axis(q_h1)
    h2 = pointer_axis(q_h2)
    # Relative directions from O toward each H in abstract pointer space
    r1 = h1 - o
    r2 = h2 - o
    n1 = float(np.linalg.norm(r1))
    n2 = float(np.linalg.norm(r2))
    if n1 < 1e-10 or n2 < 1e-10:
        # Fallback: direct angle between H axes
        return angle_between_deg(h1, h2)
    r1 = r1 / n1
    r2 = r2 / n2
    return angle_between_deg(r1, r2)


def soft_angle_kick(
    q_o: np.ndarray,
    q_h1: np.ndarray,
    q_h2: np.ndarray,
    *,
    target_deg: float,
    stiffness: float,
    max_kick: float = 0.25,
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Harmonic soft constraint on H–O–H angle.

    V = (k/2)(θ − θ*)² → force ∝ −k (θ − θ*) on the angular separation.
    Applied as equal-and-opposite small rotors on H1 and H2 about the axis
    normal to the HOH plane (Option A).

    Sign convention: if angle > target, kick closes the wedge; if angle < target,
    kick opens it.
    """
    o = pointer_axis(q_o)
    h1 = pointer_axis(q_h1)
    h2 = pointer_axis(q_h2)
    r1 = h1 - o
    r2 = h2 - o
    n1 = float(np.linalg.norm(r1))
    n2 = float(np.linalg.norm(r2))
    if n1 < 1e-10 or n2 < 1e-10:
        # Use H-axis angle directly when O is collinear in pointer space
        ang = angle_between_deg(h1, h2)
        r1u, r2u = h1, h2
    else:
        r1u, r2u = r1 / n1, r2 / n2
        ang = angle_between_deg(r1u, r2u)

    err_rad = math.radians(ang - target_deg)
    # err > 0 (too open) → positive mag closes the wedge (r1→r2, r2→r1)
    # about axis = r1 × r2 by the right-hand rule.
    mag = float(np.clip(stiffness * err_rad, -max_kick, max_kick))
    if abs(mag) < 1e-12:
        return q_h1, q_h2, ang

    axis = np.cross(r1u, r2u)
    an = float(np.linalg.norm(axis))
    if an < 1e-10:
        tmp = np.array([1.0, 0.0, 0.0]) if abs(r1u[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        axis = np.cross(r1u, tmp)
        an = float(np.linalg.norm(axis))
        if an < 1e-10:
            return q_h1, q_h2, ang
    axis = axis / an

    def _apply(q: np.ndarray, half: float) -> np.ndarray:
        return q_normalize(q_mult(small_rotor(half, axis=axis), q))

    q_h1_new = _apply(q_h1, +0.5 * mag)
    q_h2_new = _apply(q_h2, -0.5 * mag)
    return q_h1_new, q_h2_new, ang


def _quat_from_axis(axis: np.ndarray, w: float = 0.0) -> np.ndarray:
    """Build unit quaternion with given real part and vector part ∥ axis."""
    axis = np.asarray(axis, dtype=float)
    n = float(np.linalg.norm(axis))
    if n < 1e-12:
        axis = np.array([0.0, 0.0, 1.0])
        n = 1.0
    axis = axis / n
    w = float(np.clip(w, -0.999, 0.999))
    s = math.sqrt(max(0.0, 1.0 - w * w))
    return q_normalize(np.array([w, *(s * axis)]))


def _relative_dirs(
    q_o: np.ndarray, q_h1: np.ndarray, q_h2: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Return (o_axis, r1u, r2u, angle_deg) with robust fallbacks."""
    o = pointer_axis(q_o)
    h1 = pointer_axis(q_h1)
    h2 = pointer_axis(q_h2)
    r1 = h1 - o
    r2 = h2 - o
    n1 = float(np.linalg.norm(r1))
    n2 = float(np.linalg.norm(r2))
    if n1 < 1e-10 or n2 < 1e-10:
        return o, h1, h2, angle_between_deg(h1, h2)
    r1u, r2u = r1 / n1, r2 / n2
    return o, r1u, r2u, angle_between_deg(r1u, r2u)


def oh_bond_lengths(
    q_o: np.ndarray, q_h1: np.ndarray, q_h2: np.ndarray
) -> tuple[float, float]:
    """Abstract O–H 'bond lengths' = |axis_H − axis_O| in pointer space."""
    o = pointer_axis(q_o)
    h1 = pointer_axis(q_h1)
    h2 = pointer_axis(q_h2)
    return float(np.linalg.norm(h1 - o)), float(np.linalg.norm(h2 - o))


def soft_bond_kick(
    q_o: np.ndarray,
    q_h: np.ndarray,
    *,
    target_len: float,
    stiffness: float,
    max_kick: float = 0.12,
) -> np.ndarray:
    """
    Soft harmonic on O–H length: V = (k_b/2)(|r| − L*)².

    Pulls H pointer axis toward/away from O along the bond direction.
    """
    if stiffness <= 0.0:
        return q_h
    o = pointer_axis(q_o)
    h = pointer_axis(q_h)
    r = h - o
    L = float(np.linalg.norm(r))
    if L < 1e-10:
        # invent a direction
        r = np.array([1.0, 0.0, 0.0])
        L = 1.0
    r_hat = r / L
    err = L - target_len
    # move H along bond: negative err → push out
    step = float(np.clip(-stiffness * err, -max_kick, max_kick))
    h_new = h + step * r_hat
    hn = float(np.linalg.norm(h_new))
    if hn < 1e-10:
        return q_h
    return _quat_from_axis(h_new / hn, w=float(q_h[0]))


def hard_angle_project(
    q_o: np.ndarray,
    q_h1: np.ndarray,
    q_h2: np.ndarray,
    *,
    target_deg: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Option B — exact geometric projection onto target H–O–H angle.

    Keeps the HOH plane (or a stable plane for linear) and resets the
    opening to exactly ∠*. Preserves quaternion real-parts (twist-ish)
    of H1/H2 while rewriting vector parts from projected axes.

    Linear (≈180°): set r2 = −r1 (anti-aligned relative directions).
    """
    o, r1u, r2u, _ang = _relative_dirs(q_o, q_h1, q_h2)
    target = float(target_deg)

    # --- Linear special case (plane normal ill-defined near 180°) ---
    if target >= 175.0:
        # Bisector / H1 direction as the molecular axis
        axis = r1u
        r1_new = axis
        r2_new = -axis
        q_h1_new = _quat_from_axis(o + r1_new, w=float(q_h1[0]))
        q_h2_new = _quat_from_axis(o + r2_new, w=float(q_h2[0]))
        return q_h1_new, q_h2_new, 180.0

    # Plane basis from current HOH (or invent if collinear)
    nrm = np.cross(r1u, r2u)
    nn = float(np.linalg.norm(nrm))
    if nn < 1e-10:
        tmp = np.array([1.0, 0.0, 0.0]) if abs(r1u[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        nrm = np.cross(r1u, tmp)
        nn = float(np.linalg.norm(nrm))
        if nn < 1e-10:
            return q_h1, q_h2, _ang
    nrm = nrm / nn
    # Orthonormal in-plane: e1 along bisector, e2 ⟂ e1
    bis = r1u + r2u
    bn = float(np.linalg.norm(bis))
    if bn < 1e-10:
        e1 = r1u
    else:
        e1 = bis / bn
    e2 = np.cross(nrm, e1)
    e2n = float(np.linalg.norm(e2))
    if e2n < 1e-10:
        return q_h1, q_h2, _ang
    e2 = e2 / e2n

    half = math.radians(target / 2.0)
    r1_new = math.cos(half) * e1 + math.sin(half) * e2
    r2_new = math.cos(half) * e1 - math.sin(half) * e2
    # Reconstruct absolute pointer axes ≈ O + relative dir
    q_h1_new = _quat_from_axis(o + r1_new, w=float(q_h1[0]))
    q_h2_new = _quat_from_axis(o + r2_new, w=float(q_h2[0]))
    ang = hoh_angle_deg(q_o, q_h1_new, q_h2_new)
    return q_h1_new, q_h2_new, ang


# ---------------------------------------------------------------------------
# Trimer dynamics
# ---------------------------------------------------------------------------
# Default abstract O–H length target (pointer-space units, order-1)
DEFAULT_BOND_LEN = 1.0


def resolve_constraint(geometry: str, constraint: str) -> str:
    """
    hybrid = best-of-both: hard for linear (180° singularity), soft otherwise.
    """
    if geometry == "free":
        return "none"
    if constraint == "hybrid":
        return "hard" if geometry == "linear" else "soft"
    return constraint


def run_trimer(
    *,
    geometry: str = "tetrahedral",
    stiffness: float = 0.5,
    constraint: str = "soft",
    bond_stiffness: float = 0.0,
    bond_target: float = DEFAULT_BOND_LEN,
    frames: int = 250,
    kappa: float = 0.85,
    delta_omega: float = 0.008,
    omega_L: float = 0.025,
    # Detuning: O heavier / more locked; H lighter / more open
    omega_scale_O: float = 0.85,
    omega_scale_H: float = 1.15,
    seed: int = 11,
) -> dict:
    """
    Standalone three-flywheel system: indices 0=O, 1=H1, 2=H2.

    constraint:
      "soft"   — Option A harmonic angle kicks (stiffness k)
      "hard"   — Option B exact angle projection each step
      "hybrid" — hard for linear, soft for tetrahedral/right
      "none"   — free geometry
    bond_stiffness:
      soft O–H length potential (0 = off)
    """
    if geometry not in GEOMETRY_TARGETS_DEG:
        raise ValueError(f"geometry must be one of {list(GEOMETRY_TARGETS_DEG)}")
    if constraint not in ("soft", "hard", "hybrid", "none"):
        raise ValueError("constraint must be soft|hard|hybrid|none")
    target = GEOMETRY_TARGETS_DEG[geometry]
    requested = constraint
    constraint = resolve_constraint(geometry, constraint)
    if geometry == "free":
        target = None

    rng = np.random.default_rng(seed)

    # Initial orientations — seed near target if constrained
    q = np.array([q_normalize(rng.standard_normal(4)) for _ in range(3)])
    if target is not None:
        half = math.radians(min(target, 179.0) / 2.0)
        ax = np.array([1.0, 0.0, 0.0])
        q[0] = q_normalize(np.array([1.0, 0.0, 0.0, 0.0]))
        if target >= 175.0:
            # Linear seed: opposite H axes
            q[1] = q_normalize(small_rotor(+0.2, axis=ax))
            q[2] = q_normalize(small_rotor(+0.2 + math.pi, axis=ax))
        else:
            q[1] = q_normalize(small_rotor(+half, axis=ax))
            q[2] = q_normalize(small_rotor(-half, axis=ax))
        for i in range(3):
            noise = q_normalize(rng.standard_normal(4))
            q[i] = q_normalize(0.85 * q[i] + 0.15 * noise)
        if constraint == "hard":
            q[1], q[2], _ = hard_angle_project(q[0], q[1], q[2], target_deg=target)

    identity = q.copy()
    identity0 = identity.copy()
    twist = np.zeros(3)
    t_crit = float(theta_crit_fn(kappa))
    scales = np.array([omega_scale_O, omega_scale_H, omega_scale_H])

    twist_hist: list[float] = []
    angle_hist: list[float] = []
    id_hist: list[float] = []
    total_bursts = 0
    angle_err_acc = 0.0
    last_bonds = (float("nan"), float("nan"))
    bond_err_acc = 0.0

    twist0 = None
    for _ in range(frames):
        # Per-site two-gyro drive (H slightly faster / more open)
        for i in range(3):
            dL = small_rotor(omega_L * scales[i])
            dR = small_rotor((omega_L - delta_omega) * scales[i])
            q[i] = q_normalize(q_mult(q_mult(dL, q[i]), q_conj(dR)))
            twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))

        # Bond-length soft potential (optional molecular feel)
        if bond_stiffness > 0.0:
            q[1] = soft_bond_kick(
                q[0], q[1], target_len=bond_target, stiffness=bond_stiffness
            )
            q[2] = soft_bond_kick(
                q[0], q[2], target_len=bond_target, stiffness=bond_stiffness
            )
            for i in (1, 2):
                twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))

        # Angle constraint after free drive, before gauge
        if target is not None and constraint == "soft" and stiffness > 0.0:
            n_sub = 1 + int(min(4, math.floor(stiffness)))
            ang = hoh_angle_deg(q[0], q[1], q[2])
            for _sub in range(n_sub):
                q[1], q[2], ang = soft_angle_kick(
                    q[0],
                    q[1],
                    q[2],
                    target_deg=target,
                    stiffness=stiffness / n_sub,
                )
            for i in (1, 2):
                twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))
        elif target is not None and constraint == "hard":
            q[1], q[2], ang = hard_angle_project(
                q[0], q[1], q[2], target_deg=target
            )
            for i in (1, 2):
                twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))
        else:
            ang = hoh_angle_deg(q[0], q[1], q[2])

        # Shared gauge damping on mean twist
        avg = float(np.mean(twist) % (2.0 * np.pi))
        ga = -kappa * avg
        grot = np.array([np.cos(ga), 0.0, 0.0, np.sin(ga)])
        for i in range(3):
            q[i] = q_normalize(q_mult(q[i], grot))
            identity[i] = q_normalize(q_mult(identity[i], grot))
            twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))

        # Re-project hard after gauge (keeps molecule rigid under gauge rot)
        if target is not None and constraint == "hard":
            q[1], q[2], ang = hard_angle_project(
                q[0], q[1], q[2], target_deg=target
            )
            for i in (1, 2):
                twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))

        # Bursts
        for i in range(3):
            if twist[i] > t_crit:
                q[i] = q_normalize(0.3 * np.array([1.0, 0.0, 0.0, 0.0]) + 0.7 * q[i])
                twist[i] *= 0.15
                total_bursts += 1
        if target is not None and constraint == "hard":
            q[1], q[2], ang = hard_angle_project(
                q[0], q[1], q[2], target_deg=target
            )
        if bond_stiffness > 0.0:
            q[1] = soft_bond_kick(
                q[0], q[1], target_len=bond_target, stiffness=bond_stiffness
            )
            q[2] = soft_bond_kick(
                q[0], q[2], target_len=bond_target, stiffness=bond_stiffness
            )

        mean_tw = float(np.mean(twist))
        if twist0 is None and mean_tw > 1e-8:
            twist0 = mean_tw
        twist_hist.append(mean_tw)
        angle_hist.append(ang)
        cos = np.abs(np.sum(identity * identity0, axis=1))
        id_hist.append(float(np.mean(cos)))
        if target is not None:
            angle_err_acc += abs(ang - target)
        L1, L2 = oh_bond_lengths(q[0], q[1], q[2])
        last_bonds = (L1, L2)
        if bond_stiffness > 0.0:
            bond_err_acc += 0.5 * (abs(L1 - bond_target) + abs(L2 - bond_target))

    twist0 = twist0 or 1.0
    S = float(twist_hist[-1] / twist0) if twist_hist else 0.0
    id_tail = float(np.mean(id_hist[-max(10, frames // 5) :]))
    burst_rate = total_bursts / max(1, frames * 3)
    final_angle = float(angle_hist[-1]) if angle_hist else float("nan")
    mean_angle = float(np.mean(angle_hist)) if angle_hist else float("nan")
    angle_rmse = (
        float(np.sqrt(np.mean([(a - target) ** 2 for a in angle_hist])))
        if target is not None and angle_hist
        else float("nan")
    )
    angle_retention = (
        float(np.exp(-abs(final_angle - target) / 30.0)) if target is not None else 1.0
    )
    stability = id_tail / (1.0 + 10.0 * burst_rate)

    return {
        "geometry": geometry,
        "constraint_requested": requested,
        "constraint": constraint,
        "target_angle_deg": target,
        "stiffness": stiffness if constraint == "soft" else None,
        "bond_stiffness": bond_stiffness,
        "bond_target": bond_target,
        "bond_len_OH1": last_bonds[0],
        "bond_len_OH2": last_bonds[1],
        "bond_err_mean": float(bond_err_acc / max(1, frames)) if bond_stiffness > 0 else None,
        "kappa": kappa,
        "delta_omega": delta_omega,
        "frames": frames,
        "Z_labels": {"O": Z_O, "H1": Z_H, "H2": Z_H},
        "mean_survival": S,
        "burst_rate": burst_rate,
        "total_bursts": total_bursts,
        "identity": id_tail,
        "stability_score": float(stability),
        "final_angle_deg": final_angle,
        "mean_angle_deg": mean_angle,
        "angle_rmse_deg": angle_rmse,
        "angle_retention": angle_retention,
        "angle_err_mean": float(angle_err_acc / max(1, frames)) if target is not None else None,
        "twist_final": float(twist_hist[-1]) if twist_hist else 0.0,
        "omega_scale_O": omega_scale_O,
        "omega_scale_H": omega_scale_H,
    }


def run_ensemble(
    *,
    geometries: tuple[str, ...] = ("free", "tetrahedral", "right", "linear"),
    stiffnesses: np.ndarray | None = None,
    constraints: tuple[str, ...] = ("soft",),
    bond_stiffness: float = 0.0,
    bond_target: float = DEFAULT_BOND_LEN,
    n_seeds: int = 5,
    frames: int = 250,
    kappa: float = 0.85,
    delta_omega: float = 0.008,
    base_seed: int = 11,
) -> dict:
    if stiffnesses is None:
        stiffnesses = np.array([0.0, 0.15, 0.35, 0.6, 1.0, 1.5])

    rows: list[dict] = []
    # Expand hybrid into per-geometry effective modes for counting
    work = 0
    for geom in geometries:
        for cons in constraints:
            if geom == "free" and cons not in ("soft", "hybrid"):
                continue
            eff = resolve_constraint(geom, cons) if geom != "free" else "none"
            if eff == "hard":
                work += n_seeds
            else:
                for k in stiffnesses:
                    if geom == "free" and float(k) > 0.0:
                        continue
                    work += n_seeds
    done = 0

    def _agg(seed_rows: list[dict], geom: str, cons_req: str, cons_eff: str, k: float) -> dict:
        def _mean(key: str) -> float:
            vals = [r[key] for r in seed_rows if r[key] is not None and np.isfinite(r[key])]
            return float(np.mean(vals)) if vals else float("nan")

        def _std(key: str) -> float:
            vals = [r[key] for r in seed_rows if r[key] is not None and np.isfinite(r[key])]
            return float(np.std(vals)) if vals else float("nan")

        return {
            "geometry": geom,
            "constraint_requested": cons_req if geom != "free" else "none",
            "constraint": cons_eff if geom != "free" else "none",
            "stiffness": float(k) if cons_eff == "soft" and geom != "free" else 0.0,
            "bond_stiffness": bond_stiffness,
            "n_seeds": n_seeds,
            "mean_survival": _mean("mean_survival"),
            "mean_survival_std": _std("mean_survival"),
            "burst_rate": _mean("burst_rate"),
            "identity": _mean("identity"),
            "stability_score": _mean("stability_score"),
            "final_angle_deg": _mean("final_angle_deg"),
            "angle_rmse_deg": _mean("angle_rmse_deg"),
            "angle_retention": _mean("angle_retention"),
            "bond_err_mean": _mean("bond_err_mean") if bond_stiffness > 0 else None,
            "bond_len_OH1": _mean("bond_len_OH1"),
            "bond_len_OH2": _mean("bond_len_OH2"),
            "target_angle_deg": GEOMETRY_TARGETS_DEG[geom],
        }

    seen_free = False
    for geom in geometries:
        for cons in constraints:
            if geom == "free":
                if seen_free or cons not in ("soft", "hybrid"):
                    continue
                seen_free = True
            geom_offset = {"free": 0, "tetrahedral": 3, "right": 7, "linear": 11}.get(geom, 0)
            cons_offset = {"soft": 0, "hard": 100, "hybrid": 200, "none": 0}.get(cons, 0)
            eff = resolve_constraint(geom, cons) if geom != "free" else "none"

            if eff == "hard" and geom != "free":
                seed_rows = []
                for s in range(n_seeds):
                    r = run_trimer(
                        geometry=geom,
                        stiffness=0.0,
                        constraint="hard",
                        bond_stiffness=bond_stiffness,
                        bond_target=bond_target,
                        frames=frames,
                        kappa=kappa,
                        delta_omega=delta_omega,
                        seed=base_seed + s * 17 + geom_offset + cons_offset,
                    )
                    seed_rows.append(r)
                    done += 1
                tag = "hybrid→hard" if cons == "hybrid" else "hard"
                agg = _agg(seed_rows, geom, cons, "hard", 0.0)
                rows.append(agg)
                print(
                    f"  [{done}/{work}] {geom:12s} {tag:12s}  "
                    f"S={agg['mean_survival']:.4f}  burst={agg['burst_rate']:.4f}  "
                    f"id={agg['identity']:.4f}  ∠rmse={agg['angle_rmse_deg']:.2f}"
                )
                continue

            # soft / free (and hybrid→soft for non-linear)
            for k in stiffnesses:
                if geom == "free" and float(k) > 0.0:
                    continue
                seed_rows = []
                for s in range(n_seeds):
                    r = run_trimer(
                        geometry=geom,
                        stiffness=float(k) if geom != "free" else 0.0,
                        constraint="soft" if geom != "free" else "none",
                        bond_stiffness=bond_stiffness,
                        bond_target=bond_target,
                        frames=frames,
                        kappa=kappa,
                        delta_omega=delta_omega,
                        seed=base_seed + s * 17 + geom_offset,
                    )
                    seed_rows.append(r)
                    done += 1
                tag = "hybrid→soft" if cons == "hybrid" and geom != "free" else (
                    "soft" if geom != "free" else "none"
                )
                agg = _agg(
                    seed_rows,
                    geom,
                    cons if geom != "free" else "none",
                    "soft" if geom != "free" else "none",
                    float(k),
                )
                rows.append(agg)
                bond_txt = (
                    f"  bond_err={agg['bond_err_mean']:.3f}"
                    if bond_stiffness > 0 and agg.get("bond_err_mean") is not None
                    else ""
                )
                print(
                    f"  [{done}/{work}] {geom:12s} {tag:12s} k={agg['stiffness']:.2f}  "
                    f"S={agg['mean_survival']:.4f}  burst={agg['burst_rate']:.4f}  "
                    f"id={agg['identity']:.4f}  ∠rmse={agg['angle_rmse_deg']:.2f}{bond_txt}"
                )

    summary = _summarize(rows)
    return {
        "mode": "h2o_toy_minimal",
        "framing": (
            "Three quaternion flywheels (O+2H) with Option A soft, Option B hard, "
            "and/or hybrid (hard for linear). Optional O–H bond soft potential. "
            "Not MD of water."
        ),
        "constraint_modes": list(constraints),
        "constraint_defs": {
            "soft": "V=(k/2)(∠−∠*)² harmonic kicks on H",
            "hard": "exact geometric projection each step (robust linear 180°)",
            "hybrid": "soft for tetrahedral/right; hard for linear (best-of-both)",
            "none": "free",
            "bond": f"V=(k_b/2)(|r_OH|−L*)²  L*={bond_target} (k_b={bond_stiffness})",
        },
        "settings": {
            "kappa": kappa,
            "delta_omega": delta_omega,
            "frames": frames,
            "n_seeds": n_seeds,
            "stiffnesses": stiffnesses.tolist(),
            "bond_stiffness": bond_stiffness,
            "bond_target": bond_target,
            "geometries": list(geometries),
            "tetrahedral_deg": TETRAHEDRAL_DEG,
        },
        "rows": rows,
        "summary": summary,
    }


def _summarize(rows: list[dict]) -> dict:
    free = [r for r in rows if r["geometry"] == "free"]
    free_S = free[0]["mean_survival"] if free else float("nan")
    free_burst = free[0]["burst_rate"] if free else float("nan")

    by_geom: dict[str, dict] = {}
    for geom in sorted({r["geometry"] for r in rows if r["geometry"] != "free"}):
        sub = [r for r in rows if r["geometry"] == geom]
        # Prefer hard if available and RMSE is good; else best soft by stability
        hard = [r for r in sub if r.get("constraint") == "hard"]
        soft = [r for r in sub if r.get("constraint") in ("soft", None, "none")]
        best_soft = max(soft, key=lambda r: r["stability_score"]) if soft else None
        best_hard = hard[0] if hard else None
        pick = best_hard if best_hard is not None else best_soft
        if pick is None:
            continue
        by_geom[geom] = {
            "best_constraint": pick.get("constraint"),
            "best_stiffness": pick.get("stiffness"),
            "stability_score": pick["stability_score"],
            "mean_survival": pick["mean_survival"],
            "burst_rate": pick["burst_rate"],
            "identity": pick["identity"],
            "angle_rmse_deg": pick["angle_rmse_deg"],
            "soft_best": (
                {
                    "stiffness": best_soft["stiffness"],
                    "angle_rmse_deg": best_soft["angle_rmse_deg"],
                    "identity": best_soft["identity"],
                    "stability_score": best_soft["stability_score"],
                }
                if best_soft
                else None
            ),
            "hard": (
                {
                    "angle_rmse_deg": best_hard["angle_rmse_deg"],
                    "identity": best_hard["identity"],
                    "stability_score": best_hard["stability_score"],
                    "mean_survival": best_hard["mean_survival"],
                }
                if best_hard
                else None
            ),
            "delta_S_vs_free": pick["mean_survival"] - free_S if free else None,
            "delta_burst_vs_free": pick["burst_rate"] - free_burst if free else None,
        }

    return {
        "free": free[0] if free else None,
        "best_per_geometry": by_geom,
        "note": (
            "Hard constraint should drive linear ∠RMSE near 0; soft is for "
            "tunable tetrahedral/right wells."
        ),
    }


def plot_results(data: dict, out_path: Path) -> None:
    rows = data["rows"]
    geoms = sorted({r["geometry"] for r in rows})
    colors = {
        "free": "#8b949e",
        "tetrahedral": "#58a6ff",
        "right": "#3fb950",
        "linear": "#d29922",
    }

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.8))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes.ravel():
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")
        ax.grid(True, alpha=0.25, color="#30363d")

    def _plot_metric(ax, key: str, title: str, ylabel: str) -> None:
        for geom in geoms:
            soft = sorted(
                [r for r in rows if r["geometry"] == geom and r.get("constraint") in ("soft", "none")],
                key=lambda r: r["stiffness"],
            )
            hard = [r for r in rows if r["geometry"] == geom and r.get("constraint") == "hard"]
            c = colors.get(geom, "#c9d1d9")
            if geom == "free" and soft:
                ax.axhline(soft[0][key], color=c, ls="--", lw=1.2, label="free")
            elif soft:
                ax.plot(
                    [r["stiffness"] for r in soft],
                    [r[key] for r in soft],
                    "o-",
                    color=c,
                    label=f"{geom} soft",
                    ms=5,
                )
            if hard:
                ax.scatter(
                    [1.55],
                    [hard[0][key]],
                    marker="D",
                    s=55,
                    color=c,
                    edgecolors="#e6edf3",
                    zorder=5,
                    label=f"{geom} hard",
                )
        ax.set_xlabel("angle_stiffness k  (hard shown at k=1.55)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=6, loc="best")

    _plot_metric(axes[0, 0], "mean_survival", "Mean survival S", "S")
    _plot_metric(axes[0, 1], "burst_rate", "Burst rate", "burst_rate")
    _plot_metric(axes[1, 0], "identity", "Identity", "identity")
    _plot_metric(axes[1, 1], "angle_rmse_deg", "Angle RMSE (soft vs hard)", "RMSE (deg)")
    axes[1, 1].axhline(0.0, color="#30363d", lw=0.5)

    summary = data.get("summary", {})
    best = summary.get("best_per_geometry", {})
    lin = best.get("linear", {})
    tet = best.get("tetrahedral", {})
    fig.suptitle(
        f"H₂O toy  soft+hard  |  "
        f"linear hard ∠rmse={((lin.get('hard') or {}).get('angle_rmse_deg', float('nan'))):.2f}°  "
        f"tet soft ∠rmse={((tet.get('soft_best') or {}).get('angle_rmse_deg', float('nan'))):.1f}°",
        color="#e6edf3",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Minimal H₂O three-flywheel trimer (soft and/or hard angle)"
    )
    p.add_argument("--kappa", type=float, default=0.85)
    p.add_argument("--domega", type=float, default=0.008)
    p.add_argument("--frames", type=int, default=250)
    p.add_argument("--n-seeds", type=int, default=5)
    p.add_argument("--n-stiffness", type=int, default=6)
    p.add_argument("--k-max", type=float, default=1.5)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument(
        "--constraint",
        choices=("soft", "hard", "hybrid", "both"),
        default="hybrid",
        help=(
            "Angle constraint (default hybrid = soft tet/right, hard linear). "
            "Choices: soft | hard | hybrid | both (soft sweep + hard)"
        ),
    )
    p.add_argument(
        "--bond-stiffness",
        type=float,
        default=0.0,
        help="Soft O–H bond length potential strength (0=off)",
    )
    p.add_argument(
        "--bond-target",
        type=float,
        default=DEFAULT_BOND_LEN,
        help="Target abstract O–H length in pointer space",
    )
    p.add_argument("--quick", action="store_true")
    args = p.parse_args()

    if args.quick:
        args.frames = 120
        args.n_seeds = 3
        args.n_stiffness = 4

    if args.constraint == "both":
        constraints: tuple[str, ...] = ("soft", "hard")
    else:
        constraints = (args.constraint,)

    stiffnesses = np.linspace(0.0, args.k_max, args.n_stiffness)
    print("H₂O toy minimal — interpretive")
    print(
        f"  κ={args.kappa}  Δω={args.domega}  frames={args.frames}  "
        f"seeds={args.n_seeds}  constraint={args.constraint}  "
        f"bond_k={args.bond_stiffness}"
    )
    print(f"  tetrahedral target = {TETRAHEDRAL_DEG:.3f}°")

    data = run_ensemble(
        stiffnesses=stiffnesses,
        constraints=constraints,
        bond_stiffness=args.bond_stiffness,
        bond_target=args.bond_target,
        n_seeds=args.n_seeds,
        frames=args.frames,
        kappa=args.kappa,
        delta_omega=args.domega,
        base_seed=args.seed,
    )
    plot_path = OUTPUT_DIR / "h2o_toy_minimal.png"
    plot_results(data, plot_path)
    report = save_report("h2o_toy_minimal", data)

    print("\n--- summary per geometry ---")
    for geom, info in data["summary"].get("best_per_geometry", {}).items():
        hard = info.get("hard")
        soft = info.get("soft_best")
        print(f"  {geom}:")
        if hard:
            print(
                f"    hard  ∠rmse={hard['angle_rmse_deg']:.3f}  "
                f"id={hard['identity']:.4f}  stab={hard['stability_score']:.4f}  "
                f"S={hard['mean_survival']:.4f}"
            )
        if soft:
            print(
                f"    soft  k*={soft['stiffness']:.2f}  ∠rmse={soft['angle_rmse_deg']:.2f}  "
                f"id={soft['identity']:.4f}  stab={soft['stability_score']:.4f}"
            )
    if data["summary"].get("free"):
        f = data["summary"]["free"]
        print(
            f"  free          S={f['mean_survival']:.4f}  "
            f"burst={f['burst_rate']:.4f}  id={f['identity']:.4f}"
        )
    print(f"Wrote {plot_path}")
    print(f"Wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
