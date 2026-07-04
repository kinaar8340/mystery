"""Shared φ-e-π analysis helpers for Mystery Gradio and HF Spaces."""

from __future__ import annotations

import base64
import io
import os
import tempfile
import traceback
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
UNIT_CELL_VIEWPORT_PX = 550
UNIT_CELL_FIGSIZE = (6.0, 6.0)
UNIT_CELL_VIEW_ELEV = 26.0
UNIT_CELL_VIEW_AZIM = 45.0
UNIT_CELL_VIEW_DIST = 14.0
UNIT_CELL_AXIS_HALF = 2.35

BOOT_QUOTE_STRING = "TEST EVERYTHING, HOLD FAST WHAT IS GOOD AND KNOW YOUR GOD"

HF_SPACE_URL = "https://huggingface.co/spaces/kinaar111/mystery"
GITHUB_URL = "https://github.com/kinaar8340/mystery"
TOE_URL = "https://github.com/kinaar8340/toe"
_SPACE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SPACE_DIR.parent.parent


def resolve_wallpaper_url() -> str:
    """Prefer bundled/local mystery_image.png; fall back to GitHub raw after push."""
    for path in (_SPACE_DIR / "mystery_image.png", _REPO_ROOT / "mystery_image.png"):
        if path.is_file():
            stamp = int(path.stat().st_mtime)
            # Gradio serves set_static_paths() assets via /gradio_api/file= (not /file=<abs path>).
            return f"/gradio_api/file={path.name}?v={stamp}"
    return f"{GITHUB_URL}/raw/main/mystery_image.png"


def wallpaper_static_paths() -> list[Path]:
    """Directories Gradio may serve for the wallpaper background image."""
    paths: list[Path] = []
    for path in (_SPACE_DIR / "mystery_image.png", _REPO_ROOT / "mystery_image.png"):
        if path.is_file():
            paths.append(path.parent)
    return list(dict.fromkeys(paths))


WALLPAPER_URL = resolve_wallpaper_url()

SIMULATION_BANNER_MD = """
> **Demo-oriented Space** — browser κ slider, φ-e-π triangle plots, and CLI terminal.
> Not live PDE/conduit simulation. Full 11-probe suite, step-by-step notes, and JSON outputs:
> [github.com/kinaar8340/mystery](https://github.com/kinaar8340/mystery) (`run_all.py` locally).
"""

ONBOARDING_MD = """
### φ, e, π — emergent signature, not forced identity
The near-Pythagorean residual **R = φ²+e²−π² ≈ +0.137** (~1.4% relative error) defines a
triangle whose angles land near **31° / 60° / 90°** — and whose tens digits echo **3-6-9**
vortex geometry. This Space runs the **core numerical checks** interactively.

**Early-stage project** — full derivations and probe depth live on
[GitHub](https://github.com/kinaar8340/mystery) ([angle steps](https://github.com/kinaar8340/mystery/blob/main/notes/angle_derivation.md)).

### Three steps (60 seconds)
1. **Adjust κ** on the slider (documented κ = 0.85 is marked).
2. **Run analysis** — read metrics for R, B(κ), κ*, and angle/369 tens.
3. **Open Gravity** — 3D unit cell, residual explorer, and probe hooks; or **Figures** for reference plots.

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

W_G_TARGET = 350.0 / PI

GITHUB_SCRIPTS = {
    "pde": f"{GITHUB_URL}/blob/main/scripts/pde_relaxation_probe.py",
    "conduit": f"{GITHUB_URL}/blob/main/scripts/conduit_probe.py",
    "meta": f"{GITHUB_URL}/blob/main/scripts/meta_optimize_phi_probe.py",
}

PHYSICAL_INTERPRETATION_INTRO_MD = """
## Physical Interpretation & Emergent Gravity

In the gauged Hopf lattice, gravity is not fundamental but arises as a **secondary geometric effect**
from local flux imbalance under orthogonal stress.

### Unit-cell intuition

Consider a flexible unit cell whose internal opposing flux rotors maintain equilibrium. Orthogonal
pressure on one face disturbs rotor balance; because the lattice is flux-conserving and topologically
constrained (Hopf fibration), compensatory **side contraction** appears — the geometric signature of
emergent gravity at larger scales.

**Legend:** \\(T_\\phi, T_e, T_\\pi\\) = quadratic flux/tension · \\(\\delta_z\\) = primary π-face push ·
\\(\\delta_\\text{side}\\) = compensatory contraction · \\(R = \\phi^2+e^2-\\pi^2\\) imbalance.

On the **Gravity** tab, the deformable unit cell is server-rendered (no browser WebGL required). Drag **deformation pressure** to bow the π-face concave and pinch the φ/e sides inward; rotate with **view elevation/azimuth**; press **Animate deformation** for a smooth 0→100% curvature sweep with color-coded face modes.
"""

PHYSICAL_INTERPRETATION_MATH_MD = f"""
### Mathematical formulation

Orthogonal scales: \\(l_\\phi \\propto \\sqrt{{\\phi}}\\), \\(l_e \\propto \\sqrt{{e}}\\),
\\(l_\\pi \\propto \\sqrt{{\\pi}}\\). Quadratic tensions: \\(T_\\phi \\propto \\phi^2\\),
\\(T_e \\propto e^2\\), \\(T_\\pi \\propto \\pi^2\\).

\\[
R = \\phi^2 + e^2 - \\pi^2 \\approx +0.137486
\\]

When orthogonal pressure along the \\(\\pi\\) direction produces primary deformation \\(\\delta_z\\),
the lattice responds with compensatory side contraction:

\\[
\\delta_\\text{{side}} \\approx \\alpha \\cdot \\delta_z + \\beta \\cdot R \\cdot f(\\kappa)
\\]

*The second term represents the net inward contraction driven by the residual \\(R\\).*
Take \\(f(\\kappa) \\propto B(\\kappa) = \\pi^2(e/\\pi - \\kappa)\\).

#### Holonomy-gap tie-in

\\[
B(\\kappa) = \\pi^2 \\left( \\frac{{e}}{{\\pi}} - \\kappa \\right)
\\]

At \\(\\kappa^* = e/\\pi - R/\\pi^2 \\approx 0.8513\\), \\(B(\\kappa^*) = R\\) exactly.
See [residual_scaling.md]({GITHUB_URL}/blob/main/notes/residual_scaling.md).

### 4D extension

A phase/holonomy scale \\(350/\\pi \\approx {W_G_TARGET:.2f}\\) lies close to the locked
\\(W_g \\approx 111.89\\) from meta-optimization — suggesting \\(R\\) couples spatial side-suction
to rotor-phase winding along the Hopf fiber in 4D.

