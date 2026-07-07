#!/usr/bin/env python3
"""
pde_survival_eigenstructure.py
================================
Spectral / eigenstructure explanation for κ-survival optimum κ ≈ 0.891.

The twist PDE mean mode obeys
    dθ̄/dt = Δω − κ θ̄ + (D/2) M(t),   M = ⟨cot(θ/2)|∇θ|²⟩
while fluctuations decay with Laplacian eigenvalues λ_k on T³ (periodic FD).

This script:
  1. Builds the 3D periodic FD Laplacian spectrum (nx=20 default)
  2. Solves the drive-shifted zero-mode survival at λt = 2
  3. Adds cot-flux + diffusion corrections via a fast spectral surrogate
  4. Compares κ_opt from the surrogate to the full PDE (seed=42)
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import E, OUTPUT_DIR, PHI, PI, save_report

R = PHI**2 + E**2 - PI**2
E_INV2 = float(np.exp(-2.0))
KAPPA_DOC = 0.85
KAPPA_SIM = 0.89
DELTA_OMEGA = 0.002
DT = 0.001
D_DEFAULT = 0.05
NX_DEFAULT = 20
SEED = 42


def load_relaxation_survival():
    path = Path.home() / "Projects" / "toe" / "src" / "relaxation_survival.py"
    spec = importlib.util.spec_from_file_location("relaxation_survival", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def laplacian_eigenvalue(nx: int, kx: int, ky: int, kz: int) -> float:
    """Positive eigenvalue Λ_k for −Δ on periodic FD stencil (matches toe PDE)."""
    h = 1.0 / nx
    val = 0.0
    for q in (kx, ky, kz):
        if q:
            val += 2.0 * (np.cos(2.0 * PI * q / nx) - 1.0) / h**2
    return -val


def spectrum_table(nx: int = NX_DEFAULT, top_n: int = 8) -> list[dict]:
    modes: list[tuple[int, int, int, float]] = []
    half = nx // 2
    for kx in range(half + 1):
        for ky in range(half + 1):
            for kz in range(half + 1):
                if kx == ky == kz == 0:
                    continue
                lam = laplacian_eigenvalue(nx, kx, ky, kz)
                modes.append((kx, ky, kz, lam))
    modes.sort(key=lambda t: t[3])
    rows = []
    for kx, ky, kz, lam in modes[:top_n]:
        rows.append({
            "k": [kx, ky, kz],
            "lambda_k": float(lam),
            "diffusion_rate_D_lambda": float(D_DEFAULT * lam),
        })
    return rows


def initial_theta(nx: int = NX_DEFAULT, seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.uniform(0.1, 2.0, (nx, nx, nx))


def mean_cot_grad(theta: np.ndarray, D: float = D_DEFAULT) -> float:
    g0, g1, g2 = np.gradient(theta)
    grad2 = g0**2 + g1**2 + g2**2
    with np.errstate(divide="ignore", invalid="ignore"):
        cot = np.cos(theta / 2.0) / np.maximum(np.sin(theta / 2.0), 1e-8)
    return float(np.mean(0.5 * D * cot * grad2))


def gradient_spectrum_weights(theta: np.ndarray, nx: int) -> tuple[np.ndarray, np.ndarray]:
    """Laplacian eigenvalues and weights for initial ⟨|∇δθ|²⟩ on the periodic grid."""
    delta = theta - float(theta.mean())
    half = nx // 2
    weights: list[float] = []
    lambdas: list[float] = []
    for kx in range(half + 1):
        for ky in range(half + 1):
            for kz in range(half + 1):
                if kx == ky == kz == 0:
                    continue
                lam = laplacian_eigenvalue(nx, kx, ky, kz)
                mode = np.ones((nx, nx, nx))
                if kx:
                    mode *= np.cos(2 * PI * kx * np.linspace(0, 1, nx, endpoint=False)[:, None, None])
                if ky:
                    mode *= np.cos(2 * PI * ky * np.linspace(0, 1, nx, endpoint=False)[None, :, None])
                if kz:
                    mode *= np.cos(2 * PI * kz * np.linspace(0, 1, nx, endpoint=False)[None, None, :])
                proj = float(np.mean(delta * mode))
                weights.append(proj**2 * lam)
                lambdas.append(lam)
    w = np.asarray(weights, dtype=float)
    lam = np.asarray(lambdas, dtype=float)
    total = w.sum()
    if total > 0:
        w /= total
    return lam, w


def n_steps_for_kappa(kappa: float, dt: float = DT) -> int:
    return max(1, int(round((2.0 / kappa) / dt)))


def zero_mode_survival_continuous(
    kappa: float,
    theta0_mean: float,
    delta_omega: float = DELTA_OMEGA,
) -> float:
    """S₀(κ) from dθ̄/dt = Δω − κθ̄ with λt = κT = 2."""
    theta_T = delta_omega / kappa + (theta0_mean - delta_omega / kappa) * E_INV2
    return theta_T / theta0_mean


def zero_mode_survival_euler(
    kappa: float,
    theta0_mean: float,
    delta_omega: float = DELTA_OMEGA,
    dt: float = DT,
    cot_flux: float = 0.0,
) -> float:
    theta_bar = theta0_mean
    for _ in range(n_steps_for_kappa(kappa, dt)):
        theta_bar += dt * (delta_omega - kappa * theta_bar + cot_flux)
    return theta_bar / theta0_mean


def kappa_null_zero_mode(theta0_mean: float, target: float = R) -> float:
    """κ solving S₀(κ)=target for the continuous zero-mode."""
    return DELTA_OMEGA * (1.0 - E_INV2) / ((target - E_INV2) * theta0_mean)


@dataclass
class SpectralCotState:
    theta0_mean: float
    G0: float
    lam: np.ndarray
    weights: np.ndarray


def build_spectral_cot_state(theta: np.ndarray) -> SpectralCotState:
    theta0_mean = float(theta.mean())
    delta = theta - theta0_mean
    g0, g1, g2 = np.gradient(delta)
    G0 = float(np.mean(g0**2 + g1**2 + g2**2))
    lam, weights = gradient_spectrum_weights(theta, theta.shape[0])
    return SpectralCotState(theta0_mean=theta0_mean, G0=G0, lam=lam, weights=weights)


def spectral_cot_survival(
    kappa: float,
    state: SpectralCotState,
    D: float = D_DEFAULT,
    dt: float = DT,
) -> float:
    """
    Mean equation with cot flux M(t) ≈ cot(θ̄/2)·⟨|∇δθ|²⟩(t),
    ⟨|∇δθ|²⟩(t) = G₀ Σ_k w_k exp(−2Dλ_k t) from the Laplacian spectrum.
    """
    theta_bar = state.theta0_mean
    n_steps = n_steps_for_kappa(kappa, dt)
    for step in range(n_steps):
        t = step * dt
        decay = np.exp(-2.0 * D * state.lam * t)
        grad_energy = state.G0 * float(np.sum(state.weights * decay))
        cot_fac = np.cos(theta_bar / 2.0) / max(np.sin(theta_bar / 2.0), 1e-8)
        theta_bar += dt * (
            DELTA_OMEGA - kappa * theta_bar + 0.5 * D * cot_fac * grad_energy
        )
    return theta_bar / state.theta0_mean


def find_best_kappa(
    evaluator,
    kappa_min: float = 0.80,
    kappa_max: float = 0.92,
    n_points: int = 161,
    target: float = R,
) -> dict:
    kappas = np.linspace(kappa_min, kappa_max, n_points)
    best = {"delta_abs": float("inf"), "kappa": None, "survival": None}
    rows = []
    for kappa in kappas:
        surv = float(evaluator(float(kappa)))
        delta = abs(surv - target)
        rows.append({"kappa": float(kappa), "survival": surv, "delta_abs": delta})
        if delta < best["delta_abs"]:
            best = {"kappa": float(kappa), "survival": surv, "delta_abs": delta}
    best["delta_pct_vs_R"] = 100.0 * best["delta_abs"] / abs(target)
    return {"best": best, "curve": rows}


def main() -> int:
    theta = initial_theta()
    theta0_mean = float(theta.mean())
    M0_full = mean_cot_grad(theta)
    kappa_0 = kappa_null_zero_mode(theta0_mean)

    rs = load_relaxation_survival()

    cot_state = build_spectral_cot_state(theta)

    models = {
        "zero_mode_continuous": lambda k: zero_mode_survival_continuous(k, theta0_mean),
        "zero_mode_euler": lambda k: zero_mode_survival_euler(k, theta0_mean),
        "zero_mode_euler_plus_mean_M0": lambda k: zero_mode_survival_euler(
            k, theta0_mean, cot_flux=M0_full
        ),
        "spectral_cot_surrogate": lambda k: spectral_cot_survival(k, cot_state),
    }

    model_results = {}
    for name, fn in models.items():
        model_results[name] = find_best_kappa(fn, n_points=81)

    # sparse full-PDE reference (5 spot checks + reuse sweep optimum)
    pde_spot = {}
    for kappa in [kappa_0, KAPPA_DOC, 0.8909, KAPPA_SIM]:
        r = rs.simulate_twist_pde_survival(
            kappa=float(kappa), seed=SEED, dt=DT, D=D_DEFAULT, nx=NX_DEFAULT
        )
        pde_spot[f"{kappa:.4f}"] = {
            "mean_survival": r["survival"]["mean_survival"],
            "delta_pct_vs_R": r["analog_comparisons"]["mean_survival"]["delta_pct_vs_R"],
            "n_steps": r["normalization"]["n_steps"],
        }

    sweep_path = sorted(OUTPUT_DIR.glob("kappa_survival_sweep_*.json"))[-1]
    sweep_data = __import__("json").loads(sweep_path.read_text())
    pde_best_row = sweep_data["best_vs_R"]
    pde_best = {
        "kappa": pde_best_row["kappa"],
        "survival": pde_best_row["mean_survival"],
        "delta_abs": abs(pde_best_row["mean_survival"] - R),
        "delta_pct_vs_R": pde_best_row["delta_pct_vs_R"],
        "source": str(sweep_path.name),
    }

    shift = model_results["spectral_cot_surrogate"]["best"]["kappa"] - kappa_0

    result = {
        "derivation": "notes/pde_survival_eigenstructure.md",
        "reference": {
            "R": R,
            "e_inv2": E_INV2,
            "kappa_doc": KAPPA_DOC,
            "kappa_sim": KAPPA_SIM,
            "theta0_mean_seed42": theta0_mean,
            "M0_mean_cot_grad": M0_full,
        },
        "spectrum_nx20": spectrum_table(),
        "zero_mode_null": {
            "kappa_0": kappa_0,
            "S_at_kappa_0_continuous": zero_mode_survival_continuous(kappa_0, theta0_mean),
            "interpretation": "pure gauge zero mode without cot/diffusion corrections",
        },
        "models": {
            name: {
                "best_kappa": res["best"]["kappa"],
                "best_survival": res["best"]["survival"],
                "delta_pct_vs_R": res["best"]["delta_pct_vs_R"],
            }
            for name, res in model_results.items()
        },
        "pde_reference": {
            "spot_checks": pde_spot,
            "sweep_best": pde_best,
        },
        "shift_analysis": {
            "kappa_0_to_spectral_best": float(shift),
            "kappa_0_to_pde_best": float(pde_best["kappa"] - kappa_0),
            "mechanism": "cot(θ/2)|∇θ|² flux boosts θ̄; stronger κ needed to hit R",
        },
        "pass_criteria": {
            "pde_best_near_089": abs(pde_best["kappa"] - 0.891) < 0.015,
            "zero_mode_below_pde": kappa_0 < pde_best["kappa"],
            "spectral_above_zero": kappa_0 < model_results["spectral_cot_surrogate"]["best"]["kappa"],
        },
    }
    result["pass"] = all(result["pass_criteria"].values())

    path = save_report("pde_survival_eigenstructure", result)

    print("=== PDE Survival Eigenstructure ===")
    print(f"R = {R:.6f}   θ̄₀ (seed {SEED}) = {theta0_mean:.6f}")
    print(f"κ₀ (zero-mode null) = {kappa_0:.4f}")
    print(f"M₀ = ⟨cot(θ/2)|∇θ|²⟩ mean = {M0_full:.6e}")
    print()
    for name, res in model_results.items():
        b = res["best"]
        print(f"{name:32s}  κ*={b['kappa']:.4f}  S={b['survival']:.6f}  Δ%={b['delta_pct_vs_R']:.4f}%")
    pb = pde_best
    print(f"{'full_pde (sweep)':32s}  κ*={pb['kappa']:.4f}  S={pb['survival']:.6f}  Δ%={pb['delta_pct_vs_R']:.4f}%")
    print()
    print(f"Shift κ₀ → PDE best: {result['shift_analysis']['kappa_0_to_pde_best']:+.4f}")
    print(f"Overall: {'PASS' if result['pass'] else 'FAIL'}")
    print(f"Report: {path}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())