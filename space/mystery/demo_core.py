"""Shared φ-e-π analysis helpers for Mystery Gradio and HF Spaces."""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PHI = (1.0 + np.sqrt(5.0)) / 2.0
E = np.e
PI = np.pi

R = PHI**2 + E**2 - PI**2
E_OVER_PI = E / PI
KAPPA_DOC = 0.85

BOOT_QUOTE_STRING = "TEST EVERYTHING, HOLD FAST WHAT IS GOOD AND KNOW YOUR GOD"

HF_SPACE_URL = "https://huggingface.co/spaces/kinaar111/mystery"
GITHUB_URL = "https://github.com/kinaar8340/mystery"
TOE_URL = "https://github.com/kinaar8340/toe"
WALLPAPER_URL = f"{GITHUB_URL}/raw/main/mystery_image.png"

SIMULATION_BANNER_MD = """
> **Numerical probe** — browser-based φ²+e²≈π² analysis, κ holonomy-gap scaling, and
> 30-60-90 comparison. Outputs are reproducible numpy/matplotlib figures — not live PDE or
> conduit simulation. Full probe suite: `python run_all.py` locally.
"""

ONBOARDING_MD = """
### φ, e, π — emergent signature, not forced identity
The near-Pythagorean residual **R = φ²+e²−π² ≈ +0.137** (~1.4% relative error) defines a
triangle whose angles land near **31° / 60° / 90°** — and whose tens digits echo **3-6-9**
vortex geometry. This Space runs the core numerical checks interactively.

### Three steps (60 seconds)
1. **Adjust κ** on the slider (documented κ = 0.85 is marked).
2. **Run analysis** — read metrics for R, B(κ), κ*, and angle/369 tens.
3. **View figures** — φ-e-π triangle comparison and κ sweep (open **Figures** tab).

### What the metrics mean
| Metric | Plain English |
|--------|----------------|
| **R** | Pythagorean residual φ²+e²−π² — the central near-miss. |
| **B(κ)** | Holonomy-gap bound π²(e/π−κ) from effective Skyrme reduction. |
| **κ*** | κ that exactly nulls B(κ)−R: κ* = e/π − R/π². |
| **369 tens** | Each angle ÷10° — proximity to 3, 6, 9 vortex positions. |

**Framing:** compatible emergent signature within the gauged Hopf lattice TOE — not a derived identity.
"""

CLAIMS_MD = """
| Mystery element | Demo shows… |
|-----------------|-------------|
| **φ²+e²≈π²** | Residual R and relative error printed after each run. |
| **30-60-90 proximity** | Bar chart comparing φ-e-π angles vs exact 30°/60°/90°. |
| **3-6-9 tens** | Angle÷10° values (~3.10 / 5.99 / 8.91) in metrics block. |
| **Holonomy gap** | B(κ) = π²(e/π−κ) vs R; κ* nulls the bound exactly. |
| **κ_doc = 0.85** | Documented locked invariant — 0.16% from κ*, 9.5% bound gap at κ_doc. |
| **TOE linkage** | θ_crit ≈ π(1+κ), Θ_link ≈ π — see [toe repo](https://github.com/kinaar8340/toe). |

Full results: [docs/RESULTS.md](https://github.com/kinaar8340/mystery/blob/main/docs/RESULTS.md)
"""

FIGURES_INTRO_MD = (
    "Reference figures from the Mystery probe suite — regenerate locally with "
    "`python run_all.py` or individual scripts under `scripts/`."
)

FIGURE_URLS = (
    f"{GITHUB_URL}/raw/main/docs/figures/phi_e_pi_triangle.png",
    f"{GITHUB_URL}/raw/main/docs/figures/residual_kappa_sweep.png",
    f"{GITHUB_URL}/raw/main/docs/figures/vortex_369_clock.png",
    f"{GITHUB_URL}/raw/main/docs/figures/conduit_angular_histogram.png",
)


