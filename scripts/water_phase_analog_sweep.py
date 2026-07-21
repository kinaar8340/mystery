#!/usr/bin/env python3
"""
Water-phase *analog* sweep on the gauged Hopf lattice stack.

=============================================================================
  NOT H₂O thermodynamics. Falsifiable map of solid / liquid / vapor-like
  regimes onto objects already implemented in mystery / oam_flux / kingdom /
  toe / flux_hopf_lib.
=============================================================================

Control plane
  κ      — gauge damping          (cohesion / pressure-like)
  Δω     — two-gyro drive         (temperature / heat-like)
  τ_rec  — recovery time (opt.)   (viscosity / memory / glassiness)

Probes
  PDE (fixed physical horizon — not λt=2) + multi-site two-gyro lattice
  Order params: S, F, structure retention, identity |⟨q,q₀⟩|, burst_rate,
                pointer_var, drive/damp, holonomy gap B(κ)

Labels (retune LABEL_THRESHOLDS below — no logic edit required)
  solid          locked identity, low bursts, weak drive
  liquid         brackish mid-plane (default fertile zone)
  vapor          high bursts / decohered identity / strong drive
  supercritical  high drive near κ ≈ e/π holonomy-gap sign flip

Outputs
  outputs/water_phase_analog_heatmap.png
  outputs/water_phase_analog_sweep_<timestamp>.json

Examples
  python scripts/water_phase_analog_sweep.py
  python scripts/water_phase_analog_sweep.py --quick
  python scripts/water_phase_analog_sweep.py --ic hopfion
  python scripts/water_phase_analog_sweep.py --stress-ic
  python scripts/water_phase_analog_sweep.py --stress-ic-map
  python scripts/water_phase_analog_sweep.py --recovery-slice
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    E,
    OUTPUT_DIR,
    PI,
    R_RESIDUAL,
    save_report,
)
from flux_hopf_lib.constants import theta_crit as theta_crit_fn  # noqa: E402
from flux_hopf_lib.quaternion.core import q_conj, q_mult, q_normalize, small_rotor  # noqa: E402
from flux_hopf_lib.simulation.relaxation import twist_pde_step  # noqa: E402

# =============================================================================
# TUNABLE THRESHOLDS — edit here to retune phases without touching logic
# =============================================================================
# Fit notes (see notes/water_phase_analog.md):
#   solid  ← Magic Island + high identity + low bursts
#   liquid ← brackish (repo-named transitional zone); mid identity / mid drive
#   vapor  ← chaotic lattice (low gauge) or high drive/damp
#   super  ← holonomy-gap crossover near e/π under strong drive
# =============================================================================


@dataclass(frozen=True)
class LabelThresholds:
    """All knobs for label_phase(). Defaults match the calibrated 9×9 map."""

    # Residual target (mystery R = φ² + e² − π²)
    R: float = float(R_RESIDUAL)

    # --- solid (ice-like lock) ---
    solid_identity_min: float = 0.62
    solid_burst_max: float = 0.015
    solid_drive_max: float = 0.04
    solid_ptr_var_max: float = 0.05

    # --- liquid (brackish cohesion) ---
    liquid_identity_min: float = 0.50
    liquid_burst_max: float = 0.08
    # optional S-band (fixed-horizon S is not λt=2; keep wide)
    liquid_S_lo: float = 0.35
    liquid_S_hi: float = 1.05
    # |S − R| band only meaningful under λt-normalized probes; optional soft cue
    liquid_S_near_R: float = 0.08  # unused at fixed horizon by default

    # --- vapor ---
    vapor_burst_min: float = 0.04
    vapor_identity_max: float = 0.55
    vapor_drive_min: float = 0.10
    vapor_votes_needed: int = 2

    # --- supercritical (near e/π, strong drive) ---
    super_drive_min: float = 0.08
    super_kappa_near_e_over_pi: float = 0.12

    # --- recovery / glassiness (optional 3rd axis) ---
    glass_recovery_tau_min: float = 40.0
    glass_structure_ret_min: float = 0.05


# Default singleton — override via CLI or LabelThresholds(...)
LABEL_THRESHOLDS = LabelThresholds()

PHASE_SOLID = "solid"
PHASE_LIQUID = "liquid"
PHASE_VAPOR = "vapor"
PHASE_SUPER = "supercritical"
PHASE_GLASS = "glass"  # only used in recovery-slice mode annotations

PHASE_TO_INT = {
    PHASE_SOLID: 0,
    PHASE_LIQUID: 1,
    PHASE_VAPOR: 2,
    PHASE_SUPER: 3,
}
INT_TO_PHASE = {v: k for k, v in PHASE_TO_INT.items()}
PHASE_COLORS = ["#6ec6ff", "#2a9d8f", "#e9c46a", "#e76f51"]  # ice / water / steam / super


# =============================================================================
# Initial conditions
# =============================================================================
IC_CHOICES = ("helical", "hopfion", "uniform", "tetrahedral")


def _grid(nx: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    coords = np.linspace(0.0, 2.0 * np.pi, nx, endpoint=False)
    return np.meshgrid(coords, coords, coords, indexing="ij")


def ic_helical(nx: int, amplitude: float = 1.2, pitch: float = 0.35) -> np.ndarray:
    """Two-gyro helical seed (oam_flux / mystery structured-IC class)."""
    x, y, z = _grid(nx)
    return amplitude * (0.5 + 0.5 * np.sin(pitch * (x + 2.0 * y - z)))


def ic_hopfion(nx: int, amplitude: float = 2.5, sigma: float = 0.35) -> np.ndarray:
    """Localized Gaussian twist blob (flux-flywheel / hopfion seed)."""
    x, y, z = _grid(nx)
    cx = cy = cz = PI
    r2 = (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2
    return 0.2 + amplitude * np.exp(-r2 / (2.0 * sigma**2))


def ic_uniform(nx: int, seed: int = 42) -> np.ndarray:
    """Unstructured noise — gas-like / random seed."""
    rng = np.random.default_rng(seed)
    return rng.uniform(0.1, 2.0, (nx, nx, nx))


def ic_tetrahedral(nx: int, amplitude: float = 1.0) -> np.ndarray:
    """
    Four-center tetrahedral twist peaks on T³ (D4 / ice-local-structure analog).

    Centers are tetrahedron vertices projected into the periodic box — a soft
    geometric stress test, not a molecular H-bond model.
    """
    x, y, z = _grid(nx)
    # Regular tetrahedron vertices (scaled into [0, 2π))
    verts = np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0],
        ],
        dtype=float,
    )
    verts = (verts / np.linalg.norm(verts, axis=1, keepdims=True) + 1.0) * PI
    sigma = 0.45
    field = np.full((nx, nx, nx), 0.25, dtype=float)
    for vx, vy, vz in verts:
        r2 = (x - vx) ** 2 + (y - vy) ** 2 + (z - vz) ** 2
        field = field + amplitude * np.exp(-r2 / (2.0 * sigma**2))
    return field


def make_ic(name: str, nx: int, seed: int = 42) -> np.ndarray:
    name = name.lower()
    if name == "helical":
        return ic_helical(nx)
    if name == "hopfion":
        return ic_hopfion(nx)
    if name == "uniform":
        return ic_uniform(nx, seed=seed)
    if name == "tetrahedral":
        return ic_tetrahedral(nx)
    raise ValueError(f"Unknown IC {name!r}; choose from {IC_CHOICES}")


def structure_power(theta: np.ndarray) -> float:
    """
    Full-3D non-DC FFT power of demeaned θ.

    Uses fftn (not a single mid-slice) so tetrahedral / hopfion peaks off the
    equatorial plane still contribute — avoids false structure_retention spikes
    when struct₀ ≈ 0 on a bad cut.
    """
    field = theta - float(theta.mean())
    if float(np.std(field)) < 1e-12:
        return 0.0
    power = np.abs(np.fft.fftn(field)) ** 2
    power.flat[0] = 0.0
    return float(power.sum())


def safe_ratio(num: float, denom: float) -> float:
    return float(num / denom) if abs(denom) > 1e-12 else 0.0


# Default structure-retention floor for "still ordered" (seed quality)
DEFAULT_PERSIST_THRESH = 0.02


def compute_persistence_time(
    struct_ret_trace: list[float],
    times: list[float],
    threshold: float = DEFAULT_PERSIST_THRESH,
) -> dict:
    """
    First crossing of structure retention below threshold.

    Persistence = time of first sample with struct_ret < threshold.
    If never crossed, structure survives the full tracked horizon.
    """
    if not struct_ret_trace or not times:
        return {
            "persistence_time": 0.0,
            "persistence_frac": 0.0,
            "survived_horizon": False,
            "persist_threshold": threshold,
        }
    t_end = float(times[-1])
    for s, t in zip(struct_ret_trace, times):
        if s < threshold:
            return {
                "persistence_time": float(t),
                "persistence_frac": float(t / max(t_end, 1e-12)),
                "survived_horizon": False,
                "persist_threshold": threshold,
            }
    return {
        "persistence_time": t_end,
        "persistence_frac": 1.0,
        "survived_horizon": True,
        "persist_threshold": threshold,
    }


def fit_recovery_curve(
    times: np.ndarray,
    load: np.ndarray,
    *,
    min_points: int = 6,
) -> dict:
    """
    Fit simple exponential vs stretched exponential to recovery load.

    load(t) = |θ − θ₀| mean, expected to *decrease* toward 0 under recovery.
    Model A:  L(t) = L∞ + (L0 − L∞) exp(−t/τ)
    Model B:  L(t) = L∞ + (L0 − L∞) exp(−(t/τ)^β)   (Kohlrausch / stretched)

    Uses log-linear least squares on demeaned transient for A; grid-search β for B.
    """
    t = np.asarray(times, dtype=float)
    y = np.asarray(load, dtype=float)
    if len(t) < min_points or float(np.std(y)) < 1e-15:
        return {
            "model": "flat",
            "tau_exp": None,
            "tau_stretch": None,
            "beta": None,
            "r2_exp": 0.0,
            "r2_stretch": 0.0,
            "preferred": "flat",
            "delta_r2": 0.0,
        }

    t0 = t[0]
    tt = t - t0
    L0 = float(y[0])
    L_inf = float(np.mean(y[-max(3, len(y) // 10) :]))
    amp = L0 - L_inf
    if abs(amp) < 1e-12:
        return {
            "model": "flat",
            "tau_exp": None,
            "tau_stretch": None,
            "beta": None,
            "r2_exp": 0.0,
            "r2_stretch": 0.0,
            "preferred": "flat",
            "delta_r2": 0.0,
        }

    # Clip for log domain (decay toward L_inf from above or below)
    residual = y - L_inf
    sign = 1.0 if amp > 0 else -1.0
    residual_pos = np.clip(sign * residual, 1e-15, None)

    def _r2(y_true: np.ndarray, y_hat: np.ndarray) -> float:
        ss_res = float(np.sum((y_true - y_hat) ** 2))
        ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
        return 1.0 - ss_res / ss_tot if ss_tot > 1e-18 else 0.0

    # --- simple exponential via log-linear on early half ---
    mask = residual_pos > 1e-12
    if mask.sum() < min_points:
        return {
            "model": "degenerate",
            "tau_exp": None,
            "tau_stretch": None,
            "beta": None,
            "r2_exp": 0.0,
            "r2_stretch": 0.0,
            "preferred": "degenerate",
            "delta_r2": 0.0,
        }

    tt_m = tt[mask]
    log_r = np.log(residual_pos[mask])
    # log|res| = log|amp| − t/τ  →  slope = −1/τ
    A = np.vstack([tt_m, np.ones_like(tt_m)]).T
    slope, intercept = np.linalg.lstsq(A, log_r, rcond=None)[0]
    tau_exp = float(-1.0 / slope) if slope < 0 else float("inf")
    if not np.isfinite(tau_exp) or tau_exp <= 0:
        tau_exp = float(tt[-1]) if tt[-1] > 0 else 1.0
    y_hat_exp = L_inf + amp * np.exp(-tt / max(tau_exp, 1e-9))
    r2_exp = _r2(y, y_hat_exp)

    # --- stretched exponential: grid β ∈ (0.3, 1.5) ---
    best = {"beta": 1.0, "tau": tau_exp, "r2": r2_exp}
    for beta in np.linspace(0.3, 1.5, 25):
        # For fixed β, log|res| = log|amp| − (t/τ)^β  →  let u = t^β, fit slope
        u = np.power(np.maximum(tt_m, 0.0), beta)
        A_b = np.vstack([u, np.ones_like(u)]).T
        try:
            sl_b, _ = np.linalg.lstsq(A_b, log_r, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        if sl_b >= 0:
            continue
        # sl_b = −1/τ^β  ⇒  τ = (−1/sl_b)^{1/β}
        tau_b = float((-1.0 / sl_b) ** (1.0 / beta))
        if not np.isfinite(tau_b) or tau_b <= 0:
            continue
        y_hat = L_inf + amp * np.exp(-np.power(tt / tau_b, beta))
        r2_b = _r2(y, y_hat)
        if r2_b > best["r2"]:
            best = {"beta": float(beta), "tau": tau_b, "r2": r2_b}

    r2_stretch = float(best["r2"])
    # Prefer Kohlrausch-like if it gains ≥ 0.02 R² and β clearly ≠ 1
    # (β < 1 classic stretch / glass; β > 1 compressed return)
    prefer_stretch = (
        r2_stretch >= r2_exp + 0.02 and abs(float(best["beta"]) - 1.0) >= 0.05
    )
    preferred = "stretched_exp" if prefer_stretch else "exponential"

    return {
        "model": preferred,
        "tau_exp": float(tau_exp) if np.isfinite(tau_exp) else None,
        "tau_stretch": float(best["tau"]),
        "beta": float(best["beta"]),
        "r2_exp": float(r2_exp),
        "r2_stretch": r2_stretch,
        "preferred": preferred,
        "delta_r2": float(r2_stretch - r2_exp),
        "L0": L0,
        "L_inf": L_inf,
    }


# =============================================================================
# Probe A — fixed-horizon twist PDE
# =============================================================================
def run_pde_probe(
    kappa: float,
    delta_omega: float,
    *,
    nx: int = 12,
    nt: int = 800,
    dt: float = 0.001,
    D: float = 0.05,
    ic: str = "helical",
    seed: int = 42,
    recovery_tau: float | None = None,
    recovery_memory: float = 0.0,
    recovery_start_frac: float = 0.6,
    track_structure: bool = False,
    track_interval: int = 20,
    persist_threshold: float = DEFAULT_PERSIST_THRESH,
    fit_recovery: bool = False,
) -> dict:
    """
    Evolve IC for fixed *physical* time nt·dt (not λt=2).

    Optional recovery: after recovery_start_frac of steps, pump off and relax
    toward θ₀ with exponential memory (oam_flux recovery analog / viscosity).

    track_structure: record structure_retention trace + persistence_time
    fit_recovery: fit exp vs stretched-exp to post-pump load curve
    """
    t_crit = float(theta_crit_fn(kappa))
    theta0 = make_ic(ic, nx, seed=seed)
    theta = theta0.copy()
    theta0_mean = float(theta.mean())
    theta0_std = float(theta.std())
    struct0 = structure_power(theta)

    burst_site_steps = 0
    max_theta = 0.0
    recovery_on_step = int(nt * recovery_start_frac) if recovery_tau is not None else nt + 1

    struct_ret_trace: list[float] = []
    struct_times: list[float] = []
    load_trace: list[float] = []  # mean |θ − θ₀|
    load_times: list[float] = []

    for step in range(nt):
        burst_site_steps += int(np.sum(theta > 0.95 * t_crit))
        theta = twist_pde_step(
            theta,
            dt=dt,
            D=D,
            kappa=kappa,
            delta_omega=delta_omega,
            theta_crit=t_crit,
            nx=nx,
        )
        # Recovery / glassiness: pull toward initial field (memory)
        if step >= recovery_on_step and recovery_tau is not None:
            tau = max(float(recovery_tau), 1e-6)
            mem = float(np.clip(recovery_memory, 0.0, 1.0))
            alpha = (1.0 - mem) * (1.0 - np.exp(-1.0 / tau))
            theta = np.clip(
                theta + alpha * (theta0 - theta),
                0.01,
                2.0 * PI - 0.01,
            )
        max_theta = max(max_theta, float(theta.max()))

        if track_structure and (step % track_interval == 0 or step == nt - 1):
            s = structure_power(theta)
            struct_ret_trace.append(safe_ratio(s, struct0))
            struct_times.append(float((step + 1) * dt))

        if fit_recovery and recovery_tau is not None and step >= recovery_on_step:
            if (step - recovery_on_step) % track_interval == 0 or step == nt - 1:
                load = float(np.mean(np.abs(theta - theta0)))
                load_trace.append(load)
                load_times.append(float((step - recovery_on_step + 1) * dt))
                # Structure during recovery (PDE nonlinearity can stretch the return)
                s_rec = structure_power(theta)
                # reuse parallel lists via struct traces when only recovery-tracked
                if not track_structure:
                    struct_ret_trace.append(safe_ratio(s_rec, struct0))
                    struct_times.append(float((step - recovery_on_step + 1) * dt))

    final_mean = float(theta.mean())
    final_std = float(theta.std())
    struct = structure_power(theta)
    n_vox = nx**3

    out: dict = {
        "mean_survival": safe_ratio(final_mean, theta0_mean),
        "fluctuation_survival": safe_ratio(final_std, theta0_std),
        "structure_retention": safe_ratio(struct, struct0),
        "final_mean": final_mean,
        "final_std": final_std,
        "max_theta": max_theta,
        "theta_crit": t_crit,
        "burst_risk": burst_site_steps / max(1, nt * n_vox),
        "drive_over_damp": float(delta_omega / max(kappa, 1e-9)),
        "holonomy_gap": float(PI**2 * (E / PI - kappa)),
        "ic": ic,
        "recovery_tau": recovery_tau,
        "recovery_memory": recovery_memory if recovery_tau is not None else None,
        "horizon_time": float(nt * dt),
    }

    if track_structure:
        persist = compute_persistence_time(
            struct_ret_trace, struct_times, threshold=persist_threshold
        )
        out.update(persist)
        # compact traces for JSON (downsample already via track_interval)
        out["struct_ret_trace"] = struct_ret_trace
        out["struct_times"] = struct_times

    if fit_recovery and recovery_tau is not None and load_trace:
        # Prefer fitting structure_retention during recovery (can show stretch
        # from PDE nonlinearities). Fall back to load |θ−θ₀| (near-pure exp
        # by construction of the recovery step).
        if len(struct_ret_trace) >= 6 and not track_structure:
            # recovery-only structure traces (times already relative to pump-off)
            fit = fit_recovery_curve(
                np.asarray(struct_times), np.asarray(struct_ret_trace)
            )
            fit["fitted_signal"] = "structure_retention"
        else:
            fit = fit_recovery_curve(np.asarray(load_times), np.asarray(load_trace))
            fit["fitted_signal"] = "load"
        out["recovery_fit"] = fit
        out["load_trace"] = load_trace
        out["load_times"] = load_times
        out["final_load"] = float(load_trace[-1])
        if not track_structure and struct_ret_trace:
            out["recovery_struct_ret_trace"] = struct_ret_trace
            out["recovery_struct_times"] = struct_times

    return out


# =============================================================================
# Probe B — multi-site two-gyro lattice (kingdom Lattice Simulator analog)
# =============================================================================
def run_lattice_probe(
    kappa: float,
    delta_omega: float,
    *,
    n_sites: int = 48,
    frames: int = 120,
    omega_L: float = 0.025,
    seed: int = 7,
) -> dict:
    """
    Gauged two-gyro quaternion lattice.

    gauge_strength tied to κ; Δω detunes the right gyro (temperature analog).
    """
    rng = np.random.default_rng(seed)
    q = np.array([q_normalize(rng.standard_normal(4)) for _ in range(n_sites)])
    identity = np.array([q_normalize(rng.standard_normal(4)) for _ in range(n_sites)])
    identity0 = identity.copy()
    twist = np.zeros(n_sites)

    gauge_strength = float(kappa)
    omega_R = omega_L - float(delta_omega)
    t_crit = float(theta_crit_fn(kappa))

    pointer_hist: list[float] = []
    identity_hist: list[float] = []
    total_bursts = 0

    for _ in range(frames):
        dL = small_rotor(omega_L)
        dR = small_rotor(omega_R)
        for i in range(n_sites):
            q[i] = q_normalize(q_mult(q_mult(dL, q[i]), q_conj(dR)))
            twist[i] = 2.0 * np.arccos(np.clip(q[i][0], -1.0, 1.0))

        avg_imbalance = float(np.mean(twist) % (2.0 * np.pi))
        gauge_alpha = -gauge_strength * avg_imbalance
        gauge_rot = np.array([np.cos(gauge_alpha), 0.0, 0.0, np.sin(gauge_alpha)])
        for i in range(n_sites):
            q[i] = q_normalize(q_mult(q[i], gauge_rot))
            identity[i] = q_normalize(q_mult(identity[i], gauge_rot))

        bursts = 0
        for i in range(n_sites):
            if twist[i] > t_crit:
                q[i] = q_normalize(0.3 * np.array([1.0, 0.0, 0.0, 0.0]) + 0.7 * q[i])
                twist[i] *= 0.15
                bursts += 1
        total_bursts += bursts

        pointer_hist.append(float(np.tanh(gauge_alpha * 6.0)))
        cosines = np.abs(np.sum(identity * identity0, axis=1))
        identity_hist.append(float(np.mean(cosines)))

    tail = max(10, frames // 5)
    id_tail = float(np.mean(identity_hist[-tail:]))
    ptr_rms = float(np.sqrt(np.mean(np.square(pointer_hist[-tail:]))))
    ptr_var = float(np.var(pointer_hist))
    mean_twist = float(np.mean(twist))
    burst_rate = total_bursts / max(1, frames * n_sites)

    # Island-style stability score proxy (Magic Island spirit, local form)
    # score ∝ identity / (1 + bursts) — high = solid-like lock
    stability_score = id_tail / (1.0 + 10.0 * burst_rate)

    return {
        "identity_preservation": id_tail,
        "identity_mean": float(np.mean(identity_hist)),
        "pointer_rms": ptr_rms,
        "pointer_var": ptr_var,
        "burst_rate": burst_rate,
        "mean_twist": mean_twist,
        "stability_score": float(stability_score),
        "gauge_strength": gauge_strength,
        "omega_L": omega_L,
        "omega_R": omega_R,
        "total_bursts": total_bursts,
    }


# =============================================================================
# Phase labeling — reads LABEL_THRESHOLDS only
# =============================================================================
def label_phase(
    pde: dict,
    lat: dict,
    thr: LabelThresholds = LABEL_THRESHOLDS,
) -> tuple[str, dict]:
    """
    Heuristic solid / liquid / vapor / supercritical.

    Priority: supercritical → solid → vapor → liquid (brackish default).

    Skeleton form (see thr fields for numbers)::

        if identity high and bursts low and drive low:
            solid
        elif near mid-plane cohesion:
            liquid
        elif bursts high or identity low or drive high:
            vapor
        elif kappa near e/π and drive high:
            supercritical
    """
    S = float(pde["mean_survival"])
    F = float(pde["fluctuation_survival"])
    drive = float(pde["drive_over_damp"])
    B = float(pde["holonomy_gap"])
    identity = float(lat["identity_preservation"])
    bursts = float(lat["burst_rate"])
    ptr_var = float(lat["pointer_var"])
    stability = float(lat["stability_score"])
    kappa = float(lat["gauge_strength"])
    e_over_pi = E / PI

    features = {
        "mean_survival": S,
        "fluctuation_survival": F,
        "drive_over_damp": drive,
        "holonomy_gap_B": B,
        "identity": identity,
        "burst_rate": bursts,
        "pointer_var": ptr_var,
        "stability_score": stability,
        "delta_pct_vs_R": 100.0 * abs(S - thr.R) / abs(thr.R),
        "kappa_vs_e_over_pi": kappa - e_over_pi,
    }

    # Supercritical: drive blurs lock/chaos near holonomy crossover
    if drive >= thr.super_drive_min and abs(kappa - e_over_pi) <= thr.super_kappa_near_e_over_pi:
        return PHASE_SUPER, features

    # Solid: topologically locked
    if (
        identity >= thr.solid_identity_min
        and bursts <= thr.solid_burst_max
        and drive <= thr.solid_drive_max
        and ptr_var <= thr.solid_ptr_var_max
    ):
        return PHASE_SOLID, features

    # Vapor: decoherence / strong drive (require ≥N agreeing signals)
    vapor_votes = (
        int(bursts >= thr.vapor_burst_min)
        + int(identity <= thr.vapor_identity_max)
        + int(drive >= thr.vapor_drive_min)
    )
    if (
        vapor_votes >= thr.vapor_votes_needed
        or bursts >= 2.0 * thr.vapor_burst_min
        or drive >= 2.0 * thr.vapor_drive_min
    ):
        return PHASE_VAPOR, features

    # Liquid / brackish
    if identity >= thr.liquid_identity_min and bursts <= thr.liquid_burst_max:
        return PHASE_LIQUID, features
    if thr.liquid_S_lo <= S <= thr.liquid_S_hi and thr.solid_drive_max < drive < thr.vapor_drive_min:
        return PHASE_LIQUID, features
    if identity >= thr.liquid_identity_min:
        return PHASE_LIQUID, features

    return PHASE_VAPOR, features


# =============================================================================
# Sweep modes
# =============================================================================
def run_sweep(
    *,
    kappa_min: float = 0.25,
    kappa_max: float = 1.15,
    n_kappa: int = 9,
    domega_min: float = 0.001,
    domega_max: float = 0.08,
    n_domega: int = 9,
    nx: int = 12,
    nt: int = 800,
    frames: int = 120,
    n_sites: int = 48,
    seed: int = 7,
    D: float = 0.05,
    dt: float = 0.001,
    ic: str = "helical",
    thr: LabelThresholds = LABEL_THRESHOLDS,
) -> dict:
    kappas = np.linspace(kappa_min, kappa_max, n_kappa)
    domegas = np.geomspace(domega_min, domega_max, n_domega)

    rows: list[dict] = []
    phase_grid = np.zeros((n_domega, n_kappa), dtype=int)
    S_grid = np.zeros((n_domega, n_kappa))
    id_grid = np.zeros((n_domega, n_kappa))
    stab_grid = np.zeros((n_domega, n_kappa))
    drive_grid = np.zeros((n_domega, n_kappa))

    total = n_kappa * n_domega
    done = 0
    for j, kappa in enumerate(kappas):
        for i, dω in enumerate(domegas):
            pde = run_pde_probe(
                float(kappa), float(dω), nx=nx, nt=nt, dt=dt, D=D, ic=ic, seed=seed
            )
            lat = run_lattice_probe(
                float(kappa), float(dω), n_sites=n_sites, frames=frames, seed=seed
            )
            phase, features = label_phase(pde, lat, thr=thr)
            row = {
                "kappa": float(kappa),
                "delta_omega": float(dω),
                "phase": phase,
                "phase_id": PHASE_TO_INT[phase],
                **{f"pde_{k}": v for k, v in pde.items()},
                **{f"lat_{k}": v for k, v in lat.items()},
                **{f"feat_{k}": v for k, v in features.items()},
            }
            rows.append(row)
            phase_grid[i, j] = PHASE_TO_INT[phase]
            S_grid[i, j] = pde["mean_survival"]
            id_grid[i, j] = lat["identity_preservation"]
            stab_grid[i, j] = lat["stability_score"]
            drive_grid[i, j] = pde["drive_over_damp"]
            done += 1
            if done % max(1, total // 10) == 0 or done == total:
                print(f"  [{done}/{total}] κ={kappa:.3f} Δω={dω:.4f} → {phase}")

    counts = {p: 0 for p in PHASE_TO_INT}
    for r in rows:
        counts[r["phase"]] += 1

    return {
        "mode": "kappa_x_domega",
        "framing": (
            "Interpretive water-phase analog on gauged Hopf lattice dynamics — "
            "not H₂O thermodynamics."
        ),
        "axes": {
            "x": "kappa (gauge damping / cohesion-like)",
            "y": "delta_omega (drive / temperature-like, log-spaced)",
        },
        "reference": {
            "R": thr.R,
            "e_over_pi": E / PI,
            "kappa_doc": 0.85,
            "kappa_sim": 0.89,
            "W_g": 350.0 / PI,
        },
        "thresholds": asdict(thr),
        "grid": {
            "kappas": kappas.tolist(),
            "domegas": domegas.tolist(),
            "n_kappa": n_kappa,
            "n_domega": n_domega,
        },
        "pde_settings": {"nx": nx, "nt": nt, "dt": dt, "D": D, "ic": ic},
        "lattice_settings": {"n_sites": n_sites, "frames": frames, "seed": seed},
        "label_rules": {
            "solid": (
                f"identity≥{thr.solid_identity_min}, burst≤{thr.solid_burst_max}, "
                f"drive/damp≤{thr.solid_drive_max}"
            ),
            "liquid": "brackish mid-plane (default); intermediate identity/bursts",
            "vapor": f"≥{thr.vapor_votes_needed} of high burst / low identity / high drive",
            "supercritical": (
                f"drive/damp≥{thr.super_drive_min} and |κ−e/π|≤{thr.super_kappa_near_e_over_pi}"
            ),
            "identity_note": "absolute quaternion overlap |⟨q,q₀⟩|",
            "retune": "edit LabelThresholds / LABEL_THRESHOLDS at top of script",
        },
        "fit_assessment": {
            "ice": "strong — high stability_score + low bursts + structured IC",
            "liquid_brackish": "very strong — named regime; mid-plane dominance",
            "vapor": "strong — chaotic lattice / high drive",
            "latent_heat": "good — burst at θ_crit",
            "critical": "reasonable — B(κ) sign flip near e/π",
            "triple_point": "plausible — not multi-attractor scanned",
            "ice_density_anomaly": "weak — no quantitative density proxy",
        },
        "phase_counts": counts,
        "rows": rows,
        "arrays": {
            "phase_grid": phase_grid.tolist(),
            "mean_survival": S_grid.tolist(),
            "identity": id_grid.tolist(),
            "stability_score": stab_grid.tolist(),
            "drive_over_damp": drive_grid.tolist(),
        },
    }


def run_stress_ic(
    *,
    kappa: float = 0.85,
    delta_omega: float = 0.01,
    nx: int = 14,
    nt: int = 1000,
    frames: int = 120,
    n_sites: int = 48,
    seed: int = 7,
    D: float = 0.05,
    dt: float = 0.001,
    thr: LabelThresholds = LABEL_THRESHOLDS,
    persist_threshold: float = DEFAULT_PERSIST_THRESH,
    quiet: bool = False,
) -> dict:
    """
    Water stress test: tetrahedral / hopfion / helical vs uniform IC
    at fixed (κ, Δω) — does local topology boost liquid-like cohesion?

    Also reports persistence_time: how long structure_retention stays above
    persist_threshold after the seed is released into the dynamics.
    """
    rows = []
    for ic in IC_CHOICES:
        pde = run_pde_probe(
            kappa,
            delta_omega,
            nx=nx,
            nt=nt,
            dt=dt,
            D=D,
            ic=ic,
            seed=seed,
            track_structure=True,
            persist_threshold=persist_threshold,
        )
        lat = run_lattice_probe(
            kappa, delta_omega, n_sites=n_sites, frames=frames, seed=seed
        )
        phase, features = label_phase(pde, lat, thr=thr)
        # Drop bulky traces from per-row table copy used for ranking prints
        pde_row = {k: v for k, v in pde.items() if k not in ("struct_ret_trace", "struct_times")}
        row = {
            "ic": ic,
            "kappa": kappa,
            "delta_omega": delta_omega,
            "phase_from_dual": phase,
            **{f"pde_{k}": v for k, v in pde_row.items()},
            **{f"lat_{k}": v for k, v in lat.items()},
            **{f"feat_{k}": v for k, v in features.items()},
            # keep traces under nested key for optional plotting
            "struct_ret_trace": pde.get("struct_ret_trace", []),
            "struct_times": pde.get("struct_times", []),
        }
        rows.append(row)
        if not quiet:
            print(
                f"  IC={ic:12s}  S={pde['mean_survival']:.4f}  "
                f"F={pde['fluctuation_survival']:.4f}  "
                f"struct_ret={pde['structure_retention']:.4e}  "
                f"t_persist={pde.get('persistence_time', 0):.4f}  "
                f"phase={phase}"
            )

    ranked_struct = sorted(rows, key=lambda r: r["pde_structure_retention"], reverse=True)
    ranked_persist = sorted(rows, key=lambda r: r.get("pde_persistence_time", 0.0), reverse=True)
    return {
        "mode": "stress_ic",
        "framing": (
            "Tetrahedral / hopfion / helical vs uniform IC at fixed (κ, Δω). "
            "Higher structure_retention and persistence_time under structured "
            "seeds support ice/liquid local-order analogy."
        ),
        "fixed_point": {"kappa": kappa, "delta_omega": delta_omega},
        "persist_threshold": persist_threshold,
        "thresholds": asdict(thr),
        "pde_settings": {"nx": nx, "nt": nt, "dt": dt, "D": D},
        "rows": rows,
        "rank_by_structure_retention": [r["ic"] for r in ranked_struct],
        "rank_by_persistence_time": [r["ic"] for r in ranked_persist],
        "best_ic_structure": ranked_struct[0]["ic"] if ranked_struct else None,
        "best_ic_persistence": ranked_persist[0]["ic"] if ranked_persist else None,
        "best_ic": ranked_struct[0]["ic"] if ranked_struct else None,
    }


def run_stress_ic_map(
    *,
    points: list[tuple[float, float, str]] | None = None,
    nx: int = 12,
    nt: int = 700,
    frames: int = 80,
    n_sites: int = 32,
    seed: int = 7,
    D: float = 0.05,
    dt: float = 0.001,
    thr: LabelThresholds = LABEL_THRESHOLDS,
    persist_threshold: float = DEFAULT_PERSIST_THRESH,
) -> dict:
    """
    Multi-region IC stress: which seed wins where on the (κ, Δω) plane?

    Default points sample solid / liquid / vapor / super-ish neighborhoods.
    """
    if points is None:
        # (kappa, delta_omega, band_label)
        points = [
            (1.10, 0.002, "solid_hi_kappa"),
            (0.95, 0.003, "solid_edge"),
            (0.85, 0.010, "liquid_mid"),
            (0.89, 0.015, "liquid_kappa_sim"),
            (0.70, 0.020, "liquid_lo_kappa"),
            (0.50, 0.030, "vapor_bursty"),
            (0.35, 0.050, "vapor_hot"),
            (0.86, 0.070, "super_near_e_over_pi"),
        ]

    cells = []
    for kappa, dω, band in points:
        print(f"\n  band={band}  κ={kappa:.3f}  Δω={dω:.4f}")
        cell = run_stress_ic(
            kappa=kappa,
            delta_omega=dω,
            nx=nx,
            nt=nt,
            frames=frames,
            n_sites=n_sites,
            seed=seed,
            D=D,
            dt=dt,
            thr=thr,
            persist_threshold=persist_threshold,
            quiet=False,
        )
        # Slim rows for map JSON (drop traces)
        slim_rows = []
        for r in cell["rows"]:
            slim_rows.append(
                {
                    "ic": r["ic"],
                    "struct_ret": r["pde_structure_retention"],
                    "persistence_time": r.get("pde_persistence_time", 0.0),
                    "persistence_frac": r.get("pde_persistence_frac", 0.0),
                    "F": r["pde_fluctuation_survival"],
                    "S": r["pde_mean_survival"],
                }
            )
        cells.append(
            {
                "band": band,
                "kappa": kappa,
                "delta_omega": dω,
                "best_ic_structure": cell["best_ic_structure"],
                "best_ic_persistence": cell["best_ic_persistence"],
                "rank_structure": cell["rank_by_structure_retention"],
                "rank_persistence": cell["rank_by_persistence_time"],
                "rows": slim_rows,
            }
        )

    # Aggregate win counts
    wins_struct: dict[str, int] = {ic: 0 for ic in IC_CHOICES}
    wins_persist: dict[str, int] = {ic: 0 for ic in IC_CHOICES}
    for c in cells:
        if c["best_ic_structure"] in wins_struct:
            wins_struct[c["best_ic_structure"]] += 1
        if c["best_ic_persistence"] in wins_persist:
            wins_persist[c["best_ic_persistence"]] += 1

    return {
        "mode": "stress_ic_map",
        "framing": (
            "Which IC seed wins structure_retention / persistence_time across "
            "solid / liquid / vapor regions of the (κ, Δω) plane."
        ),
        "persist_threshold": persist_threshold,
        "pde_settings": {"nx": nx, "nt": nt, "dt": dt, "D": D},
        "cells": cells,
        "wins_by_structure": wins_struct,
        "wins_by_persistence": wins_persist,
    }


def run_recovery_slice(
    *,
    kappa: float = 0.85,
    delta_omega: float = 0.01,
    tau_min: float = 2.0,
    tau_max: float = 80.0,
    n_tau: int = 10,
    memory_values: tuple[float, ...] = (0.0, 0.3, 0.6),
    nx: int = 12,
    nt: int = 800,
    seed: int = 7,
    D: float = 0.05,
    dt: float = 0.001,
    ic: str = "helical",
    thr: LabelThresholds = LABEL_THRESHOLDS,
) -> dict:
    """
    Third-axis slice: recovery_tau × memory at fixed (κ, Δω).

    Large τ + high memory → glassiness / supercooling analog (structure sticks).
    Each point fits exp vs stretched-exp to the post-pump load curve.
    """
    taus = np.geomspace(tau_min, tau_max, n_tau)
    rows = []
    preferred_counts = {"exponential": 0, "stretched_exp": 0, "flat": 0, "degenerate": 0}
    for mem in memory_values:
        for tau in taus:
            pde = run_pde_probe(
                kappa,
                delta_omega,
                nx=nx,
                nt=nt,
                dt=dt,
                D=D,
                ic=ic,
                seed=seed,
                recovery_tau=float(tau),
                recovery_memory=float(mem),
                fit_recovery=True,
            )
            glass_like = (
                float(tau) >= thr.glass_recovery_tau_min
                and pde["structure_retention"] >= thr.glass_structure_ret_min
            )
            fit = pde.get("recovery_fit", {})
            pref = fit.get("preferred", "flat")
            if pref in preferred_counts:
                preferred_counts[pref] += 1
            # Drop bulky traces from default row (kept under recovery_fit summary)
            pde_slim = {
                k: v
                for k, v in pde.items()
                if k not in ("load_trace", "load_times", "struct_ret_trace", "struct_times")
            }
            rows.append(
                {
                    "kappa": kappa,
                    "delta_omega": delta_omega,
                    "recovery_tau": float(tau),
                    "recovery_memory": float(mem),
                    "glass_like": glass_like,
                    "recovery_preferred": pref,
                    "recovery_beta": fit.get("beta"),
                    "recovery_r2_exp": fit.get("r2_exp"),
                    "recovery_r2_stretch": fit.get("r2_stretch"),
                    "recovery_delta_r2": fit.get("delta_r2"),
                    "recovery_tau_exp": fit.get("tau_exp"),
                    "recovery_tau_stretch": fit.get("tau_stretch"),
                    **{f"pde_{k}": v for k, v in pde_slim.items() if k != "recovery_fit"},
                }
            )
        print(f"  memory={mem:.2f}  τ grid done ({n_tau} points)")

    n_stretch = preferred_counts.get("stretched_exp", 0)
    n_exp = preferred_counts.get("exponential", 0)
    return {
        "mode": "recovery_slice",
        "framing": (
            "Viscosity / glassiness analog: recovery_tau and memory after pump-off. "
            "High τ + structure retention → supercooling / glass-like stickiness. "
            "Curve shape: exponential vs stretched-exp (Kohlrausch) fit on load."
        ),
        "fixed_point": {"kappa": kappa, "delta_omega": delta_omega, "ic": ic},
        "thresholds": asdict(thr),
        "tau_range": [tau_min, tau_max],
        "memory_values": list(memory_values),
        "rows": rows,
        "n_glass_like": sum(1 for r in rows if r["glass_like"]),
        "recovery_model_counts": preferred_counts,
        "fraction_stretched": n_stretch / max(1, n_stretch + n_exp),
    }


# =============================================================================
# Plots
# =============================================================================
def _edges(vals: np.ndarray, geom: bool = False) -> np.ndarray:
    if len(vals) == 1:
        if geom:
            return np.array([vals[0] / 1.2, vals[0] * 1.2])
        return np.array([vals[0] - 0.05, vals[0] + 0.05])
    if geom:
        logv = np.log(vals)
        mids = 0.5 * (logv[:-1] + logv[1:])
        edges_log = np.concatenate(
            [[logv[0] - (mids[0] - logv[0])], mids, [logv[-1] + (logv[-1] - mids[-1])]]
        )
        return np.exp(edges_log)
    mids = 0.5 * (vals[:-1] + vals[1:])
    return np.concatenate(
        [[vals[0] - (mids[0] - vals[0])], mids, [vals[-1] + (vals[-1] - mids[-1])]]
    )


def plot_heatmaps(data: dict, out_path: Path) -> None:
    kappas = np.asarray(data["grid"]["kappas"], dtype=float)
    domegas = np.asarray(data["grid"]["domegas"], dtype=float)
    phase = np.asarray(data["arrays"]["phase_grid"], dtype=float)
    S = np.asarray(data["arrays"]["mean_survival"], dtype=float)
    identity = np.asarray(data["arrays"]["identity"], dtype=float)
    stab = np.asarray(data["arrays"]["stability_score"], dtype=float)

    x_edges = _edges(kappas, geom=False)
    y_edges = _edges(domegas, geom=True)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 9.5))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes.ravel():
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    def _style_cbar(cb) -> None:
        cb.ax.yaxis.set_tick_params(color="#c9d1d9")
        plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#c9d1d9")

    # Phase map
    ax = axes[0, 0]
    cmap = ListedColormap(PHASE_COLORS)
    ax.pcolormesh(x_edges, y_edges, phase, cmap=cmap, vmin=-0.5, vmax=3.5, shading="flat")
    ax.set_yscale("log")
    ax.set_xlabel("κ (gauge damping)")
    ax.set_ylabel("Δω (drive)")
    ax.set_title("Water-phase analog labels")
    for kval, label, ls in [
        (0.85, "κ_doc", "--"),
        (0.89, "κ_sim", ":"),
        (E / PI, "e/π", "-."),
    ]:
        ax.axvline(kval, color="#8b949e", ls=ls, lw=1.0, alpha=0.85)
        ax.text(
            kval, y_edges[-1] * 0.92, label,
            color="#8b949e", fontsize=7, ha="center", va="top", rotation=90,
        )
    ax.legend(
        handles=[
            Patch(facecolor=PHASE_COLORS[i], edgecolor="#30363d", label=INT_TO_PHASE[i])
            for i in range(4)
        ],
        loc="lower right",
        fontsize=8,
        framealpha=0.85,
    )

    # Mean survival
    ax = axes[0, 1]
    pcm = ax.pcolormesh(x_edges, y_edges, S, cmap="magma", shading="flat")
    ax.set_yscale("log")
    ax.set_xlabel("κ")
    ax.set_ylabel("Δω")
    ax.set_title("PDE mean survival S (fixed horizon)")
    _style_cbar(fig.colorbar(pcm, ax=ax, fraction=0.046, pad=0.04))

    # Identity
    ax = axes[1, 0]
    pcm = ax.pcolormesh(x_edges, y_edges, identity, cmap="viridis", shading="flat")
    ax.set_yscale("log")
    ax.set_xlabel("κ")
    ax.set_ylabel("Δω")
    ax.set_title("Lattice identity |⟨q, q₀⟩|")
    _style_cbar(fig.colorbar(pcm, ax=ax, fraction=0.046, pad=0.04))

    # Stability score (island-like)
    ax = axes[1, 1]
    pcm = ax.pcolormesh(x_edges, y_edges, stab, cmap="cividis", shading="flat")
    ax.set_yscale("log")
    ax.set_xlabel("κ")
    ax.set_ylabel("Δω")
    ax.set_title("Stability score  id / (1 + 10·burst)")
    _style_cbar(fig.colorbar(pcm, ax=ax, fraction=0.046, pad=0.04))

    counts = data["phase_counts"]
    ic = data["pde_settings"].get("ic", "helical")
    fig.suptitle(
        f"Water-phase analog · IC={ic}  |  "
        f"solid={counts.get('solid', 0)}  liquid={counts.get('liquid', 0)}  "
        f"vapor={counts.get('vapor', 0)}  super={counts.get('supercritical', 0)}",
        color="#e6edf3",
        fontsize=12,
        y=0.995,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_stress_ic(data: dict, out_path: Path) -> None:
    rows = data["rows"]
    ics = [r["ic"] for r in rows]
    S = [r["pde_mean_survival"] for r in rows]
    F = [r["pde_fluctuation_survival"] for r in rows]
    struct = [r["pde_structure_retention"] for r in rows]
    t_pers = [r.get("pde_persistence_time", 0.0) for r in rows]

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.5))
    fig.patch.set_facecolor("#0d1117")
    colors = ["#58a6ff", "#3fb950", "#d29922", "#f85149"]
    for ax in axes.ravel():
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    x = np.arange(len(ics))
    for ax, vals, title, ylab in [
        (axes[0, 0], S, "Mean survival S", "S"),
        (axes[0, 1], F, "Fluctuation survival F", "F"),
        (axes[1, 0], struct, "Structure retention", "struct_ret"),
        (axes[1, 1], t_pers, "Persistence time", "t_persist"),
    ]:
        ax.bar(x, vals, color=colors[: len(ics)], edgecolor="#30363d")
        ax.set_xticks(x)
        ax.set_xticklabels(ics, rotation=15, ha="right")
        ax.set_title(title)
        ax.set_ylabel(ylab)
        ax.grid(True, axis="y", alpha=0.25, color="#30363d")

    # Overlay structure decay traces if present
    # (small inset-style lines on structure panel via twin — skip; separate curves optional)

    fp = data["fixed_point"]
    thr = data.get("persist_threshold", DEFAULT_PERSIST_THRESH)
    fig.suptitle(
        f"IC stress @ κ={fp['kappa']:.3f}, Δω={fp['delta_omega']:.4f}  "
        f"(best struct: {data.get('best_ic_structure')}, "
        f"best persist: {data.get('best_ic_persistence')}, thr={thr})",
        color="#e6edf3",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Optional decay-curve companion plot
    if any(r.get("struct_ret_trace") for r in rows):
        fig2, ax2 = plt.subplots(figsize=(7.5, 4.5))
        fig2.patch.set_facecolor("#0d1117")
        ax2.set_facecolor("#161b22")
        ax2.tick_params(colors="#c9d1d9")
        ax2.xaxis.label.set_color("#c9d1d9")
        ax2.yaxis.label.set_color("#c9d1d9")
        ax2.title.set_color("#e6edf3")
        for spine in ax2.spines.values():
            spine.set_color("#30363d")
        for r, c in zip(rows, colors):
            t = r.get("struct_times", [])
            s = r.get("struct_ret_trace", [])
            if t and s:
                ax2.plot(t, s, color=c, lw=1.6, label=r["ic"])
        ax2.axhline(thr, color="#8b949e", ls="--", lw=1.0, label=f"persist thr={thr}")
        ax2.set_xlabel("time")
        ax2.set_ylabel("structure retention")
        ax2.set_yscale("log")
        ax2.set_title("Structure decay by IC seed")
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3, color="#30363d")
        fig2.tight_layout()
        decay_path = out_path.with_name(out_path.stem + "_decay.png")
        fig2.savefig(decay_path, dpi=140, facecolor=fig2.get_facecolor())
        plt.close(fig2)


def plot_stress_ic_map(data: dict, out_path: Path) -> None:
    cells = data["cells"]
    if not cells:
        return
    bands = [c["band"] for c in cells]
    ics = list(IC_CHOICES)
    # Heat of struct_ret per (band, ic)
    mat = np.zeros((len(bands), len(ics)))
    for i, c in enumerate(cells):
        by_ic = {r["ic"]: r["struct_ret"] for r in c["rows"]}
        for j, ic in enumerate(ics):
            mat[i, j] = by_ic.get(ic, 0.0)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes:
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    ax = axes[0]
    im = ax.imshow(np.log10(np.maximum(mat, 1e-12)), aspect="auto", cmap="magma")
    ax.set_xticks(range(len(ics)))
    ax.set_xticklabels(ics, rotation=20, ha="right")
    ax.set_yticks(range(len(bands)))
    ax.set_yticklabels(bands, fontsize=8)
    ax.set_title("log₁₀(struct_ret) by band × IC")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.yaxis.set_tick_params(color="#c9d1d9")
    plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#c9d1d9")
    # Mark winners
    for i, c in enumerate(cells):
        j = ics.index(c["best_ic_structure"]) if c["best_ic_structure"] in ics else -1
        if j >= 0:
            ax.plot(j, i, "o", mfc="none", mec="#3fb950", ms=12, mew=1.5)

    ax = axes[1]
    wins_s = data["wins_by_structure"]
    wins_p = data["wins_by_persistence"]
    x = np.arange(len(ics))
    w = 0.35
    ax.bar(x - w / 2, [wins_s[ic] for ic in ics], w, label="struct wins", color="#58a6ff")
    ax.bar(x + w / 2, [wins_p[ic] for ic in ics], w, label="persist wins", color="#3fb950")
    ax.set_xticks(x)
    ax.set_xticklabels(ics, rotation=15, ha="right")
    ax.set_ylabel("wins across bands")
    ax.set_title("Which seed wins where")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.25, color="#30363d")

    fig.suptitle(
        "IC stress map across (κ, Δω) bands  (green ○ = structure winner)",
        color="#e6edf3",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_recovery_slice(data: dict, out_path: Path) -> None:
    rows = data["rows"]
    mems = sorted({r["recovery_memory"] for r in rows})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes:
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        ax.xaxis.label.set_color("#c9d1d9")
        ax.yaxis.label.set_color("#c9d1d9")
        ax.title.set_color("#e6edf3")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    ax = axes[0]
    for mem in mems:
        sub = [r for r in rows if r["recovery_memory"] == mem]
        sub = sorted(sub, key=lambda r: r["recovery_tau"])
        ax.plot(
            [r["recovery_tau"] for r in sub],
            [r["pde_structure_retention"] for r in sub],
            "o-",
            label=f"memory={mem:.2f}",
        )
    ax.set_xscale("log")
    ax.set_xlabel("recovery τ")
    ax.set_ylabel("structure retention")
    ax.set_title("Final structure vs recovery τ")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, color="#30363d")

    # Model preference: fraction stretched vs τ (collapsed over memory)
    ax = axes[1]
    taus = sorted({r["recovery_tau"] for r in rows})
    frac_stretch = []
    mean_beta = []
    for tau in taus:
        sub = [r for r in rows if abs(r["recovery_tau"] - tau) < 1e-12]
        stretch = sum(1 for r in sub if r.get("recovery_preferred") == "stretched_exp")
        frac_stretch.append(stretch / max(1, len(sub)))
        betas = [r["recovery_beta"] for r in sub if r.get("recovery_beta") is not None]
        mean_beta.append(float(np.mean(betas)) if betas else np.nan)
    ax.plot(taus, frac_stretch, "s-", color="#d29922", label="frac stretched-exp")
    ax.set_xscale("log")
    ax.set_xlabel("recovery τ")
    ax.set_ylabel("fraction preferred stretched")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Recovery curve shape (exp vs Kohlrausch)")
    ax2 = ax.twinx()
    ax2.plot(taus, mean_beta, "o--", color="#58a6ff", alpha=0.85, label="mean β")
    ax2.set_ylabel("mean β", color="#58a6ff")
    ax2.tick_params(colors="#58a6ff")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3, color="#30363d")

    counts = data.get("recovery_model_counts", {})
    fig.suptitle(
        f"Recovery / glassiness  |  models: {counts}  |  "
        f"glass-like={data.get('n_glass_like', 0)}",
        color="#e6edf3",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(out_path, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)


# =============================================================================
# CLI
# =============================================================================
def _parse_threshold_overrides(args: argparse.Namespace) -> LabelThresholds:
    """Apply any --thr-FIELD=value overrides onto LABEL_THRESHOLDS."""
    base = asdict(LABEL_THRESHOLDS)
    for f in fields(LabelThresholds):
        cli_name = f"thr_{f.name}"
        val = getattr(args, cli_name, None)
        if val is not None:
            base[f.name] = val
    return LabelThresholds(**base)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Water-phase analog sweep (solid/liquid/vapor on Hopf lattice). "
            "Retune via LABEL_THRESHOLDS or --thr-* flags."
        )
    )
    # Grid
    parser.add_argument("--kappa-min", type=float, default=0.25)
    parser.add_argument("--kappa-max", type=float, default=1.15)
    parser.add_argument("--n-kappa", type=int, default=9)
    parser.add_argument("--domega-min", type=float, default=0.001)
    parser.add_argument("--domega-max", type=float, default=0.08)
    parser.add_argument("--n-domega", type=int, default=9)
    parser.add_argument("--nx", type=int, default=12)
    parser.add_argument("--nt", type=int, default=800)
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--n-sites", type=int, default=48)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--ic", choices=IC_CHOICES, default="helical")
    parser.add_argument("--quick", action="store_true", help="Tiny grid smoke test")
    # Modes
    parser.add_argument(
        "--stress-ic",
        action="store_true",
        help="Compare tetrahedral/hopfion/helical/uniform IC at fixed (κ, Δω)",
    )
    parser.add_argument(
        "--stress-ic-map",
        action="store_true",
        help="Multi-region IC stress: which seed wins across solid/liquid/vapor bands",
    )
    parser.add_argument(
        "--recovery-slice",
        action="store_true",
        help="Third-axis viscosity slice: recovery_tau × memory at fixed (κ, Δω)",
    )
    parser.add_argument("--fix-kappa", type=float, default=0.85, help="Fixed κ for stress modes")
    parser.add_argument(
        "--fix-domega", type=float, default=0.01, help="Fixed Δω for stress modes"
    )
    parser.add_argument(
        "--persist-threshold",
        type=float,
        default=DEFAULT_PERSIST_THRESH,
        help="Structure-retention floor for persistence_time (IC stress)",
    )
    # Threshold overrides (generated from LabelThresholds fields)
    for f in fields(LabelThresholds):
        parser.add_argument(
            f"--thr-{f.name.replace('_', '-')}",
            type=float,
            default=None,
            dest=f"thr_{f.name}",
            help=f"Override LabelThresholds.{f.name}",
        )

    args = parser.parse_args()
    thr = _parse_threshold_overrides(args)

    if args.quick:
        args.n_kappa = 5
        args.n_domega = 5
        args.nx = 10
        args.nt = 400
        args.frames = 60
        args.n_sites = 32

    # --- Mode: multi-region IC map ---
    if args.stress_ic_map:
        print("IC stress map across solid / liquid / vapor bands")
        data = run_stress_ic_map(
            nx=args.nx if not args.quick else 10,
            nt=args.nt if not args.quick else 400,
            frames=args.frames if not args.quick else 50,
            n_sites=args.n_sites if not args.quick else 24,
            seed=args.seed,
            thr=thr,
            persist_threshold=args.persist_threshold,
        )
        plot_path = OUTPUT_DIR / "water_phase_ic_stress_map.png"
        plot_stress_ic_map(data, plot_path)
        report_path = save_report("water_phase_ic_stress_map", data)
        print("\nWins by structure:", data["wins_by_structure"])
        print("Wins by persistence:", data["wins_by_persistence"])
        print(f"Wrote {plot_path}")
        print(f"Wrote {report_path}")
        return 0

    # --- Mode: IC stress test ---
    if args.stress_ic:
        print("IC stress test (tetrahedral / hopfion / helical / uniform)")
        print(f"  fixed κ={args.fix_kappa}, Δω={args.fix_domega}")
        data = run_stress_ic(
            kappa=args.fix_kappa,
            delta_omega=args.fix_domega,
            nx=args.nx,
            nt=args.nt,
            frames=args.frames,
            n_sites=args.n_sites,
            seed=args.seed,
            thr=thr,
            persist_threshold=args.persist_threshold,
        )
        plot_path = OUTPUT_DIR / "water_phase_ic_stress.png"
        plot_stress_ic(data, plot_path)
        report_path = save_report("water_phase_ic_stress", data)
        print(f"Best IC by structure: {data['best_ic_structure']}")
        print(f"Best IC by persistence: {data['best_ic_persistence']}")
        print(f"Wrote {plot_path}")
        print(f"Wrote {plot_path.with_name(plot_path.stem + '_decay.png')} (decay curves)")
        print(f"Wrote {report_path}")
        return 0

    # --- Mode: recovery / glassiness slice ---
    if args.recovery_slice:
        print("Recovery / glassiness slice (viscosity analog)")
        print(f"  fixed κ={args.fix_kappa}, Δω={args.fix_domega}, ic={args.ic}")
        data = run_recovery_slice(
            kappa=args.fix_kappa,
            delta_omega=args.fix_domega,
            nx=args.nx,
            nt=args.nt,
            seed=args.seed,
            ic=args.ic,
            thr=thr,
        )
        plot_path = OUTPUT_DIR / "water_phase_recovery_slice.png"
        plot_recovery_slice(data, plot_path)
        report_path = save_report("water_phase_recovery_slice", data)
        print(f"glass-like points: {data['n_glass_like']}")
        print(f"recovery models: {data['recovery_model_counts']}")
        print(f"fraction stretched: {data['fraction_stretched']:.2f}")
        print(f"Wrote {plot_path}")
        print(f"Wrote {report_path}")
        return 0

    # --- Default: κ × Δω phase map ---
    print("Water-phase analog sweep (interpretive — not H₂O thermo)")
    print(
        f"  grid {args.n_kappa}×{args.n_domega}  "
        f"κ∈[{args.kappa_min},{args.kappa_max}]  "
        f"Δω∈[{args.domega_min},{args.domega_max}] (geom)  IC={args.ic}"
    )

    data = run_sweep(
        kappa_min=args.kappa_min,
        kappa_max=args.kappa_max,
        n_kappa=args.n_kappa,
        domega_min=args.domega_min,
        domega_max=args.domega_max,
        n_domega=args.n_domega,
        nx=args.nx,
        nt=args.nt,
        frames=args.frames,
        n_sites=args.n_sites,
        seed=args.seed,
        ic=args.ic,
        thr=thr,
    )

    plot_path = OUTPUT_DIR / "water_phase_analog_heatmap.png"
    plot_heatmaps(data, plot_path)
    report_path = save_report("water_phase_analog_sweep", data)

    print("\nPhase counts:", data["phase_counts"])
    print(f"Wrote {plot_path}")
    print(f"Wrote {report_path}")
    print(
        "\nRetune: edit LabelThresholds / LABEL_THRESHOLDS at top of script, "
        "or pass --thr-solid-identity-min=… etc."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