**Canonical write-up:**
[README § Physical Interpretation]({GITHUB_URL}#physical-interpretation--emergent-gravity)
"""

PROBE_HOOKS_TABLE_MD = f"""
| Probe | Hook | Script |
|-------|------|--------|
| **PDE relaxation** | Seed Hopfion ICs with orthogonal deformation bias under \\(\\delta_z\\) | [pde_relaxation_probe.py]({GITHUB_SCRIPTS['pde']}) |
| **Conduit** | Inject \\(R \\cdot B(\\kappa)\\) as holonomy source; monitor \\(W_g\\) drift | [conduit_probe.py]({GITHUB_SCRIPTS['conduit']}) |
| **Meta-optimizer** | Add deformation energy \\(\\propto R\\); check \\(\\kappa \\to \\kappa^*\\) | [meta_optimize_phi_probe.py]({GITHUB_SCRIPTS['meta']}) |
"""

EXPLORE_FURTHER_MD = f"""
### How to explore further

1. **Clone the repo** — [`git clone {GITHUB_URL}.git`]({GITHUB_URL}) and run `python run_all.py` for the full 11-probe suite.
2. **Read the canonical section** — [Physical Interpretation & Emergent Gravity]({GITHUB_URL}#physical-interpretation--emergent-gravity) in the README.
3. **Try the probe hooks** — expand the accordions above; snippets drop into existing `scripts/` files.
4. **Parent TOE stack** — [kinaar8340/toe]({TOE_URL}) for conduit PDE and meta-optimizer depth.
5. **Tune interactively** — use the **Residual explorer** sliders on this tab to stress-test \\(R\\), \\(B(\\kappa)\\), and \\(\\delta_\\text{{side}}\\).
"""

PROBE_SNIPPETS: tuple[tuple[str, str, str], ...] = (
    (
        "PDE relaxation — holonomy source at IC + in time loop",
        GITHUB_SCRIPTS["pde"],
        """from _common import PHI, E, PI

R = PHI**2 + E**2 - PI**2
kappa = 0.8513
B_kappa = PI**2 * (E / PI - kappa)
beta = 0.1

z = np.linspace(0, 1, nx, endpoint=False)
theta += beta * R * B_kappa * np.sin(2 * np.pi * z)[:, None, None]

holonomy_source = -beta * R * B_kappa * np.sin(theta)
rhs = D * lap + cot_term + delta_omega + gauge + burst + holonomy_source
theta += dt * rhs""",
    ),
    (
        "Conduit — seed at κ* and log residual–winding coupling",
        GITHUB_SCRIPTS["conduit"],
        """from _common import PHI, E, PI

R = PHI**2 + E**2 - PI**2
kappa_star = E / PI - R / PI**2
B_kappa = PI**2 * (E / PI - kappa_star)

stats = conduit.monitor_topological_winding(n_samples=128)
report = {
    "R": R,
    "B_kappa": B_kappa,
    "kappa_star": kappa_star,
    "residual_coupling": R * B_kappa,
    "geometric_winding": stats.get("geometric_winding"),
    "w_g_target": 350.0 / PI,
}""",
    ),
    (
        "Meta-optimizer — deformation penalty on holonomy gap",
        GITHUB_SCRIPTS["meta"],
        """R = PHI**2 + E**2 - PI**2
kappa = trial.suggest_float("kappa", 0.80, 0.90)
B_kappa = PI**2 * (E / PI - kappa)
deformation_cost = (B_kappa - R) ** 2
objective = base_loss + w_def * deformation_cost  # w_def ≈ 0.01""",
    ),
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


def residual_from_scales(
    phi_sq_scale: float = 1.0,
    e_sq_scale: float = 1.0,
    pi_sq_scale: float = 1.0,
) -> float:
    """Pythagorean residual with per-term scale factors (explore sensitivity)."""
    return float(
        phi_sq_scale * PHI**2 + e_sq_scale * E**2 - pi_sq_scale * PI**2
    )


def kappa_star_from_r(r: float) -> float:
    return float(E_OVER_PI - r / PI**2)


def delta_side_contraction(
    delta_z: float,
    r: float,
    kappa: float,
    *,
    alpha: float = 1.0,
    beta: float = 1.0,
) -> float:
    """δ_side ≈ α·δ_z + β·R·B(κ) with f(κ) ∝ B(κ)."""
    return float(alpha * delta_z + beta * r * bound(kappa))


def format_residual_explorer(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
) -> str:
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    k_star = kappa_star_from_r(r_val)
    b_k = bound(kappa)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    rel_err = 100 * abs(r_val) / PI**2
    gap = b_k - r_val
    return "\n".join(
        [
            "=== Residual Explorer ===",
            "",
            f"φ² scale       : {phi_sq_scale:.4f}   →  {phi_sq_scale * PHI**2:.6f}",
            f"e² scale       : {e_sq_scale:.4f}   →  {e_sq_scale * E**2:.6f}",
            f"π² scale       : {pi_sq_scale:.4f}   →  {pi_sq_scale * PI**2:.6f}",
            "",
            f"R              : {r_val:+.8f}",
            f"Rel. error     : {rel_err:.4f}%",
            "",
            f"κ              : {kappa:.4f}",
            f"κ* (nulls gap) : {k_star:.6f}",
            f"B(κ)           : {b_k:.6f}",
            f"B(κ) − R       : {gap:+.6f}",
            "",
            f"δ_z (push)     : {delta_z:.4f}",
            f"α, β           : {alpha:.3f}, {beta:.3f}",
            f"δ_side         : {d_side:.6f}",
            f"  α·δ_z term   : {alpha * delta_z:.6f}",
            f"  β·R·B(κ)     : {beta * r_val * b_k:.6f}",
            "",
            f"W_g target     : {W_G_TARGET:.4f}  (350/π)",
            f"350/π vs W_g   : meta-opt W_g ≈ 111.89",
        ]
    )


_UNIT_CELL_MATRIX_GREEN = "#33ff66"
_UNIT_CELL_GOLD = "#c9a227"
_UNIT_CELL_RED = "#e63946"
_UNIT_CELL_GREEN = "#22c55e"
_UNIT_CELL_BLUE = "#2563eb"
_UNIT_CELL_BOTTOM_CONVEX = "#5a9ef2"
_UNIT_CELL_LABEL_TEXT = "#ffffff"


def _clamp_deform_pressure(pressure: float) -> float:
    """Signed deformation driver: −1 = max concave, 0 = rigid, +1 = max convex."""
    return float(np.clip(pressure, -1.0, 1.0))


def _deform_pressure_hint(pressure: float) -> str:
    p = _clamp_deform_pressure(pressure)
    if abs(p) < 0.04:
        return "rigid cube"
    if p > 0.0:
        if p < 0.45:
            return "mild convex · outward side bow"
        if p < 0.8:
            return "moderate convex · inflated faces"
        return "max convex · very high internal pressure"
    ap = abs(p)
    if ap < 0.45:
        return "mild concave · side pinch"
    if ap < 0.8:
        return "moderate concave · π bowl inward"
    return "max concave · very low internal pressure"


def deformation_key_metrics(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    pressure: float,
    *,
    frame_idx: int | None = None,
    total_frames: int | None = None,
) -> dict[str, float | int | str | None]:
    """Per-frame gravity/residual metrics for animation TUI readout."""
    p = _clamp_deform_pressure(pressure)
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    b_k = bound(kappa)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    return {
        "pressure": p,
        "pressure_pct": p * 100.0,
        "r": float(r_val),
        "kappa": float(kappa),
        "b_k": float(b_k),
        "b_minus_r": float(b_k - r_val),
        "delta_z": float(delta_z),
        "delta_side": float(d_side),
        "alpha": float(alpha),
        "beta": float(beta),
        "w_g": float(W_G_TARGET),
        "deform_hint": _deform_pressure_hint(p),
        "frame_idx": frame_idx,
        "total_frames": total_frames,
    }


def build_unit_cell_viewport_header_html(
    *,
    pressure: float,
    r_val: float | None = None,
    frame_idx: int | None = None,
    total_frames: int | None = None,
) -> str:
    """Compact fixed viewport nameplate (no legend/equation scroll stack)."""
    del r_val
    p = _clamp_deform_pressure(pressure)
    hint = _deform_pressure_hint(p)
    frame_note = ""
    if frame_idx is not None and total_frames:
        frame_note = f" · frame {int(frame_idx)}/{int(total_frames)}"
    return f"""<div class="myst-cube-viewport-header myst-cube-viewport-header-fixed" role="img" aria-label="Unit cell viewport">
  <div class="myst-cube-viewport-title-line">UNIT CELL VIEWPORT</div>
  <div class="myst-cube-viewport-sub-line">Deformable Unit Cell · No WebGL · pressure {p * 100:.0f}% · {hint}{frame_note}</div>
</div>"""


def _lerp3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    return (
        a[0] + t * (b[0] - a[0]),
        a[1] + t * (b[1] - a[1]),
        a[2] + t * (b[2] - a[2]),
    )


def _bilinear_face(
    p00: tuple[float, float, float],
    p10: tuple[float, float, float],
    p11: tuple[float, float, float],
    p01: tuple[float, float, float],
    u: float,
    v: float,
) -> tuple[float, float, float]:
    p0 = _lerp3(p00, p10, u)
    p1 = _lerp3(p01, p11, u)
    return _lerp3(p0, p1, v)


def _deformation_weights(
    x: float,
    y: float,
    z: float,
    s: float,
) -> dict[str, float]:
    """Per-vertex weights for π-bowl, φ/e concavity, and bottom convex bulge."""
    xn, yn, zn = x / s, y / s, z / s
    bowl = max(0.0, 1.0 - xn**2) * max(0.0, 1.0 - yn**2)
    equator = max(0.12, 1.0 - 0.5 * zn**2)
    top_w = max(0.0, zn) ** 1.45
    bottom_w = max(0.0, -zn) ** 1.45
    x_edge = min(1.0, abs(xn) ** 1.25)
    y_edge = min(1.0, abs(yn) ** 1.25)
    return {
        "bowl": bowl,
        "equator": equator,
        "top_w": top_w,
        "bottom_w": bottom_w,
        "x_edge": x_edge,
        "y_edge": y_edge,
        "zn": zn,
        "xn": xn,
        "yn": yn,
    }


def _displacement_components(
    x: float,
    y: float,
    z: float,
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
) -> tuple[float, float, float, dict[str, float]]:
    """Return (dx, dy, dz) offsets and mode weights for coloring.

    Signed pressure: positive = convex (outward bulge), negative = concave
    (inward bowl + side pinch), zero = rigid cube.
    """
    p = _clamp_deform_pressure(pressure)
    if abs(p) < 1e-9:
        return 0.0, 0.0, 0.0, {
            "pi_bowl": 0.0,
            "phi_concave": 0.0,
            "e_concave": 0.0,
            "bottom_convex": 0.0,
        }

    mag = abs(p)
    w = _deformation_weights(x, y, z, s)
    bowl = w["bowl"]
    equator = w["equator"]

    # Concave template at |p|: π-face bowl inward, φ/e sides pinch inward
    pi_mag = mag * delta_z * 5.0 * w["top_w"] * bowl
    dz_pi = -pi_mag

    phi_mag = 0.0
    e_mag = 0.0
    dx_side = 0.0
    dy_side = 0.0
    if abs(x) > 1e-9:
        phi_mag = mag * delta_side * 3.6 * w["x_edge"] * equator * (1.0 - 0.25 * bowl)
        dx_side = -np.sign(x) * phi_mag
    if abs(y) > 1e-9:
        e_mag = mag * delta_side * 3.6 * w["y_edge"] * equator * (1.0 - 0.25 * bowl)
        dy_side = -np.sign(y) * e_mag

    bottom_mag = mag * delta_z * 0.85 * w["bottom_w"] * bowl
    dz_bottom = bottom_mag

    dx = dx_side
    dy = dy_side
    dz = dz_pi + dz_bottom
    if p > 0.0:
        dx, dy, dz = -dx, -dy, -dz

    modes = {
        "pi_bowl": pi_mag,
        "phi_concave": phi_mag,
        "e_concave": e_mag,
        "bottom_convex": bottom_mag,
    }
    return dx, dy, dz, modes


def _displace_vertex(
    x: float,
    y: float,
    z: float,
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
) -> tuple[float, float, float]:
    """π-face bowl (push), φ/e side concavity, slight bottom convex — scaled by pressure."""
    dx, dy, dz, _modes = _displacement_components(
        x, y, z, s, pressure, delta_z, delta_side
    )
    return float(x + dx), float(y + dy), float(z + dz)


def _cube_face_quads(s: float) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    return (
        ((-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)),  # π top
        ((-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s)),  # bottom
        ((-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)),  # front −y
        ((-s, s, -s), (s, s, -s), (s, s, s), (-s, s, s)),  # back +y
        ((-s, -s, -s), (-s, s, -s), (-s, s, s), (-s, -s, s)),  # left −x φ
        ((s, -s, -s), (s, s, -s), (s, s, s), (s, -s, s)),  # right +x e
    )


_MESH_TOPOLOGY_CACHE: dict[int, list[tuple[tuple[float, float, float], ...]]] = {}


def _cube_mesh_topology(
    s: float,
    *,
    subdiv: int = 8,
) -> list[tuple[tuple[float, float, float], ...]]:
    """Fixed quad corners per surface patch (cached by subdiv)."""
    if subdiv not in _MESH_TOPOLOGY_CACHE:
        patches: list[tuple[tuple[float, float, float], ...]] = []
        for p00, p10, p11, p01 in _cube_face_quads(s):
            for i in range(subdiv):
                u0, u1 = i / subdiv, (i + 1) / subdiv
                for j in range(subdiv):
                    v0, v1 = j / subdiv, (j + 1) / subdiv
                    patches.append(
                        (
                            _bilinear_face(p00, p10, p11, p01, u0, v0),
                            _bilinear_face(p00, p10, p11, p01, u1, v0),
                            _bilinear_face(p00, p10, p11, p01, u1, v1),
                            _bilinear_face(p00, p10, p11, p01, u0, v1),
                        )
                    )
        _MESH_TOPOLOGY_CACHE[subdiv] = patches
    return _MESH_TOPOLOGY_CACHE[subdiv]


def _triangle_mode_color(
    modes: tuple[dict[str, float], dict[str, float], dict[str, float]],
    *,
    pressure: float,
) -> tuple[float, float, float, float]:
    """Blend face colors from dominant deformation mode at triangle centroid."""
    eq_red = (0.90, 0.22, 0.27)
    eq_green = (0.13, 0.77, 0.37)
    eq_blue = (0.15, 0.39, 0.92)
    neutral = (0.22, 0.28, 0.42)

    totals = {
        "pi_bowl": sum(m["pi_bowl"] for m in modes),
        "phi_concave": sum(m["phi_concave"] for m in modes),
        "e_concave": sum(m["e_concave"] for m in modes),
        "bottom_convex": sum(m["bottom_convex"] for m in modes),
    }
    dominant = max(totals, key=totals.get)
    mag = totals[dominant] / 3.0
    p_abs = abs(_clamp_deform_pressure(pressure))
    blend = min(1.0, mag / max(0.08, p_abs * 0.35 + 0.05))
    palette = {
        "pi_bowl": eq_blue,
        "phi_concave": eq_red,
        "e_concave": eq_green,
        "bottom_convex": (0.35, 0.62, 0.95),
    }
    base = palette.get(dominant, neutral)
    rgb = tuple(neutral[i] + blend * (base[i] - neutral[i]) for i in range(3))
    alpha = 0.12 + 0.38 * min(1.0, p_abs)
    return (*rgb, alpha)


def _deformed_cube_surface(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    subdiv: int = 8,
) -> tuple[list[list[tuple[float, float, float]]], list[tuple[float, float, float, float]]]:
    """Subdivided surface triangles and per-triangle RGBA colors."""
    triangles: list[list[tuple[float, float, float]]] = []
    colors: list[tuple[float, float, float, float]] = []
    for corners in _cube_mesh_topology(s, subdiv=subdiv):
        displaced = []
        mode_triplet = []
        for corner in corners:
            x, y, z = corner
            dx, dy, dz, modes = _displacement_components(
                x, y, z, s, pressure, delta_z, delta_side
            )
            displaced.append((x + dx, y + dy, z + dz))
            mode_triplet.append(modes)
        a, b, c, d = displaced
        ma, mb, mc = mode_triplet[0], mode_triplet[1], mode_triplet[2]
        md = mode_triplet[3]
        triangles.append([a, b, c])
        colors.append(_triangle_mode_color((ma, mb, mc), pressure=pressure))
        triangles.append([a, c, d])
        colors.append(_triangle_mode_color((ma, mc, md), pressure=pressure))
    return triangles, colors


def _deformed_cube_triangles(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    subdiv: int = 8,
) -> list[list[tuple[float, float, float]]]:
    """Subdivided surface triangles for a pressure-deformed unit cell."""
    triangles, _colors = _deformed_cube_surface(
        s, pressure, delta_z, delta_side, subdiv=subdiv
    )
    return triangles


def _deformed_face_curvature_grid(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    subdiv: int = 8,
    grid_step: int = 2,
) -> list[list[tuple[float, float, float]]]:
    """Iso-u / iso-v lines on each face — bend visibly under pressure."""
    polylines: list[list[tuple[float, float, float]]] = []
    for p00, p10, p11, p01 in _cube_face_quads(s):
        n = subdiv
        for i in range(0, n + 1, grid_step):
            u = i / n
            line = [
                _displace_vertex(
                    *_bilinear_face(p00, p10, p11, p01, u, v / n),
                    s,
                    pressure,
                    delta_z,
                    delta_side,
                )
                for v in range(n + 1)
            ]
            polylines.append(line)
        for j in range(0, n + 1, grid_step):
            v = j / n
            line = [
                _displace_vertex(
                    *_bilinear_face(p00, p10, p11, p01, u / n, v),
                    s,
                    pressure,
                    delta_z,
                    delta_side,
                )
                for u in range(n + 1)
            ]
            polylines.append(line)
    return polylines


def _deformed_cube_edge_polylines(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    samples: int = 18,
) -> list[list[tuple[float, float, float]]]:
    edges = (
        ((-s, -s, -s), (s, -s, -s)),
        ((s, -s, -s), (s, s, -s)),
        ((s, s, -s), (-s, s, -s)),
        ((-s, s, -s), (-s, -s, -s)),
        ((-s, -s, s), (s, -s, s)),
        ((s, -s, s), (s, s, s)),
        ((s, s, s), (-s, s, s)),
        ((-s, s, s), (-s, -s, s)),
        ((-s, -s, -s), (-s, -s, s)),
        ((s, -s, -s), (s, -s, s)),
        ((s, s, -s), (s, s, s)),
        ((-s, s, -s), (-s, s, s)),
    )
    polylines: list[list[tuple[float, float, float]]] = []
    for p0, p1 in edges:
        pts = []
        for t in np.linspace(0.0, 1.0, samples):
            raw = _lerp3(p0, p1, float(t))
            pts.append(_displace_vertex(*raw, s, pressure, delta_z, delta_side))
        polylines.append(pts)
    return polylines


def _anchor_point(
    raw: tuple[float, float, float],
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
) -> tuple[float, float, float]:
    return _displace_vertex(*raw, s, pressure, delta_z, delta_side)


def _draw_leader_label(
    ax,
    anchor: tuple[float, float, float],
    label_pos: tuple[float, float, float],
    text: str,
    line_color: str,
    *,
    text_color: str | None = None,
    fontsize: float = 12,
) -> None:
    """Leader line (phase-colored) from cube anchor to offset label (white text)."""
    label_color = _UNIT_CELL_LABEL_TEXT if text_color is None else text_color
    ax.plot(
        [anchor[0], label_pos[0]],
        [anchor[1], label_pos[1]],
        [anchor[2], label_pos[2]],
        color=line_color,
        linewidth=2.0,
        linestyle="-",
        solid_capstyle="round",
        alpha=1.0,
        zorder=8,
    )
    ax.text(
        label_pos[0],
        label_pos[1],
        label_pos[2],
        text,
        color=label_color,
        fontsize=fontsize,
        ha="center",
        va="center",
        alpha=1.0,
        zorder=9,
    )


def export_figure_for_gradio(fig: plt.Figure, *, dpi: int = 80) -> str:
    """Write figure to a temp PNG and close it — safe for Gradio streaming."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        path = tmp.name
    fig.savefig(
        path,
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        pad_inches=0.05,
    )
    plt.close(fig)
    return path


def figure_to_pil_image(fig: plt.Figure, *, dpi: int = 150):
    """Matplotlib figure → PIL Image."""
    import io

    from PIL import Image as PILImage

    print(f"[DEBUG] figure_to_pil_image: rendering dpi={dpi}", flush=True)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    pil_img = PILImage.open(buf).copy()
    print(f"[DEBUG] figure_to_pil_image: PIL size={pil_img.size}", flush=True)
    return pil_img


def _resize_pil_for_viewport(pil_img, *, max_px: int = UNIT_CELL_VIEWPORT_PX):
    """Downscale for Gradio viewport display (smaller websocket payload)."""
    from PIL import Image as PILImage

    if max(pil_img.size) <= max_px:
        return pil_img
    resized = pil_img.copy()
    resized.thumbnail((max_px, max_px), PILImage.Resampling.LANCZOS)
    return resized


def _flatten_to_opaque_black_rgb(pil_img) -> "object":
    """Composite any alpha onto solid #000 — prevents wallpaper bleed in browser."""
    from PIL import Image as PILImage

    if pil_img.mode == "P":
        pil_img = pil_img.convert("RGBA")
    if pil_img.mode in ("RGBA", "LA"):
        bg = PILImage.new("RGB", pil_img.size, (0, 0, 0))
        alpha = pil_img.getchannel("A")
        bg.paste(pil_img.convert("RGB"), mask=alpha)
        return bg
    return pil_img.convert("RGB")


def _fit_on_black_canvas(pil_img, *, size: int = UNIT_CELL_VIEWPORT_PX) -> "object":
    """Center image on a fixed opaque black square for the Gradio viewport."""
    from PIL import Image as PILImage

    rgb = _flatten_to_opaque_black_rgb(pil_img)
    fitted = _resize_pil_for_viewport(rgb, max_px=size)
    canvas = PILImage.new("RGB", (size, size), (0, 0, 0))
    ox = (size - fitted.size[0]) // 2
    oy = (size - fitted.size[1]) // 2
    canvas.paste(fitted, (ox, oy))
    return canvas


def _viewport_nonblack_count(image) -> int:
    """Count non-black pixels — 0 signals headless matplotlib failed to draw."""
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return 0
    return int(np.any(arr[:, :, :3] != 0, axis=-1).sum())


def _save_figure_viewport_png(fig: plt.Figure, buf: io.BytesIO, *, dpi: int) -> None:
    """Save viewport figure as opaque PNG sized for display."""
    face = fig.get_facecolor()
    if not face or str(face).lower() in {"none", "auto"}:
        face = "#000000"
    fig.savefig(
        buf,
        format="png",
        dpi=dpi,
        facecolor=face,
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.05,
    )
    plt.close(fig)


def _resize_rgb_for_viewport(arr: np.ndarray, *, max_px: int = UNIT_CELL_VIEWPORT_PX) -> np.ndarray:
    from PIL import Image as PILImage

    if arr.ndim != 3 or arr.shape[2] < 3:
        return arr
    pil_img = PILImage.fromarray(arr[:, :, :3])
    return np.asarray(_resize_pil_for_viewport(pil_img, max_px=max_px))


def figure_to_numpy_rgb(fig: plt.Figure, *, dpi: int = 150) -> np.ndarray:
    """Matplotlib figure → RGB numpy array for gr.Image(type='numpy')."""
    pil_img = _resize_pil_for_viewport(figure_to_pil_image(fig, dpi=dpi).convert("RGB"))
    rgb = np.asarray(pil_img)
    print(f"[DEBUG] figure_to_numpy_rgb: shape={rgb.shape}", flush=True)
    return rgb


def export_unit_cell_pil_for_gradio(fig: plt.Figure, *, dpi: int = 150):
    """PIL image for gr.Image — avoids /tmp filepath serving issues on Spaces."""
    return figure_to_pil_image(fig, dpi=dpi)


def export_unit_cell_numpy_for_gradio(fig: plt.Figure, *, dpi: int = 150) -> np.ndarray:
    """RGB numpy array for gr.Image — most reliable on HF Spaces."""
    return figure_to_numpy_rgb(fig, dpi=dpi)


def unit_cell_error_placeholder_numpy(
    *,
    height: int = 550,
    width: int = 550,
) -> np.ndarray:
    """Red RGB placeholder when viewport conversion fails (visible error signal)."""
    placeholder = np.zeros((height, width, 3), dtype=np.uint8)
    placeholder[:, :, 0] = 180
    return placeholder


def figure_to_viewport_numpy(fig: plt.Figure, *, dpi: int = 100) -> np.ndarray:
    """Matplotlib figure → RGB numpy for gr.Image(type='numpy'); never raises."""
    print(f"[DEBUG] figure_to_viewport_numpy: dpi={dpi}", flush=True)
    try:
        buf = io.BytesIO()
        _save_figure_viewport_png(fig, buf, dpi=dpi)
        buf.seek(0)
        from PIL import Image as PILImage

        pil_img = _fit_on_black_canvas(PILImage.open(buf).convert("RGB"))
        arr = np.asarray(pil_img, dtype=np.uint8)
        nonblack = _viewport_nonblack_count(arr)
        print(
            f"[DEBUG] figure_to_viewport_numpy: shape={arr.shape} nonblack={nonblack}",
            flush=True,
        )
        return arr
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_numpy failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_numpy()


_VIEWPORT_WRAP_STYLE = (
    "width:100%;max-width:550px;height:550px;background:#000;"
    "display:flex;align-items:center;justify-content:center;"
    "overflow:hidden;margin:0 auto;box-sizing:border-box;"
)
_VIEWPORT_IMG_STYLE = (
    "max-width:100%;max-height:100%;width:auto;height:auto;"
    "object-fit:contain;display:block;background:#000;"
)


UNIT_CELL_VIEWPORT_EMPTY_HTML = (
    '<div class="myst-unit-cell-viewport-inner" '
    'style="width:100%;max-width:550px;height:550px;background:#000000;"></div>'
)


def _viewport_img_wrap_html(src: str, *, error: bool = False) -> str:
    """Inner viewport markup — gr.HTML block carries elem_id unit-cell-main-view."""
    error_cls = " myst-unit-cell-viewport-error" if error else ""
    return (
        f'<div class="myst-unit-cell-viewport-inner myst-unit-cell-viewport-img-wrap{error_cls}" '
        f'style="{_VIEWPORT_WRAP_STYLE}">'
        f'<img src="{src}" alt="Deformable unit cell viewport" '
        f'class="myst-unit-cell-viewport-img" style="{_VIEWPORT_IMG_STYLE}" '
        'loading="eager" decoding="sync" />'
        "</div>"
    )


def _viewport_file_url_html(file_path: str, *, error: bool = False) -> str:
    """HF Spaces — plain img via Gradio-served /gradio_api/file= URL."""
    return _viewport_img_wrap_html(f"/gradio_api/file={file_path}", error=error)


def numpy_viewport_to_html(arr: np.ndarray) -> str:
    """RGB numpy → inline base64 <img> for gr.HTML (local dev)."""
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.fromarray(np.asarray(arr, dtype=np.uint8)).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return _viewport_img_wrap_html(f"data:image/png;base64,{b64}")


def figure_to_viewport_html(fig: plt.Figure, *, dpi: int = 100) -> str:
    """Matplotlib figure → inline HTML img; never raises."""
    print(f"[DEBUG] figure_to_viewport_html: dpi={dpi}", flush=True)
    try:
        arr = figure_to_viewport_numpy(fig, dpi=dpi)
        html = numpy_viewport_to_html(arr)
        print(
            f"[DEBUG] figure_to_viewport_html: shape={arr.shape} bytes={len(html)}",
            flush=True,
        )
        return html
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_html failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_html()


def _gradio_upload_cache_dir() -> str:
    from gradio.utils import get_upload_folder

    return get_upload_folder()


def numpy_viewport_to_cached_html(arr: np.ndarray) -> str:
    """RGB numpy → gr.HTML img via Gradio upload cache (HF Spaces-safe file URL)."""
    from gradio.processing_utils import save_img_array_to_cache

    cached_path = save_img_array_to_cache(
        np.asarray(arr, dtype=np.uint8),
        _gradio_upload_cache_dir(),
        format="png",
    )
    return _viewport_img_wrap_html(f"/gradio_api/file={cached_path}")


def figure_to_viewport_cached_html(fig: plt.Figure, *, dpi: int = 100) -> str:
    """Matplotlib figure → gr.HTML with Gradio cache file URL; never raises."""
    print(f"[DEBUG] figure_to_viewport_cached_html: dpi={dpi}", flush=True)
    try:
        arr = figure_to_viewport_numpy(fig, dpi=dpi)
        html = numpy_viewport_to_cached_html(arr)
        print(
            f"[DEBUG] figure_to_viewport_cached_html: shape={arr.shape} bytes={len(html)}",
            flush=True,
        )
        return html
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_cached_html failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_cached_html()


def unit_cell_error_placeholder_cached_html() -> str:
    """Red placeholder via Gradio cache file URL when viewport conversion fails."""
    return numpy_viewport_to_cached_html(unit_cell_error_placeholder_numpy())


def unit_cell_error_placeholder_html() -> str:
    """Red placeholder <img> when viewport conversion fails."""
    placeholder = unit_cell_error_placeholder_numpy()
    buf = io.BytesIO()
    from PIL import Image as PILImage

    PILImage.fromarray(placeholder).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return _viewport_img_wrap_html(f"data:image/png;base64,{b64}", error=True)


def unit_cell_error_placeholder_pil():
    """Red PIL placeholder when viewport conversion fails."""
    from PIL import Image as PILImage

    return PILImage.fromarray(unit_cell_error_placeholder_numpy())


def figure_to_viewport_pil(fig: plt.Figure, *, dpi: int = 100):
    """Matplotlib figure → PIL for gr.Image(type='pil'); never raises."""
    print(f"[DEBUG] figure_to_viewport_pil: dpi={dpi}", flush=True)
    try:
        from PIL import Image as PILImage

        buf = io.BytesIO()
        _save_figure_viewport_png(fig, buf, dpi=dpi)
        buf.seek(0)
        pil_img = _fit_on_black_canvas(PILImage.open(buf))
        nonblack = _viewport_nonblack_count(pil_img)
        print(
            f"[DEBUG] figure_to_viewport_pil: size={pil_img.size} nonblack={nonblack}",
            flush=True,
        )
        return pil_img
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_pil failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_pil()


def _pil_to_viewport_jpeg_path(pil_img) -> str:
    """Write opaque JPEG for gr.Image(type='filepath') — no alpha channel."""
    fd, path = tempfile.mkstemp(suffix=".jpg", prefix="myst_viewport_")
    os.close(fd)
    pil_img.convert("RGB").save(path, format="JPEG", quality=92, subsampling=0)
    return path


def figure_to_viewport_filepath(fig: plt.Figure, *, dpi: int = 100) -> str:
    """Matplotlib figure → PNG filepath for gr.Image(type='filepath') on HF."""
    print(f"[DEBUG] figure_to_viewport_filepath: dpi={dpi}", flush=True)
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
            tmp_path = tmp.name
        face = fig.get_facecolor()
        if not face or str(face).lower() in {"none", "auto"}:
            face = "#000000"
        fig.savefig(
            tmp_path,
            format="png",
            dpi=dpi,
            facecolor=face,
            edgecolor="none",
            bbox_inches="tight",
            pad_inches=0.05,
        )
        plt.close(fig)
        print(f"[DEBUG] figure_to_viewport_filepath: path={tmp_path}", flush=True)
        return tmp_path
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_filepath failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_filepath()


def unit_cell_error_placeholder_filepath() -> str:
    """Red PNG placeholder filepath when viewport conversion fails."""
    from PIL import Image as PILImage

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp") as tmp:
        tmp_path = tmp.name
    PILImage.fromarray(unit_cell_error_placeholder_numpy()).save(tmp_path, format="PNG")
    return tmp_path


def figure_to_viewport_file_html(fig: plt.Figure, *, dpi: int = 100) -> str:
    """Matplotlib figure → gr.HTML with /gradio_api/file= PNG (HF Spaces)."""
    print(f"[DEBUG] figure_to_viewport_file_html: dpi={dpi}", flush=True)
    try:
        path = figure_to_viewport_filepath(fig, dpi=dpi)
        html = _viewport_file_url_html(path)
        print(
            f"[DEBUG] figure_to_viewport_file_html: path={path} bytes={len(html)}",
            flush=True,
        )
        return html
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_file_html failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_file_html()


def unit_cell_error_placeholder_file_html() -> str:
    """Red placeholder gr.HTML via Gradio file URL."""
    return _viewport_file_url_html(unit_cell_error_placeholder_filepath(), error=True)


def figure_to_viewport_gradio_pil(fig: plt.Figure, *, dpi: int = 100):
    """Opaque RGB PIL for gr.Image(type='pil') — inline over websocket (HF-safe)."""
    print(f"[DEBUG] figure_to_viewport_gradio_pil: dpi={dpi}", flush=True)
    try:
        from PIL import Image as PILImage

        pil_img = figure_to_viewport_pil(fig, dpi=dpi)
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=92, subsampling=0)
        buf.seek(0)
        out = PILImage.open(buf).copy()
        print(f"[DEBUG] figure_to_viewport_gradio_pil: size={out.size}", flush=True)
        return out
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_gradio_pil failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_pil()