def is_hf_space() -> bool:
    """True when running inside a Hugging Face Space container."""
    return bool(os.environ.get("SPACE_ID"))


def get_build_label() -> str:
    """Return a short last-updated line for the terminal build screen."""
    try:
        from build_info import BUILD_COMMIT, BUILD_UPDATED_UTC  # noqa: WPS433

        return f"Last updated: {BUILD_UPDATED_UTC} UTC · commit `{BUILD_COMMIT}`"
    except ImportError:
        pass

    import subprocess

    try:
        root = Path(__file__).resolve().parent.parent.parent
        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
        )
        if commit:
            return f"Build: commit `{commit}` (local git)"
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    return "Build: development (no build_info.py)"


def law_of_cosines_angle(opposite: float, side1: float, side2: float) -> float:
    cos_theta = (side1**2 + side2**2 - opposite**2) / (2 * side1 * side2)
    return float(np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0))))


def phi_e_pi_triangle() -> dict:
    phi, e, pi = PHI, E, PI
    angles = {
        "opposite_phi": law_of_cosines_angle(phi, e, pi),
        "opposite_e": law_of_cosines_angle(e, phi, pi),
        "opposite_pi": law_of_cosines_angle(pi, phi, e),
    }
    pythag_check = phi**2 + e**2 - pi**2
    return {
        "constants": {"phi": phi, "e": e, "pi": pi},
        "pythagorean_residual": float(pythag_check),
        "pythagorean_relative_error_pct": float(100 * abs(pythag_check) / pi**2),
        "angles_deg": angles,
        "angles_369_tens": {
            "phi_angle_tens": angles["opposite_phi"] / 10,
            "e_angle_tens": angles["opposite_e"] / 10,
            "pi_angle_tens": angles["opposite_pi"] / 10,
        },
    }


def bound(kappa: float) -> float:
    return float(PI**2 * (E_OVER_PI - kappa))


def kappa_star() -> float:
    return float(E_OVER_PI - R / PI**2)


def format_metrics(kappa: float) -> str:
    tri = phi_e_pi_triangle()
    k_star = kappa_star()
    b = bound(kappa)
    tens = tri["angles_369_tens"]
    return "\n".join(
        [
            "=== Mystery φ-e-π Analysis ===",
            "",
            f"R = φ²+e²−π²     : {tri['pythagorean_residual']:+.8f}",
            f"Relative error  : {tri['pythagorean_relative_error_pct']:.4f}%",
            "",
            "Angles (degrees):",
            f"  opposite φ    : {tri['angles_deg']['opposite_phi']:.4f}°",
            f"  opposite e    : {tri['angles_deg']['opposite_e']:.4f}°",
            f"  opposite π    : {tri['angles_deg']['opposite_pi']:.4f}°",
            "",
            "3-6-9 tens (angle÷10):",
            f"  φ tens        : {tens['phi_angle_tens']:.4f}",
            f"  e tens        : {tens['e_angle_tens']:.4f}",
            f"  π tens        : {tens['pi_angle_tens']:.4f}",
            "",
            f"κ (slider)      : {kappa:.4f}",
            f"κ_doc           : {KAPPA_DOC}",
            f"κ* = e/π−R/π²  : {k_star:.6f}",
            f"κ* vs κ_doc     : {100 * abs(k_star - KAPPA_DOC) / KAPPA_DOC:.3f}%",
            "",
            f"B(κ)            : {b:.6f}",
            f"B(κ) − R        : {b - tri['pythagorean_residual']:+.6f}",
            f"|gap|/|R|       : {100 * abs(b - tri['pythagorean_residual']) / abs(tri['pythagorean_residual']):.2f}%",
            "",
            "Framing: emergent signature — not a derived identity.",
        ]
    )


