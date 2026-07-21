#!/usr/bin/env python3
"""
cusp_resonance_probe.py
=======================
Burst-threshold / cusp resonance analysis:

1. Cardioid envelope on twist / harmonic synthesis
2. Track θ_crit behaviour with a cardioid modulation term
3. Quantify whether the cusp acts as a high-gradient zone for φ-e-π alignment
4. FFT comparison before/after cardioid modulation
5. 350/π as a critical accumulation scale for cusp coherence

Complements pde_relaxation_probe.py and cardioid_golden_angle_probe.py.
Keeps math diagnostics separate from interpretive language.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    DEFAULT_KAPPA,
    E,
    GOLDEN_ANGLE_DEG,
    GOLDEN_ANGLE_FRACTION,
    OUTPUT_DIR,
    PHI,
    PI,
    R_RESIDUAL,
    save_report,
)

GOLDEN_ANGLE_RAD = float(np.radians(GOLDEN_ANGLE_DEG))
W_G = 350.0 / PI
NINE_OVER_PI_RAD = 9.0 / PI
CUSP_HALF_WIDTH = 0.25  # rad — shared with cardioid_golden_angle_probe

# ---------------------------------------------------------------------------
# Metric formulas (mathematical layer — explicit, reproducible)
# ---------------------------------------------------------------------------
# θ_crit = π(1 + κ)                     operational burst sink
# a_k = 1 + A · cos(θ_k)                cardioid amp (A = cardioid_amp)
# holonomy_k = (a_k · θ_k) mod [2π(1+κ)]  amp-weighted angular sample
# burst_mask_k = 1  iff  holonomy_k > θ_crit
# burst_fraction = (1/N) Σ burst_mask_k
#
# radial_collapse = mean(a | bulk) / mean(a | cusp)
#   cusp ⇔ |θ − π| ≤ w,  bulk = complement
#
# polar curvature proxy (finite-diff r(θ)):
#   κ_curve = |r² + 2(r')² − r r''| / (r² + (r')²)^{3/2}
#   curvature_ratio = mean(κ_curve|cusp) / mean(κ_curve|bulk)
#
# cusp_coherence (scale sweep):
#   sens = curvature_ratio · radial_collapse
#   cusp_coherence = sens · (1 + burst_fraction) · 1/(1 + |align − R|)
# ---------------------------------------------------------------------------


def theta_crit(kappa: float = DEFAULT_KAPPA) -> float:
    """Operational burst threshold: θ_crit = π(1 + κ)."""
    return PI * (1.0 + kappa)


def cardioid_envelope(theta: np.ndarray) -> np.ndarray:
    """r(θ) = 1 + cos(θ); cusp at θ = π."""
    return 1.0 + np.cos(theta)


def harmonic_synthesis(
    n: int,
    *,
    step_rad: float = GOLDEN_ANGLE_RAD,
    kappa: float = DEFAULT_KAPPA,
    cardioid_amp: float = 0.0,
    seed: int = 0,
) -> dict:
    """
    1D angular harmonic chain with optional cardioid amplitude modulation.

    θ_k = k·step mod 2π
    a_k = 1 + cardioid_amp · cos(θ_k)     (cardioid_amp=0 → flat)
    s_k = a_k · sin(θ_k + φ_k)

    Holonomy proxy and burst:
        holonomy_k = (a_k · θ_k) mod 2π(1+κ)
        burst_fraction = mean( holonomy_k > θ_crit ),  θ_crit = π(1+κ)
    """
    rng = np.random.default_rng(seed)
    k = np.arange(n, dtype=float)
    theta = (k * step_rad) % (2.0 * PI)
    amp = 1.0 + cardioid_amp * np.cos(theta)
    phase = 0.05 * rng.standard_normal(n)
    signal = amp * np.sin(theta + phase)

    t_crit = theta_crit(kappa)
    # amp-weighted holonomy sample in [0, 2π(1+κ))
    holonomy = (amp * theta) % (2.0 * PI * (1.0 + kappa))
    burst_mask = holonomy > t_crit
    burst_excess = np.where(burst_mask, holonomy - t_crit, 0.0)

    return {
        "theta": theta,
        "amp": amp,
        "signal": signal,
        "holonomy": holonomy,
        "burst_mask": burst_mask,
        "burst_excess": burst_excess,
        "theta_crit": float(t_crit),
        "kappa": float(kappa),
        "cardioid_amp": float(cardioid_amp),
        "n_burst": int(np.sum(burst_mask)),
        # burst_fraction = (1/N) Σ 1[holonomy_k > θ_crit]
        "burst_fraction": float(np.mean(burst_mask)),
        "burst_fraction_formula": "mean( holonomy_k > θ_crit ), holonomy=(a·θ) mod 2π(1+κ)",
        "mean_amp": float(np.mean(amp)),
        "std_amp": float(np.std(amp)),
        "mean_signal": float(np.mean(signal)),
        "std_signal": float(np.std(signal)),
    }


def cusp_gradient_metrics(theta: np.ndarray, amp: np.ndarray, signal: np.ndarray) -> dict:
    """
    Cusp sensitivity around θ ≈ π.

    For r = 1 + cos(θ): first derivative r' = −sin(θ) vanishes at the cusp,
    but curvature diverges as r → 0. We therefore report:
      - radial collapse (mean amp near cusp vs bulk)
      - curvature proxy |r² + 2(r')² − r r''| / (r² + (r')²)^{3/2}
      - first-derivative ratio only as a secondary diagnostic
    """
    d = np.abs(((theta - PI + PI) % (2.0 * PI)) - PI)
    half = 0.25
    near = d <= half
    far = d > half

    # Analytic cardioid derivatives when amp tracks 1 + a cos θ (a from std)
    # Finite-diff first derivative for general amp
    order = np.argsort(theta)
    th_s = theta[order]
    amp_s = amp[order]
    dth = np.diff(th_s, append=th_s[0] + 2.0 * PI)
    damp = np.diff(amp_s, append=amp_s[0])
    r_prime = damp / (dth + 1e-12)
    r_pp = np.diff(r_prime, append=r_prime[0]) / (dth + 1e-12)
    # Curvature of polar graph r(θ): κ = |r² + 2(r')² − r r''| / (r² + (r')²)^{3/2}
    r = amp_s
    num = np.abs(r**2 + 2.0 * r_prime**2 - r * r_pp)
    den = (r**2 + r_prime**2 + 1e-12) ** 1.5
    curv = num / den
    curv_full = np.zeros_like(amp)
    grad_full = np.zeros_like(amp)
    curv_full[order] = curv
    grad_full[order] = np.abs(r_prime)

    mean_curv_cusp = float(np.mean(curv_full[near])) if near.any() else float("nan")
    mean_curv_bulk = float(np.mean(curv_full[far])) if far.any() else float("nan")
    curv_ratio = (
        mean_curv_cusp / mean_curv_bulk
        if mean_curv_bulk and mean_curv_bulk > 1e-12
        else float("nan")
    )

    mean_grad_cusp = float(np.mean(grad_full[near])) if near.any() else float("nan")
    mean_grad_bulk = float(np.mean(grad_full[far])) if far.any() else float("nan")
    grad_ratio = (
        mean_grad_cusp / mean_grad_bulk
        if mean_grad_bulk and mean_grad_bulk > 1e-12
        else float("nan")
    )

    mean_amp_cusp = float(np.mean(amp[near])) if near.any() else float("nan")
    mean_amp_bulk = float(np.mean(amp[far])) if far.any() else float("nan")
    collapse_ratio = (
        mean_amp_bulk / (mean_amp_cusp + 1e-12)
        if mean_amp_cusp == mean_amp_cusp
        else float("nan")
    )

    # Alignment: signal energy near triangle angles vs residual scale
    targets = np.radians([31.0, 59.9, 89.1])  # φ-e-π triangle angles
    support = []
    for t in targets:
        dd = np.abs(((theta - t + PI) % (2.0 * PI)) - PI)
        w = np.exp(-0.5 * (dd / 0.2) ** 2)
        support.append(float(np.average(np.abs(signal), weights=w + 1e-12)))
    mean_support = float(np.mean(support))

    is_sensitive = bool(
        (collapse_ratio > 1.2 if collapse_ratio == collapse_ratio else False)
        or (curv_ratio > 1.2 if curv_ratio == curv_ratio else False)
    )

    return {
        "mean_amp_cusp": mean_amp_cusp,
        "mean_amp_bulk": mean_amp_bulk,
        # radial_collapse = mean(a|bulk) / mean(a|cusp)
        "radial_collapse_ratio_bulk_over_cusp": float(collapse_ratio),
        "radial_collapse_formula": "mean(a|bulk) / mean(a|cusp)",
        "mean_curvature_cusp": mean_curv_cusp,
        "mean_curvature_bulk": mean_curv_bulk,
        "curvature_ratio_cusp_over_bulk": float(curv_ratio),
        "curvature_formula": "|r²+2(r')²−r r''| / (r²+(r')²)^{3/2}",
        "mean_grad_cusp": mean_grad_cusp,
        "mean_grad_bulk": mean_grad_bulk,
        "grad_ratio_cusp_over_bulk": float(grad_ratio),
        "cusp_is_high_sensitivity": is_sensitive,
        "cusp_is_high_gradient": is_sensitive,  # back-compat alias
        "phi_e_pi_signal_support": mean_support,
        "delta_support_vs_R": float(mean_support - R_RESIDUAL),
        "points_near_cusp": int(np.sum(near)),
        "mean_abs_signal_cusp": float(np.mean(np.abs(signal[near]))) if near.any() else float("nan"),
        "mean_abs_signal_bulk": float(np.mean(np.abs(signal[far]))) if far.any() else float("nan"),
        "note": (
            "Cardioid cusp: r'→0 but curvature → ∞ as r→0. "
            "Prefer radial_collapse_ratio and curvature_ratio over first-derivative grad_ratio."
        ),
    }


def fft_region_compare(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
    theta: np.ndarray,
    *,
    label_a: str = "unmodulated",
    label_b: str = "cardioid",
) -> dict:
    """FFT power comparison global + cusp-window samples (interpolated)."""

    def power_spectrum(sig: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        sig = sig - np.mean(sig)
        spec = np.fft.rfft(sig)
        p = np.abs(spec) ** 2
        freqs = np.fft.rfftfreq(len(sig), d=1.0)
        return freqs, p

    fa, pa = power_spectrum(signal_a)
    fb, pb = power_spectrum(signal_b)

    # Top modes
    def top_modes(freqs, power, k=5):
        idx = np.argsort(power)[::-1][:k]
        return [
            {"freq": float(freqs[i]), "power_frac": float(power[i] / (power.sum() + 1e-12))}
            for i in idx
        ]

    # Cusp-window restriction: take samples near π, pad to same length via histogram
    d = np.abs(((theta - PI + PI) % (2.0 * PI)) - PI)
    near = d <= 0.35
    n_bins = 64

    def cusp_signal(sig: np.ndarray) -> np.ndarray:
        # Angular histogram of |signal| near cusp for comparable FFT length
        th_n = theta[near]
        s_n = np.abs(sig[near])
        if th_n.size < 4:
            return np.zeros(n_bins)
        hist, _ = np.histogram(th_n, bins=n_bins, range=(PI - 0.35, PI + 0.35), weights=s_n)
        return hist.astype(float)

    ca, pa_c = power_spectrum(cusp_signal(signal_a))
    cb, pb_c = power_spectrum(cusp_signal(signal_b))

    # Spectral shift: mean frequency weighted by power
    def mean_f(freqs, power):
        return float((freqs * power).sum() / (power.sum() + 1e-12))

    return {
        "global": {
            label_a: {"top_modes": top_modes(fa, pa), "mean_freq": mean_f(fa, pa), "total_power": float(pa.sum())},
            label_b: {"top_modes": top_modes(fb, pb), "mean_freq": mean_f(fb, pb), "total_power": float(pb.sum())},
        },
        "cusp_window": {
            label_a: {"mean_freq": mean_f(ca, pa_c), "total_power": float(pa_c.sum())},
            label_b: {"mean_freq": mean_f(cb, pb_c), "total_power": float(pb_c.sum())},
        },
        "power_ratio_mod_over_raw": float(pb.sum() / (pa.sum() + 1e-12)),
        "cusp_power_ratio_mod_over_raw": float(pb_c.sum() / (pa_c.sum() + 1e-12)),
    }


def kappa_burst_sweep(
    kappas: np.ndarray,
    *,
    n: int = 256,
    cardioid_amp: float = 0.5,
    step_rad: float = GOLDEN_ANGLE_RAD,
) -> list[dict]:
    """How burst fraction and cusp gradient depend on κ with cardioid on/off."""
    rows = []
    for k in kappas:
        raw = harmonic_synthesis(n, step_rad=step_rad, kappa=float(k), cardioid_amp=0.0)
        mod = harmonic_synthesis(n, step_rad=step_rad, kappa=float(k), cardioid_amp=cardioid_amp)
        g_raw = cusp_gradient_metrics(raw["theta"], raw["amp"], raw["signal"])
        g_mod = cusp_gradient_metrics(mod["theta"], mod["amp"], mod["signal"])
        rows.append({
            "kappa": float(k),
            "theta_crit": float(theta_crit(float(k))),
            "burst_frac_raw": raw["burst_fraction"],
            "burst_frac_mod": mod["burst_fraction"],
            "burst_delta": mod["burst_fraction"] - raw["burst_fraction"],
            "grad_ratio_mod": g_mod["grad_ratio_cusp_over_bulk"],
            "curvature_ratio_mod": g_mod["curvature_ratio_cusp_over_bulk"],
            "radial_collapse_mod": g_mod["radial_collapse_ratio_bulk_over_cusp"],
            "alignment_mod": g_mod["phi_e_pi_signal_support"],
            "alignment_raw": g_raw["phi_e_pi_signal_support"],
        })
    return rows


def scale_accumulation_sweep(
    *,
    base: float = W_G,
    cardioid_amp: float = 0.5,
    kappa: float = DEFAULT_KAPPA,
    factors: list[float] | None = None,
) -> list[dict]:
    """Cusp coherence vs N ~ factor × 350/π."""
    if factors is None:
        factors = [0.25, 0.5, 1.0, 1.5, 2.0, PHI, 3.0, PI, 4.0]
    rows = []
    for f in factors:
        n = max(16, int(round(base * f)))
        mod = harmonic_synthesis(n, kappa=kappa, cardioid_amp=cardioid_amp)
        raw = harmonic_synthesis(n, kappa=kappa, cardioid_amp=0.0)
        g = cusp_gradient_metrics(mod["theta"], mod["amp"], mod["signal"])
        fft = fft_region_compare(raw["signal"], mod["signal"], mod["theta"])
        curv = g["curvature_ratio_cusp_over_bulk"]
        coll = g["radial_collapse_ratio_bulk_over_cusp"]
        sens = (curv if curv == curv else 1.0) * (coll if coll == coll else 1.0)
        coherence = (
            sens
            * (1.0 + mod["burst_fraction"])
            * (1.0 / (1.0 + abs(g["delta_support_vs_R"])))
        )
        rows.append({
            "factor": float(f),
            "n": n,
            "n_over_W_g": float(n / base),
            "burst_fraction": mod["burst_fraction"],
            "grad_ratio": g["grad_ratio_cusp_over_bulk"],
            "curvature_ratio": g["curvature_ratio_cusp_over_bulk"],
            "radial_collapse_ratio": g["radial_collapse_ratio_bulk_over_cusp"],
            "alignment_support": g["phi_e_pi_signal_support"],
            "cusp_power_ratio": fft["cusp_power_ratio_mod_over_raw"],
            "cusp_coherence": float(coherence),
        })
    return rows


def plot_cusp_resonance(
    raw: dict,
    mod: dict,
    kappa_rows: list[dict],
    scale_rows: list[dict],
    fft: dict,
    path: Path,
) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))

    # 1. Amplitude vs θ
    ax = axes[0, 0]
    order = np.argsort(raw["theta"])
    ax.plot(raw["theta"][order], raw["amp"][order], color="#457b9d", lw=1.2, label="raw amp=1")
    ax.plot(mod["theta"][order], mod["amp"][order], color="#e63946", lw=1.2, label="cardioid amp")
    ax.axvline(PI, color="#333", ls="--", lw=0.9, label="cusp θ=π")
    ax.set_xlabel("θ (rad)")
    ax.set_ylabel("amplitude")
    ax.set_title("Cardioid envelope")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    # 2. Signal
    ax = axes[0, 1]
    ax.plot(raw["signal"], color="#457b9d", alpha=0.7, lw=0.8, label="raw")
    ax.plot(mod["signal"], color="#e63946", alpha=0.7, lw=0.8, label="cardioid")
    ax.set_xlabel("step k")
    ax.set_ylabel("signal")
    ax.set_title("Harmonic synthesis")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    # 3. Holonomy vs θ_crit
    ax = axes[0, 2]
    ax.scatter(mod["theta"], mod["holonomy"], s=8, c=mod["burst_mask"], cmap="coolwarm", alpha=0.7)
    ax.axhline(mod["theta_crit"], color="#c9a227", ls="--", label=f"θ_crit={mod['theta_crit']:.3f}")
    ax.set_xlabel("θ")
    ax.set_ylabel("holonomy proxy")
    ax.set_title("Burst mask (cardioid)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    # 4. κ sweep burst fractions
    ax = axes[1, 0]
    ks = [r["kappa"] for r in kappa_rows]
    ax.plot(ks, [r["burst_frac_raw"] for r in kappa_rows], "o-", color="#457b9d", label="raw")
    ax.plot(ks, [r["burst_frac_mod"] for r in kappa_rows], "s-", color="#e63946", label="cardioid")
    ax.axvline(DEFAULT_KAPPA, color="#333", ls=":", label=f"κ_doc={DEFAULT_KAPPA}")
    ax.set_xlabel("κ")
    ax.set_ylabel("burst fraction")
    ax.set_title("Burst-threshold vs κ")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    # 5. Scale sweep
    ax = axes[1, 1]
    xs = [r["n_over_W_g"] for r in scale_rows]
    ax.plot(xs, [r["cusp_coherence"] for r in scale_rows], "o-", color="#6a4c93", label="coherence")
    ax.plot(
        xs,
        [r.get("curvature_ratio", r["grad_ratio"]) for r in scale_rows],
        "s--",
        color="#2a9d8f",
        alpha=0.8,
        label="curvature ratio",
    )
    ax.axvline(1.0, color="#c9a227", ls="--", label="N=350/π")
    ax.set_xlabel("N / (350/π)")
    ax.set_ylabel("metric")
    ax.set_title("Accumulation scale 350/π")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    # 6. FFT bar comparison
    ax = axes[1, 2]
    labels = ["global raw", "global mod", "cusp raw", "cusp mod"]
    g = fft["global"]
    c = fft["cusp_window"]
    vals = [
        g["unmodulated"]["total_power"],
        g["cardioid"]["total_power"],
        c["unmodulated"]["total_power"],
        c["cardioid"]["total_power"],
    ]
    # Normalize for display
    vals_n = np.array(vals) / (max(vals) + 1e-12)
    colors = ["#457b9d", "#e63946", "#457b9d", "#e63946"]
    ax.bar(labels, vals_n, color=colors, alpha=0.8, edgecolor="#333")
    ax.set_ylabel("relative total power")
    ax.set_title("FFT power (normalized)")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(alpha=0.3, axis="y")

    fig.suptitle(
        f"Cusp resonance · κ={mod['kappa']} · θ_crit={mod['theta_crit']:.3f} · "
        f"cardioid_amp={mod['cardioid_amp']} · R={R_RESIDUAL:.4f}",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cusp / burst-threshold resonance probe")
    parser.add_argument("--n", type=int, default=512)
    parser.add_argument("--kappa", type=float, default=DEFAULT_KAPPA)
    parser.add_argument("--cardioid-amp", type=float, default=0.5)
    parser.add_argument("--step", choices=("golden", "nine_pi"), default="golden")
    args = parser.parse_args()

    step_rad = GOLDEN_ANGLE_RAD if args.step == "golden" else NINE_OVER_PI_RAD
    step_name = "golden" if args.step == "golden" else "9/π"

    raw = harmonic_synthesis(
        args.n, step_rad=step_rad, kappa=args.kappa, cardioid_amp=0.0, seed=42
    )
    mod = harmonic_synthesis(
        args.n, step_rad=step_rad, kappa=args.kappa, cardioid_amp=args.cardioid_amp, seed=42
    )
    g_raw = cusp_gradient_metrics(raw["theta"], raw["amp"], raw["signal"])
    g_mod = cusp_gradient_metrics(mod["theta"], mod["amp"], mod["signal"])
    fft = fft_region_compare(raw["signal"], mod["signal"], mod["theta"])

    kappas = np.linspace(0.75, 0.95, 21)
    kappa_rows = kappa_burst_sweep(
        kappas, n=min(args.n, 256), cardioid_amp=args.cardioid_amp, step_rad=step_rad
    )
    scale_rows = scale_accumulation_sweep(
        base=W_G, cardioid_amp=args.cardioid_amp, kappa=args.kappa
    )
    best_scale = max(scale_rows, key=lambda r: r["cusp_coherence"])
    best_kappa = min(kappa_rows, key=lambda r: abs(r["alignment_mod"] - R_RESIDUAL))

    plot_path = OUTPUT_DIR / "cusp_resonance_probe.png"
    plot_cusp_resonance(raw, mod, kappa_rows, scale_rows, fft, plot_path)

    # Strip arrays for JSON
    def slim(h: dict) -> dict:
        return {k: v for k, v in h.items() if k not in (
            "theta", "amp", "signal", "holonomy", "burst_mask", "burst_excess"
        )}

    payload = {
        "step": step_name,
        "step_rad": float(step_rad),
        "n": args.n,
        "kappa": args.kappa,
        "theta_crit": float(theta_crit(args.kappa)),
        "cardioid_amp": args.cardioid_amp,
        "W_g": float(W_G),
        "R_residual": float(R_RESIDUAL),
        "golden_fraction": float(GOLDEN_ANGLE_FRACTION),
        "raw": slim(raw),
        "modulated": slim(mod),
        "gradient_raw": g_raw,
        "gradient_modulated": g_mod,
        "fft": fft,
        "kappa_sweep": kappa_rows,
        "scale_sweep_350_over_pi": scale_rows,
        "best_scale": best_scale,
        "best_kappa_for_alignment": best_kappa,
        "plot": str(plot_path),
        "summary": {
            "cusp_high_sensitivity": g_mod["cusp_is_high_sensitivity"],
            "radial_collapse_ratio": g_mod["radial_collapse_ratio_bulk_over_cusp"],
            "curvature_ratio": g_mod["curvature_ratio_cusp_over_bulk"],
            "grad_ratio": g_mod["grad_ratio_cusp_over_bulk"],
            "burst_frac_delta": mod["burst_fraction"] - raw["burst_fraction"],
            "fft_cusp_power_ratio": fft["cusp_power_ratio_mod_over_raw"],
            "best_n_over_Wg": best_scale["n_over_W_g"],
            "best_coherence": best_scale["cusp_coherence"],
        },
        "metric_formulas": {
            "theta_crit": "π(1+κ)",
            "amplitude": "a_k = 1 + A·cos(θ_k)",
            "burst_fraction": "mean(holonomy_k > θ_crit), holonomy=(a·θ) mod 2π(1+κ)",
            "radial_collapse": "mean(a|bulk) / mean(a|cusp)",
            "curvature_ratio": "mean(κ_curve|cusp) / mean(κ_curve|bulk)",
            "cusp_coherence": (
                "curvature_ratio · radial_collapse · (1+burst_frac) · 1/(1+|align−R|)"
            ),
        },
        "interpretation": (
            "Cardioid modulation collapses radius at θ≈π (cusp) with elevated polar curvature. "
            "Burst fraction vs κ and cusp FFT power quantify threshold sensitivity. "
            "N near 350/π is a candidate accumulation scale for coherence — empirical "
            "diagnostic, not a derived identity."
        ),
    }
    report_path = save_report("cusp_resonance_probe", payload)

    print("=== Cusp Resonance / Burst-Threshold Probe ===")
    print(f"step={step_name}  N={args.n}  κ={args.kappa}  θ_crit={theta_crit(args.kappa):.4f}  "
          f"cardioid_amp={args.cardioid_amp}")
    print(f"Burst fraction: raw={raw['burst_fraction']:.4f}  mod={mod['burst_fraction']:.4f}  "
          f"Δ={mod['burst_fraction']-raw['burst_fraction']:+.4f}")
    print(
        f"Cusp sensitivity (mod): collapse={g_mod['radial_collapse_ratio_bulk_over_cusp']:.3f}  "
        f"curv_ratio={g_mod['curvature_ratio_cusp_over_bulk']:.3f}  "
        f"high_sensitivity={g_mod['cusp_is_high_sensitivity']}"
    )
    print(f"φ-e-π signal support: raw={g_raw['phi_e_pi_signal_support']:.4f}  "
          f"mod={g_mod['phi_e_pi_signal_support']:.4f}  (R={R_RESIDUAL:.4f})")
    print(f"FFT cusp power ratio mod/raw: {fft['cusp_power_ratio_mod_over_raw']:.3f}")
    print(f"Best 350/π scale: N={best_scale['n']} (×{best_scale['factor']:.3f})  "
          f"coherence={best_scale['cusp_coherence']:.4f}")
    print(f"Report: {report_path}")
    print(f"Plot:   {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