def unit_cell_error_placeholder_dict() -> dict:
    """Red placeholder as Gradio Image dict with inline base64 url."""
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.fromarray(unit_cell_error_placeholder_numpy()).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {
        "url": f"data:image/png;base64,{b64}",
        "mime_type": "image/png",
        "orig_name": "unit_cell_error.png",
    }


def figure_to_viewport_image_dict(fig: plt.Figure, *, dpi: int = 100) -> dict:
    """Matplotlib figure → Gradio Image dict with inline base64 url (HF-safe)."""
    print(f"[DEBUG] figure_to_viewport_image_dict: dpi={dpi}", flush=True)
    try:
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=dpi,
            facecolor=fig.get_facecolor(),
            bbox_inches="tight",
            pad_inches=0.02,
        )
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"
        print(
            f"[DEBUG] figure_to_viewport_image_dict: b64_len={len(b64)}",
            flush=True,
        )
        return {
            "url": data_url,
            "mime_type": "image/png",
            "orig_name": "unit_cell_viewport.png",
        }
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_image_dict failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_dict()


def figure_to_viewport_img_html(fig: plt.Figure, *, dpi: int = 100) -> str:
    """Matplotlib figure → inline base64 PNG for gr.HTML (no /tmp file URLs on HF)."""
    print(f"[DEBUG] figure_to_viewport_img_html: dpi={dpi}", flush=True)
    try:
        pil_img = _fit_on_black_canvas(figure_to_pil_image(fig, dpi=dpi))
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        px = UNIT_CELL_VIEWPORT_PX
        print(
            f"[DEBUG] figure_to_viewport_img_html: b64_len={len(b64)} "
            f"pil_size={pil_img.size}",
            flush=True,
        )
        return (
            '<div class="myst-unit-cell-viewport-img-wrap" '
            f'style="width:100%;height:{px}px;min-height:{px}px;max-height:{px}px;'
            'display:block;background:#000000;overflow:hidden;box-sizing:border-box;">'
            f'<img src="data:image/png;base64,{b64}" '
            'alt="Unit cell viewport" class="myst-unit-cell-viewport-img" '
            f'width="{pil_img.size[0]}" height="{pil_img.size[1]}" '
            f'style="width:100%;height:{px}px;max-width:100%;max-height:{px}px;'
            'object-fit:contain;object-position:center center;'
            'display:block;visibility:visible;opacity:1;" />'
            "</div>"
        )
    except Exception as exc:
        print(f"[ERROR] figure_to_viewport_img_html failed: {exc}", flush=True)
        traceback.print_exc()
        return unit_cell_error_placeholder_html()