def plot_triangle_comparison(result: dict, out_dir: Path) -> str:
    labels = ["φ", "e", "π"]
    mystery_angles = [
        result["angles_deg"]["opposite_phi"],
        result["angles_deg"]["opposite_e"],
        result["angles_deg"]["opposite_pi"],
    ]
    exact_angles = [30.0, 60.0, 90.0]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    x = np.arange(3)
    w = 0.35
    axes[0].bar(x - w / 2, mystery_angles, w, label="φ-e-π triangle", color="#c9a227")
    axes[0].bar(x + w / 2, exact_angles, w, label="30-60-90 exact", color="#6a4c93", alpha=0.8)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)
    axes[0].set_ylabel("Angle (degrees)")
    axes[0].set_title("Angle comparison")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.3)

    ratios_m = [1.0, E / PHI, PI / PHI]
    ratios_e = [1.0, float(np.sqrt(3)), 2.0]
    axes[1].bar(x - w / 2, ratios_m, w, label="φ-e-π (norm to φ)", color="#c9a227")
    axes[1].bar(x + w / 2, ratios_e, w, label="30-60-90 exact", color="#6a4c93", alpha=0.8)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels)
    axes[1].set_ylabel("Side ratio")
    axes[1].set_title("Normalized side ratios")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.3)

    fig.suptitle(
        f"φ² + e² − π² = {result['pythagorean_residual']:+.6f} "
        f"({result['pythagorean_relative_error_pct']:.2f}% rel. error)",
        fontsize=11,
    )
    fig.tight_layout()

    path = out_dir / "phi_e_pi_triangle.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_kappa_sweep(kappa: float, out_dir: Path) -> str:
    k_star = kappa_star()
    kappas = np.linspace(0.70, 0.95, 100)
    b_vals = np.array([bound(k) for k in kappas])
    gap = b_vals - R

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    ax = axes[0]
    ax.plot(kappas, b_vals, label="B(κ) = π²(e/π − κ)", color="#6a4c93", lw=2)
    ax.axhline(R, color="#c9a227", ls="--", label=f"R = {R:.5f}")
    ax.axvline(KAPPA_DOC, color="#e63946", ls=":", label=f"κ_doc = {KAPPA_DOC}")
    ax.axvline(k_star, color="#457b9d", ls="-.", label=f"κ* = {k_star:.5f}")
    ax.axvline(kappa, color="#2a9d8f", ls="-", lw=1.2, alpha=0.85, label=f"κ = {kappa:.3f}")
    ax.set_xlabel("κ")
    ax.set_ylabel("Value")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_title("B(κ) vs residual R")

    ax2 = axes[1]
    ax2.plot(kappas, gap, color="#6a4c93", lw=2)
    ax2.axhline(0, color="#333", ls="-", lw=0.8)
    ax2.axvline(KAPPA_DOC, color="#e63946", ls=":", label=f"κ_doc")
    ax2.axvline(k_star, color="#457b9d", ls="-.", label="κ* (exact null)")
    ax2.scatter([kappa], [bound(kappa) - R], color="#2a9d8f", zorder=5, s=40)
    ax2.set_xlabel("κ")
    ax2.set_ylabel("B(κ) − R")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    ax2.set_title("Holonomy-gap scaling error")

    fig.suptitle("κ* = e/π − R/π² sits 0.16% from documented κ = 0.85", fontsize=11)
    fig.tight_layout()

    path = out_dir / "residual_kappa_sweep.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def run_analysis(kappa: float) -> tuple[str, str | None, str | None]:
    """Return (metrics text, triangle figure path, kappa sweep path)."""
    tri = phi_e_pi_triangle()
    out_dir = Path(tempfile.mkdtemp(prefix="mystery_gradio_"))
    tri_path = plot_triangle_comparison(tri, out_dir)
    sweep_path = plot_kappa_sweep(float(kappa), out_dir)
    return format_metrics(float(kappa)), tri_path, sweep_path