def get_unit_cell_viewport_pil_image(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.35,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
    *,
    dpi: int = 150,
):
    """Build matplotlib unit cell and return a PIL Image for gr.Image."""
    _metrics, _header, fig = run_residual_explorer(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure,
        view_elev,
        view_azim,
    )
    print("[DEBUG] get_unit_cell_viewport_pil_image: building figure", flush=True)
    pil_img = export_unit_cell_pil_for_gradio(fig, dpi=dpi)
    print(f"[DEBUG] get_unit_cell_viewport_pil_image: done size={pil_img.size}", flush=True)
    return pil_img


def _ease_in_out_cubic(t: float) -> float:
    """Smooth acceleration/deceleration for deformation animation."""
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def _deformation_pressure_once(n_forward: int = 24) -> list[float]:
    """Single 0 → 1 pressure sweep for one-shot playback."""
    sweep_t = np.linspace(0.0, 1.0, max(4, int(n_forward)))
    return [_ease_in_out_cubic(float(t)) for t in sweep_t]


def _deformation_pressure_demo_sweep(target: float, n_forward: int = 28) -> list[float]:
    """Signed demo sweep from rigid (0) toward the preset deformation target."""
    target = _clamp_deform_pressure(target)
    if abs(target) < 0.02:
        sweep_t = np.linspace(0.0, 1.0, max(8, int(n_forward)))
        pulse = [0.22 * np.sin(float(t) * np.pi) for t in sweep_t]
        return [_clamp_deform_pressure(p) for p in pulse]
    sweep_t = np.linspace(0.0, 1.0, max(6, int(n_forward)))
    eased = [_ease_in_out_cubic(float(t)) for t in sweep_t]
    return [_clamp_deform_pressure(target * e) for e in eased]