PROBE_SCRIPTS: tuple[tuple[str, str], ...] = (
    ("phi_e_pi_analysis.py", "φ²+e²≈π² triangle & 30-60-90"),
    ("hopf_constant_bridge.py", "κ, W_g, θ_crit vs e/π"),
    ("vortex_369_clock.py", "3-6-9 clock & Rodin mod-9"),
    ("residual_bound_probe.py", "Bound R via W_g, κ"),
    ("residual_kappa_sweep.py", "B(κ) sweep; κ* null"),
    ("pde_relaxation_probe.py", "Meta-seeded PDE + FFT"),
    ("pde_structured_ic_probe.py", "Hopfion / two-gyro IC"),
    ("rodin_hopf_fiber_map.py", "Rodin doubling → Hopf S¹"),
    ("conduit_probe.py", "TOE conduit smoke (local toe venv)"),
    ("conduit_angular_probe.py", "30°/60°/90° angular histogram"),
    ("meta_optimize_phi_probe.py", "Meta-optimizer κ lock"),
)

TERM_KEY_ACTIONS: dict[int, tuple[str, str]] = {
    1: ("home", "Return to selection menu"),
    2: ("status", "Live constants & environment"),
    3: ("scope", "What this Space runs vs local suite"),
    4: ("directory", "Repo layout & paths"),
    5: ("results", "φ-e-π results snapshot"),
    6: ("build", "Build stamp & deploy info"),
    7: ("help", "D-pad / keypad navigation"),
    8: ("scan", "Phosphor signal scan — CSS only, any key exits"),
    9: ("probes", "11-script probe catalog"),
    10: ("vortex369", "3-6-9 tens & vortex clock"),
    11: ("toe", "TOE parent linkage"),
    12: ("figures", "Reference figure index"),
}


def terminal_results_snapshot() -> str:
    tri = phi_e_pi_triangle()
    k_star = kappa_star()
    tens = tri["angles_369_tens"]
    b_doc = bound(KAPPA_DOC)
    return "\n".join(
        [
            "Confirmed emergent signature (June 2026 probes):",
            "",
            f"R = φ²+e²−π²   {tri['pythagorean_residual']:+.6f}",
            f"Rel. error     {tri['pythagorean_relative_error_pct']:.2f}%",
            "",
            f"Angles         {tri['angles_deg']['opposite_phi']:.1f}° / "
            f"{tri['angles_deg']['opposite_e']:.1f}° / "
            f"{tri['angles_deg']['opposite_pi']:.1f}°",
            f"369 tens       {tens['phi_angle_tens']:.2f} / "
            f"{tens['e_angle_tens']:.2f} / "
            f"{tens['pi_angle_tens']:.2f}",
            "",
            f"κ_doc          {KAPPA_DOC}",
            f"κ*             {k_star:.5f}  ({100 * abs(k_star - KAPPA_DOC) / KAPPA_DOC:.2f}% from κ_doc)",
            f"B(κ_doc)−R     {b_doc - tri['pythagorean_residual']:+.5f}  "
            f"({100 * abs(b_doc - tri['pythagorean_residual']) / abs(tri['pythagorean_residual']):.1f}% gap)",
            "",
            "Not a derived identity — compatible with gauged Hopf lattice TOE.",
        ]
    )


def terminal_directory_help() -> str:
    return "\n".join(
        [
            "mystery/  (github.com/kinaar8340/mystery)",
            "├── scripts/          11 probe scripts",
            "├── notes/            emergent_signatures, synthesis, …",
            "├── docs/             RESULTS.md, figures/",
            "├── outputs/          JSON + PNG (gitignored)",
            "├── run_all.py        full local suite runner",
            "├── space/mystery/    HF Gradio bundle (this UI)",
            "│   ├── app.py        terminal + keypad + analysis",
            "│   └── demo_core.py  φ-e-π math & plots",
            "",
            "Local:  python run_all.py",
            "HF:     Run analysis (κ slider) · Figures tab",
            f"TOE:    {TOE_URL}",
        ]
    )