def _deformation_pressure_loop(n_forward: int = 24) -> list[float]:
    """Ping-pong 0 → 1 → 0 pressure path for seamless video loops."""
    sweep_t = np.linspace(0.0, 1.0, max(4, int(n_forward)))
    forward = [_ease_in_out_cubic(float(t)) for t in sweep_t]
    reverse = list(reversed(forward[:-1]))
    return forward + reverse


def _ensure_even_frame(frame: np.ndarray) -> np.ndarray:
    """libx264 requires even width and height."""
    h, w = frame.shape[:2]
    h_even = h - (h % 2)
    w_even = w - (w % 2)
    if h_even == h and w_even == w:
        return frame
    return frame[:h_even, :w_even]


def _figure_to_rgb(fig: plt.Figure, *, dpi: int = 96) -> np.ndarray:
    """Rasterize a matplotlib figure to a fixed-size RGB frame."""
    from PIL import Image

    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        bbox_inches=None,
        pad_inches=0,
    )
    buf.seek(0)
    return _ensure_even_frame(np.asarray(Image.open(buf).convert("RGB")))


def _encode_loop_video(rgb_frames: list[np.ndarray], *, fps: int = 12) -> str:
    """Write frames to H.264 mp4 (browser-playable); fall back to looping GIF."""
    if not rgb_frames:
        raise ValueError("no frames to encode")

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        mp4_path = tmp.name

    try:
        import imageio.v2 as imageio

        writer = imageio.get_writer(
            mp4_path,
            fps=fps,
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
            macro_block_size=1,
        )
        try:
            for frame in rgb_frames:
                writer.append_data(_ensure_even_frame(frame))
        finally:
            writer.close()
        return mp4_path
    except Exception:
        try:
            os.unlink(mp4_path)
        except OSError:
            pass

    from PIL import Image

    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        gif_path = tmp.name
    pil_frames = [Image.fromarray(frame) for frame in rgb_frames]
    pil_frames[0].save(
        gif_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=max(1, int(1000 / fps)),
        loop=0,
    )
    return gif_path


def build_unit_cell_figure(
    delta_z: float = 0.15,
    delta_side: float = 0.08,
    *,
    r_val: float | None = None,
    pressure: float = 1.0,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
    view_dist: float = UNIT_CELL_VIEW_DIST,
    axis_half: float = UNIT_CELL_AXIS_HALF,
    show_curvature_grid: bool = True,
    dpi: int = 150,
) -> plt.Figure:
    """Server-rendered deformable unit cell — bowing π-face, concave φ/e sides."""
    from matplotlib.colors import to_rgba
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    s = 1.0
    side = abs(delta_side)
    p = _clamp_deform_pressure(pressure)
    p_abs = abs(p)
    edge_gold = _UNIT_CELL_GOLD
    eq_red = _UNIT_CELL_RED
    eq_green = _UNIT_CELL_GREEN
    eq_blue = _UNIT_CELL_BLUE

    bg = "#000000"
    font_main = 12
    font_small = 11
    font_tick = 10
    font_axis = 12
    caption_neutral = _UNIT_CELL_LABEL_TEXT

    fig = plt.figure(figsize=UNIT_CELL_FIGSIZE, dpi=dpi, facecolor=bg)
    ax = fig.add_subplot(111, projection="3d", facecolor=bg)

    triangles, tri_colors = _deformed_cube_surface(s, p, delta_z, side)
    ax.add_collection3d(
        Poly3DCollection(
            triangles,
            facecolors=[to_rgba(c) for c in tri_colors],
            edgecolors=(0, 0, 0, 0),
            linewidths=0.0,
        )
    )
    if show_curvature_grid and p_abs > 0.02:
        grid_alpha = 0.25 + 0.55 * p_abs
        for grid_line in _deformed_face_curvature_grid(s, p, delta_z, side):
            gx, gy, gz = zip(*grid_line)
            ax.plot(
                gx,
                gy,
                gz,
                color=edge_gold,
                linewidth=0.85,
                alpha=grid_alpha,
                zorder=4,
            )
    for edge_pts in _deformed_cube_edge_polylines(s, p, delta_z, side):
        xs, ys, zs = zip(*edge_pts)
        ax.plot(
            xs,
            ys,
            zs,
            color=edge_gold,
            linewidth=2.2,
            solid_capstyle="round",
            alpha=1.0,
            zorder=5,
        )

    arrow_scale = max(0.15, p_abs)
    arrow_kw = dict(arrow_length_ratio=0.28, linewidth=2.2, alpha=1.0)
    top_anchor = _anchor_point((0.0, 0.0, s), s, p, delta_z, side)
    ax.quiver(
        top_anchor[0],
        top_anchor[1],
        top_anchor[2] + 0.12,
        0,
        0,
        -delta_z * 2.0 * arrow_scale,
        color=eq_blue,
        **arrow_kw,
    )
    phi_anchor = _anchor_point((-s, 0.0, 0.0), s, p, delta_z, side)
    ax.quiver(
        phi_anchor[0] - 0.12,
        phi_anchor[1],
        phi_anchor[2],
        side * 2.0 * arrow_scale,
        0,
        0,
        color=eq_red,
        **arrow_kw,
    )
    e_anchor = _anchor_point((s, 0.0, 0.0), s, p, delta_z, side)
    ax.quiver(
        e_anchor[0] + 0.12,
        e_anchor[1],
        e_anchor[2],
        -side * 2.0 * arrow_scale,
        0,
        0,
        color=eq_green,
        **arrow_kw,
    )

    phi_face = _anchor_point((s, 0.0, 0.0), s, p, delta_z, side)
    e_face = _anchor_point((0.0, s, 0.0), s, p, delta_z, side)
    pi_face = _anchor_point((0.0, 0.0, s), s, p, delta_z, side)
    _draw_leader_label(
        ax,
        phi_face,
        (2.35, 0.45, 0.25),
        r"$T_\phi \propto \phi^2$",
        eq_red,
        fontsize=font_main,
    )
    _draw_leader_label(
        ax,
        e_face,
        (0.45, 2.35, 0.25),
        r"$T_e \propto e^2$",
        eq_green,
        fontsize=font_main,
    )
    _draw_leader_label(
        ax,
        pi_face,
        (0.45, 0.25, 2.35),
        r"$T_\pi \propto \pi^2$",
        eq_blue,
        fontsize=font_main,
    )
    _draw_leader_label(
        ax,
        _anchor_point((-s, 0.0, 0.0), s, p, delta_z, side),
        (-2.35, -0.55, 0.35),
        r"$\delta_\mathrm{side}$ (inward)",
        eq_green,
        fontsize=font_small,
    )
    _draw_leader_label(
        ax,
        pi_face,
        (-0.55, -2.25, 2.35),
        r"$\delta_z$ (push)",
        eq_blue,
        fontsize=font_small,
    )

    half = float(max(2.0, axis_half))
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_zlim(-half, half)
    ax.set_xlabel("φ-face", color=caption_neutral, fontsize=font_axis, labelpad=4)
    ax.set_ylabel("e-face", color=caption_neutral, fontsize=font_axis, labelpad=4)
    ax.set_zlabel("π-face", color=caption_neutral, fontsize=font_axis, labelpad=4)
    ax.tick_params(colors=caption_neutral, labelsize=font_tick)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor("#333333")
    ax.grid(True, color="#505050")
    elev = float(np.clip(view_elev, 5.0, 85.0))
    azim = float(view_azim) % 360.0
    ax.view_init(elev=elev, azim=azim)
    ax.dist = float(max(8.0, view_dist))
    try:
        ax.set_box_aspect((1, 1, 1))
    except (AttributeError, TypeError, ValueError):
        pass
    ax.set_position([0.0, 0.0, 1.0, 1.0])

    fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0, wspace=0, hspace=0)
    return fig