def terminal_probe_scope() -> str:
    return "\n".join(
        [
            "THIS SPACE (browser):",
            "  · φ-e-π triangle angles & side ratios",
            "  · B(κ) = π²(e/π−κ) holonomy-gap scaling",
            "  · κ slider + triangle + κ-sweep plots",
            "  · Matrix terminal + keypad (you are here)",
            "",
            "LOCAL ONLY (run_all.py — 11 probes):",
            "  · PDE relaxation & structured IC",
            "  · Conduit angular + TOE conduit smoke",
            "  · Meta-optimizer κ lock, Rodin-Hopf map",
            "  · Full JSON reports → outputs/",
            "",
            "Press 09 for script catalog · Run analysis below.",
        ]
    )


def terminal_probe_catalog() -> str:
    lines = ["11 probes in scripts/ (run_all.py order):", ""]
    for idx, (name, blurb) in enumerate(PROBE_SCRIPTS, start=1):
        lines.append(f"  {idx:02d}. {name}")
        lines.append(f"      {blurb}")
    lines.extend(["", "TOE-linked: conduit_*, meta_optimize_* need toe venv."])
    return "\n".join(lines)


def terminal_vortex369_readout() -> str:
    tri = phi_e_pi_triangle()
    tens = tri["angles_369_tens"]
    return "\n".join(
        [
            "Vortex 3-6-9 positional geometry (angle ÷ 10°):",
            "",
            f"  φ leg → {tens['phi_angle_tens']:.3f}  (nearest 3)",
            f"  e leg → {tens['e_angle_tens']:.3f}  (nearest 6)",
            f"  π leg → {tens['pi_angle_tens']:.3f}  (nearest 9)",
            "",
            "Rodin doubling cycle 1-2-4-8-7-5 maps to Hopf S¹ phases",
            "(see rodin_hopf_fiber_map.py + vortex_369_clock.py).",
            "",
            "Echo is numerical — not a forced 3-6-9 lock.",
        ]
    )


def terminal_toe_linkage() -> str:
    w_g = 350.0 / PI
    theta_crit = PI * (1.0 + KAPPA_DOC)
    return "\n".join(
        [
            "Gauged Hopf lattice TOE (parent repo):",
            "",
            f"  κ_doc         {KAPPA_DOC}",
            f"  e/π           {E_OVER_PI:.5f}",
            f"  W_g ≈ 350/π   {w_g:.3f}",
            f"  θ_crit ≈ π(1+κ)  {theta_crit:.3f}",
            f"  Θ_link ≈ π    (not 5.8 — see toe papers)",
            "",
            f"Repo: {TOE_URL}",
            "Burst threshold reconciliation:",
            "  notes/theta_crit_reconciliation.md",
        ]
    )


def terminal_figures_index() -> str:
    labels = (
        "phi_e_pi_triangle.png",
        "residual_kappa_sweep.png",
        "vortex_369_clock.png",
        "conduit_angular_histogram.png",
    )
    lines = ["docs/figures/ (Figures tab + GitHub raw):", ""]
    for idx, (url, name) in enumerate(zip(FIGURE_URLS, labels, strict=True), start=1):
        lines.append(f"  {idx}. {name}")
        lines.append(f"     {url}")
    lines.append("")
    lines.append("Regenerate: python run_all.py → outputs/")
    return "\n".join(lines)


def terminal_keypad_map() -> str:
    lines = ["Assigned prog keys (01–12):", ""]
    for index in sorted(TERM_KEY_ACTIONS):
        _action, desc = TERM_KEY_ACTIONS[index]
        tag = "01 Home" if index == 1 else f"{index:02d}"
        lines.append(f"  [{tag}]  {desc}")
    lines.extend(
        [
            "",
            "D-pad: ▲▼◀▶ move menu · enter confirm · clear blank",
            "Keys 13–24: reserved (latch only)",
            "Menu items 01–08 mirror d-pad selection.",
        ]
    )
    return "\n".join(lines)