def _rgba_to_plotly_color(rgba: tuple[float, float, float, float]) -> str:
    r, g, b, a = rgba
    return f"rgba({int(r * 255)},{int(g * 255)},{int(b * 255)},{float(a):.3f})"


def _plotly_camera_from_view(
    elev: float,
    azim: float,
    *,
    radius: float = 2.35,
) -> dict[str, dict[str, float]]:
    elev_rad = np.deg2rad(float(elev))
    azim_rad = np.deg2rad(float(azim))
    x = radius * np.cos(elev_rad) * np.cos(azim_rad)
    y = radius * np.sin(elev_rad)
    z = radius * np.cos(elev_rad) * np.sin(azim_rad)
    return {
        "eye": {"x": float(x), "y": float(y), "z": float(z)},
        "center": {"x": 0.0, "y": 0.0, "z": 0.0},
        "up": {"x": 0.0, "y": 1.0, "z": 0.0},
    }


def build_unit_cell_plotly_figure(
    delta_z: float = 0.15,
    delta_side: float = 0.08,
    *,
    r_val: float | None = None,
    pressure: float = 1.0,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
    axis_half: float = UNIT_CELL_AXIS_HALF,
    show_curvature_grid: bool = True,
):
    """Interactive Plotly unit-cell mesh for Render preset detail view."""
    import plotly.graph_objects as go

    _ = r_val
    s = 1.0
    side = abs(delta_side)
    p = _clamp_deform_pressure(pressure)
    p_abs = abs(p)
    triangles, tri_colors = _deformed_cube_surface(s, p, delta_z, side)

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    i_idx: list[int] = []
    j_idx: list[int] = []
    k_idx: list[int] = []
    face_colors: list[str] = []
    for tri, rgba in zip(triangles, tri_colors, strict=True):
        base = len(xs)
        for vtx in tri:
            xs.append(float(vtx[0]))
            ys.append(float(vtx[1]))
            zs.append(float(vtx[2]))
        i_idx.append(base)
        j_idx.append(base + 1)
        k_idx.append(base + 2)
        face_colors.append(_rgba_to_plotly_color(rgba))

    traces: list[go.Mesh3d | go.Scatter3d] = [
        go.Mesh3d(
            x=xs,
            y=ys,
            z=zs,
            i=i_idx,
            j=j_idx,
            k=k_idx,
            facecolor=face_colors,
            flatshading=True,
            lighting=dict(ambient=0.55, diffuse=0.85, specular=0.25, roughness=0.5),
            lightposition=dict(x=2, y=4, z=3),
            hoverinfo="skip",
            showscale=False,
        )
    ]

    if show_curvature_grid and p_abs > 0.02:
        grid_alpha = 0.25 + 0.55 * p_abs
        for grid_line in _deformed_face_curvature_grid(s, p, delta_z, side):
            gx, gy, gz = zip(*grid_line, strict=True)
            traces.append(
                go.Scatter3d(
                    x=list(gx),
                    y=list(gy),
                    z=list(gz),
                    mode="lines",
                    line=dict(
                        color=f"rgba(201,162,39,{grid_alpha:.3f})",
                        width=2,
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    for edge_pts in _deformed_cube_edge_polylines(s, p, delta_z, side):
        ex, ey, ez = zip(*edge_pts, strict=True)
        traces.append(
            go.Scatter3d(
                x=list(ex),
                y=list(ey),
                z=list(ez),
                mode="lines",
                line=dict(color=_UNIT_CELL_GOLD, width=5),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    half = float(max(2.0, axis_half))
    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, t=0, b=0, pad=0),
        autosize=True,
        scene=dict(
            xaxis=dict(range=[-half, half], visible=False, showbackground=False),
            yaxis=dict(range=[-half, half], visible=False, showbackground=False),
            zaxis=dict(range=[-half, half], visible=False, showbackground=False),
            aspectmode="cube",
            camera=_plotly_camera_from_view(view_elev, view_azim),
            dragmode="orbit",
        ),
        showlegend=False,
        uirevision="mystery-unit-cell",
    )
    return fig


def run_residual_explorer_plotly(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.35,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
):
    """Return an interactive Plotly unit-cell figure for preset detail view."""
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    return build_unit_cell_plotly_figure(
        delta_z=delta_z,
        delta_side=abs(d_side) * 0.5,
        r_val=r_val,
        pressure=deform_pressure,
        view_elev=view_elev,
        view_azim=view_azim,
    )


def plotly_figure_to_render_detail_html(fig) -> str:
    """Embed a responsive Plotly figure for the Render preset detail page."""
    import plotly.io as pio

    div = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn",
        config={
            "responsive": True,
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
        },
        div_id="myst-render-detail-plotly",
    )
    return f'<div class="myst-render-detail-plotly-wrap">{div}</div>'


def run_residual_explorer(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.35,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
) -> tuple[str, str, plt.Figure]:
    """Return explorer metrics, viewport header HTML, and unit-cell figure."""
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    metrics = format_residual_explorer(
        phi_sq_scale, e_sq_scale, pi_sq_scale, kappa, delta_z, alpha, beta
    )
    p = _clamp_deform_pressure(deform_pressure)
    mode = _deform_pressure_hint(p)
    metrics = (
        f"{metrics}\n\n"
        f"Deformation pressure : {p * 100:.1f}%  ({mode})\n"
        f"View                 : elev {view_elev:.0f}° · azim {view_azim:.0f}°"
    )
    fig = build_unit_cell_figure(
        delta_z=delta_z,
        delta_side=abs(d_side) * 0.5,
        r_val=r_val,
        pressure=p,
        view_elev=view_elev,
        view_azim=view_azim,
    )
    header = build_unit_cell_viewport_header_html(pressure=p, r_val=r_val)
    return metrics, header, fig


def stream_unit_cell_deformation(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.35,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
):
    """Yield frames sweeping deformation pressure 0 → 1 → hold (animation)."""
    import time

    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    base_metrics = format_residual_explorer(
        phi_sq_scale, e_sq_scale, pi_sq_scale, kappa, delta_z, alpha, beta
    )
    side = abs(d_side) * 0.5
    hold = float(np.clip(deform_pressure, 0.0, 1.0))

    sweep_t = np.linspace(0.0, 1.0, 20)
    eased = [_ease_in_out_cubic(t) for t in sweep_t]
    ease_steps = 4 if hold < 0.995 else 0
    total_frames = len(eased) + ease_steps
    frame_idx = 0
    def _yield_frame(
        metrics_text: str,
        pressure_val: float,
        *,
        phase: str,
    ) -> tuple[str, str, plt.Figure, dict[str, float | int | str | None]]:
        nonlocal frame_idx
        fig = build_unit_cell_figure(
            delta_z=delta_z,
            delta_side=side,
            r_val=r_val,
            pressure=pressure_val,
            view_elev=view_elev,
            view_azim=view_azim,
            show_curvature_grid=False,
            dpi=80,
        )
        header = build_unit_cell_viewport_header_html(
            pressure=pressure_val,
            r_val=r_val,
            frame_idx=frame_idx,
            total_frames=total_frames,
        )
        key_metrics = deformation_key_metrics(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            pressure_val,
            frame_idx=frame_idx,
            total_frames=total_frames,
        )
        key_metrics["phase"] = phase
        return metrics_text, header, fig, key_metrics

    for pressure in eased:
        frame_idx += 1
        p = float(pressure)
        km = deformation_key_metrics(
            phi_sq_scale,
            e_sq_scale,
            pi_sq_scale,
            kappa,
            delta_z,
            alpha,
            beta,
            p,
            frame_idx=frame_idx,
            total_frames=total_frames,
        )
        metrics = (
            f"{base_metrics}\n\n"
            f"=== LIVE FRAME {frame_idx}/{total_frames} ===\n"
            f"Deformation pressure : {p * 100:.1f}%\n"
            f"R (residual)         : {km['r']:+.6f}\n"
            f"δ_side               : {km['delta_side']:.6f}\n"
            f"B(κ) − R             : {km['b_minus_r']:+.6f}\n"
            f"W_g (350/π)          : {km['w_g']:.4f}\n"
            f"Mode                 : {km['deform_hint']}\n"
            f"▶ animating bow/concave"
        )
        yield _yield_frame(metrics, p, phase="sweep")
        time.sleep(0.03)

    if hold < 0.995:
        for pressure in np.linspace(1.0, hold, ease_steps):
            frame_idx += 1
            p = float(pressure)
            km = deformation_key_metrics(
                phi_sq_scale,
                e_sq_scale,
                pi_sq_scale,
                kappa,
                delta_z,
                alpha,
                beta,
                p,
                frame_idx=frame_idx,
                total_frames=total_frames,
            )
            metrics = (
                f"{base_metrics}\n\n"
                f"=== LIVE FRAME {frame_idx}/{total_frames} ===\n"
                f"Deformation pressure : {p * 100:.1f}%\n"
                f"R (residual)         : {km['r']:+.6f}\n"
                f"δ_side               : {km['delta_side']:.6f}\n"
                f"B(κ) − R             : {km['b_minus_r']:+.6f}\n"
                f"W_g (350/π)          : {km['w_g']:.4f}\n"
                f"Mode                 : {km['deform_hint']}\n"
                f"▶ easing to slider"
            )
            yield _yield_frame(metrics, p, phase="ease")
            time.sleep(0.03)

    metrics, header, fig = run_residual_explorer(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure=hold,
        view_elev=view_elev,
        view_azim=view_azim,
    )
    final_km = deformation_key_metrics(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        hold,
        frame_idx=total_frames,
        total_frames=total_frames,
    )
    final_km["phase"] = "hold"
    yield metrics, header, fig, final_km


def render_unit_cell_deformation_video(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.35,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
    *,
    fps: int = 12,
    dpi: int = 96,
    progress=None,
) -> tuple[str, str, str, plt.Figure, dict[str, float | int | str | None]]:
    """Render a one-shot deformation sweep (mp4/gif) for Gradio playback."""
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    side = abs(d_side) * 0.5
    hold = float(np.clip(deform_pressure, 0.0, 1.0))
    pressures = _deformation_pressure_once()
    total_frames = len(pressures)
    rgb_frames: list[np.ndarray] = []

    for frame_idx, pressure_val in enumerate(pressures, start=1):
        if progress is not None:
            progress(frame_idx / total_frames, desc=f"Rendering frame {frame_idx}/{total_frames}")
        p = float(pressure_val)
        fig = build_unit_cell_figure(
            delta_z=delta_z,
            delta_side=side,
            r_val=r_val,
            pressure=p,
            view_elev=view_elev,
            view_azim=view_azim,
            show_curvature_grid=False,
            dpi=dpi,
        )
        rgb_frames.append(_figure_to_rgb(fig, dpi=dpi))
        plt.close(fig)

    if progress is not None:
        progress(0.98, desc="Encoding deformation video…")
    video_path = _encode_loop_video(rgb_frames, fps=fps)

    metrics, header, fig = run_residual_explorer(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        deform_pressure=hold,
        view_elev=view_elev,
        view_azim=view_azim,
    )
    final_km = deformation_key_metrics(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        hold,
        frame_idx=total_frames,
        total_frames=total_frames,
    )
    final_km["phase"] = "once"
    metrics = (
        f"{metrics}\n\n"
        f"=== DEFORMATION PLAYBACK ===\n"
        f"Frames rendered       : {total_frames} @ {fps} fps\n"
        f"Playback              : single 0→100% sweep (plays once)\n"
        f"Hold pressure         : {hold * 100:.1f}%"
    )
    if progress is not None:
        progress(1.0, desc="Video ready")
    return video_path, metrics, header, fig, final_km


def _breathing_deformation_path(*, n_per_segment: int = 12) -> list[float]:
    """Full breathing cycle: rigid → max convex → rigid → max concave → 08 → 07 → 06 → rigid."""

    def _segment(start: float, end: float, n: int, *, skip_first: bool = False) -> list[float]:
        vals = np.linspace(float(start), float(end), max(2, int(n)), endpoint=True)
        if skip_first and len(vals) > 1:
            vals = vals[1:]
        return [_clamp_deform_pressure(float(v)) for v in vals]

    path: list[float] = []
    path += _segment(0.0, 1.0, n_per_segment)  # Preset 05 → 01
    path += _segment(1.0, 0.0, n_per_segment, skip_first=True)  # 01 → 05
    path += _segment(0.0, -1.0, n_per_segment, skip_first=True)  # 05 → 09
    for target in (-0.75, -0.5, -0.25, 0.0):  # 09 → 08 → 07 → 06 → 05
        path += _segment(path[-1], target, max(4, n_per_segment // 2), skip_first=True)
    return path


_BREATHING_ANIMATION_CACHE: object | None = None


def build_breathing_animation_figure(
    *,
    n_per_segment: int = 12,
    frame_duration_ms: int = 90,
):
    """Looping Plotly breathing animation — rigid ↔ convex ↔ concave unit cell."""
    global _BREATHING_ANIMATION_CACHE
    if _BREATHING_ANIMATION_CACHE is not None:
        return _BREATHING_ANIMATION_CACHE

    import plotly.graph_objects as go

    phi = 1.0
    e = 1.0
    pi = 1.0
    kappa = KAPPA_DOC
    delta_z = 0.1
    alpha = 1.0
    beta = 1.0
    view_elev = UNIT_CELL_VIEW_ELEV
    view_azim = UNIT_CELL_VIEW_AZIM
    r_val = residual_from_scales(phi, e, pi)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    side = abs(d_side) * 0.5

    pressures = _breathing_deformation_path(n_per_segment=n_per_segment)
    frames: list[go.Frame] = []
    first_data = None
    half = float(max(2.0, UNIT_CELL_AXIS_HALF))

    for idx, pressure in enumerate(pressures):
        frame_fig = build_unit_cell_plotly_figure(
            delta_z=delta_z,
            delta_side=side,
            pressure=pressure,
            view_elev=view_elev,
            view_azim=view_azim,
            show_curvature_grid=False,
        )
        if first_data is None:
            first_data = frame_fig.data
        frames.append(go.Frame(data=frame_fig.data, name=str(idx)))

    fig = go.Figure(data=first_data, frames=frames)
    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, t=8, b=0),
        height=650,
        autosize=True,
        scene=dict(
            xaxis=dict(range=[-half, half], visible=False, showbackground=False),
            yaxis=dict(range=[-half, half], visible=False, showbackground=False),
            zaxis=dict(range=[-half, half], visible=False, showbackground=False),
            aspectmode="cube",
            camera=_plotly_camera_from_view(view_elev, view_azim),
            dragmode="orbit",
        ),
        showlegend=False,
        uirevision="mystery-breathing",
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "y": 1.08,
                "x": 0.05,
                "buttons": [
                    {
                        "label": "▶ Breathing",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": frame_duration_ms, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    }
                ],
            }
        ],
    )
    print(
        f"[breathing] build_breathing_animation_figure: {len(frames)} frames",
        flush=True,
    )
    _BREATHING_ANIMATION_CACHE = fig
    return fig


def create_breathing_animation(*, fresh: bool = False):
    """Viewport-ready Plotly breathing figure (54 frames) for Demo A."""
    import plotly.graph_objects as go

    fig = build_breathing_animation_figure()
    if not fig.frames:
        print("WARNING: No frames found in breathing animation!", flush=True)
    else:
        print(f"[breathing] create_breathing_animation: {len(fig.frames)} frames", flush=True)

    fig.update_layout(
        height=620,
        margin=dict(l=0, r=0, t=40, b=0),
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "y": 1.1,
                "x": 0.02,
                "buttons": [
                    {
                        "label": "▶ Breathing",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 85, "redraw": True},
                                "fromcurrent": True,
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    }
                ],
            }
        ],
    )
    if fresh:
        fig = go.Figure(fig.to_dict())
        fig.update_layout(uirevision="mystery-breathing-fresh")
    return fig


def render_gravity_demo_animation_video(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.0,
    view_elev: float = UNIT_CELL_VIEW_ELEV,
    view_azim: float = UNIT_CELL_VIEW_AZIM,
    *,
    fps: int = 10,
    dpi: int = 88,
) -> str:
    """Render a looping signed deformation demo (0 → target) for Gravity viewport."""
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    side = abs(d_side) * 0.5
    target = _clamp_deform_pressure(deform_pressure)
    pressures = _deformation_pressure_demo_sweep(target)
    rgb_frames: list[np.ndarray] = []
    for pressure_val in pressures:
        p = float(pressure_val)
        fig = build_unit_cell_figure(
            delta_z=delta_z,
            delta_side=side,
            r_val=r_val,
            pressure=p,
            view_elev=view_elev,
            view_azim=view_azim,
            show_curvature_grid=False,
            dpi=dpi,
        )
        rgb_frames.append(_figure_to_rgb(fig, dpi=dpi))
        plt.close(fig)
    return _encode_loop_video(rgb_frames, fps=fps)


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
            "THIS SPACE — demo-oriented (browser):",
            "  · φ-e-π triangle angles & side ratios",
            "  · B(κ) = π²(e/π−κ) holonomy-gap scaling",
            "  · κ slider + triangle + κ-sweep plots",
            "  · CLI terminal + keypad (you are here)",
            "",
            "GITHUB REPO — full depth:",
            "  · notes/angle_derivation.md — step-by-step angles",
            "  · 11 probes: PDE, conduit, meta-opt, Rodin map",
            "  · JSON reports → outputs/ (run_all.py)",
            "",
            "Early-stage project · Press 09 for catalog.",
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


