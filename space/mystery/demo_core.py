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
_UNIT_CELL_RED = "#e63946"
_UNIT_CELL_GREEN = "#22c55e"
_UNIT_CELL_BLUE = "#2563eb"


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
    """Return (dx, dy, dz) offsets and signed mode weights for coloring."""
    if pressure <= 0.0:
        return 0.0, 0.0, 0.0, {
            "pi_bowl": 0.0,
            "phi_concave": 0.0,
            "e_concave": 0.0,
            "bottom_convex": 0.0,
        }

    w = _deformation_weights(x, y, z, s)
    bowl = w["bowl"]
    equator = w["equator"]

    # π-face: parabolic bowl — concave when viewed from above
    pi_mag = pressure * delta_z * 5.0 * w["top_w"] * bowl
    dz_pi = -pi_mag

    # φ / e lateral faces: concave pinch toward cell center
    phi_mag = 0.0
    e_mag = 0.0
    dx_side = 0.0
    dy_side = 0.0
    if abs(x) > 1e-9:
        phi_mag = pressure * delta_side * 3.6 * w["x_edge"] * equator * (1.0 - 0.25 * bowl)
        dx_side = -np.sign(x) * phi_mag
    if abs(y) > 1e-9:
        e_mag = pressure * delta_side * 3.6 * w["y_edge"] * equator * (1.0 - 0.25 * bowl)
        dy_side = -np.sign(y) * e_mag

    # Bottom: compensatory convex dome (anticlastic response)
    bottom_mag = pressure * delta_z * 0.85 * w["bottom_w"] * bowl
    dz_bottom = bottom_mag

    modes = {
        "pi_bowl": pi_mag,
        "phi_concave": phi_mag,
        "e_concave": e_mag,
        "bottom_convex": bottom_mag,
    }
    return dx_side, dy_side, dz_pi + dz_bottom, modes


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
    blend = min(1.0, mag / max(0.08, pressure * 0.35 + 0.05))
    palette = {
        "pi_bowl": eq_blue,
        "phi_concave": eq_red,
        "e_concave": eq_green,
        "bottom_convex": (0.35, 0.62, 0.95),
    }
    base = palette.get(dominant, neutral)
    rgb = tuple(neutral[i] + blend * (base[i] - neutral[i]) for i in range(3))
    alpha = 0.12 + 0.38 * min(1.0, pressure)
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
    color: str,
    *,
    fontsize: float = 12,
) -> None:
    """Leader line from cube anchor to offset label (solid, color-matched)."""
    ax.plot(
        [anchor[0], label_pos[0]],
        [anchor[1], label_pos[1]],
        [anchor[2], label_pos[2]],
        color=color,
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
        color=color,
        fontsize=fontsize,
        ha="center",
        va="center",
        alpha=1.0,
        zorder=9,
    )


def _ease_in_out_cubic(t: float) -> float:
    """Smooth acceleration/deceleration for deformation animation."""
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def build_unit_cell_figure(
    delta_z: float = 0.15,
    delta_side: float = 0.08,
    *,
    r_val: float | None = None,
    pressure: float = 1.0,
    view_elev: float = 22.0,
    view_azim: float = 45.0,
    show_curvature_grid: bool = True,
    dpi: int = 120,
) -> plt.Figure:
    """Server-rendered deformable unit cell — bowing π-face, concave φ/e sides."""
    from matplotlib.colors import to_rgba
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    s = 1.0
    r_show = R if r_val is None else r_val
    side = abs(delta_side)
    p = float(np.clip(pressure, 0.0, 1.0))
    matrix_green = _UNIT_CELL_MATRIX_GREEN
    eq_red = _UNIT_CELL_RED
    eq_green = _UNIT_CELL_GREEN
    eq_blue = _UNIT_CELL_BLUE

    bg = "#000000"
    font_main = 12
    font_small = 11
    font_caption = 11
    font_tick = 10
    font_title = 13
    font_axis = 12
    caption_neutral = "#ffffff"

    fig = plt.figure(figsize=(8, 6.5), dpi=dpi, facecolor=bg)
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
    if show_curvature_grid and p > 0.02:
        grid_alpha = 0.25 + 0.55 * p
        for grid_line in _deformed_face_curvature_grid(s, p, delta_z, side):
            gx, gy, gz = zip(*grid_line)
            ax.plot(
                gx,
                gy,
                gz,
                color=matrix_green,
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
            color=matrix_green,
            linewidth=2.2,
            solid_capstyle="round",
            alpha=1.0,
            zorder=5,
        )

    arrow_scale = max(0.15, p)
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

    from matplotlib.patches import FancyBboxPatch

    caption_y = 0.085
    fig.add_artist(
        FancyBboxPatch(
            (0.14, 0.055),
            0.72,
            0.05,
            boxstyle="round,pad=0.008",
            transform=fig.transFigure,
            facecolor="#000000",
            edgecolor=matrix_green,
            linewidth=1.2,
            alpha=1.0,
            zorder=4,
        )
    )
    caption_segments = (
        (0.17, "R = ", caption_neutral),
        (0.215, r"$\phi^2$", eq_red),
        (0.255, " + ", caption_neutral),
        (0.275, r"$e^2$", eq_green),
        (0.305, " − ", caption_neutral),
        (0.325, r"$\pi^2$", eq_blue),
        (0.355, f" ≈ {r_show:+.3f} drives net ", caption_neutral),
        (0.545, r"$\delta_\mathrm{side}$", eq_green),
        (0.595, " contraction", caption_neutral),
    )
    for x_pos, label, label_color in caption_segments:
        fig.text(
            x_pos,
            caption_y,
            label,
            transform=fig.transFigure,
            ha="left",
            color=label_color,
            fontsize=font_caption,
            alpha=1.0,
            zorder=6,
        )

    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-2.6, 2.6)
    ax.set_zlim(-2.6, 2.6)
    ax.set_xlabel("φ-face", color=caption_neutral, fontsize=font_axis, labelpad=8)
    ax.set_ylabel("e-face", color=caption_neutral, fontsize=font_axis, labelpad=8)
    ax.set_zlabel("π-face", color=caption_neutral, fontsize=font_axis, labelpad=8)
    ax.tick_params(colors=caption_neutral, labelsize=font_tick)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor("#333333")
    ax.grid(True, color="#505050")
    elev = float(np.clip(view_elev, 5.0, 85.0))
    azim = float(view_azim) % 360.0
    ax.view_init(elev=elev, azim=azim)

    if p < 0.04:
        deform_hint = "rigid cube"
    elif p < 0.45:
        deform_hint = "mild bow + side pinch"
    elif p < 0.8:
        deform_hint = "π bowl concave · φ/e sides curving inward"
    else:
        deform_hint = "full concave bowl + compensatory bottom convex bulge"

    ax.set_title(
        f"Deformable unit cell — pressure {p * 100:.0f}% · {deform_hint}",
        color=caption_neutral,
        fontsize=font_title,
        pad=14,
    )

    legend_y = 0.94
    legend_items = (
        (0.16, r"$\pi$ bowl (concave)", eq_blue),
        (0.38, r"$\phi$ face pinch", eq_red),
        (0.56, r"$e$ face pinch", eq_green),
        (0.74, "bottom convex", (0.35, 0.62, 0.95)),
    )
    for x_pos, label, color in legend_items:
        fig.text(
            x_pos,
            legend_y,
            "■",
            transform=fig.transFigure,
            ha="center",
            color=color,
            fontsize=font_small,
            alpha=0.55 + 0.45 * p,
            zorder=6,
        )
        fig.text(
            x_pos + 0.02,
            legend_y,
            label,
            transform=fig.transFigure,
            ha="left",
            color=caption_neutral,
            fontsize=font_caption - 1,
            alpha=0.75,
            zorder=6,
        )
    fig.tight_layout()
    return fig


def run_residual_explorer(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.35,
    view_elev: float = 22.0,
    view_azim: float = 45.0,
) -> tuple[str, plt.Figure]:
    """Return explorer metrics text and updated deformable unit-cell figure."""
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    metrics = format_residual_explorer(
        phi_sq_scale, e_sq_scale, pi_sq_scale, kappa, delta_z, alpha, beta
    )
    p = float(np.clip(deform_pressure, 0.0, 1.0))
    mode = (
        "rigid"
        if p < 0.05
        else "mild curvature"
        if p < 0.45
        else "strong concave bowl"
        if p < 0.85
        else "max bow + bottom convex bulge"
    )
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
    return metrics, fig


def stream_unit_cell_deformation(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    deform_pressure: float = 0.35,
    view_elev: float = 22.0,
    view_azim: float = 45.0,
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

    sweep_t = np.linspace(0.0, 1.0, 36)
    eased = [_ease_in_out_cubic(t) for t in sweep_t]
    total_frames = len(eased) + (8 if hold < 0.995 else 0)
    frame_idx = 0
    prev_fig: plt.Figure | None = None

    def _yield_frame(metrics_text: str, pressure_val: float) -> tuple[str, plt.Figure]:
        nonlocal prev_fig
        fig = build_unit_cell_figure(
            delta_z=delta_z,
            delta_side=side,
            r_val=r_val,
            pressure=pressure_val,
            view_elev=view_elev,
            view_azim=view_azim,
            dpi=100,
        )
        if prev_fig is not None:
            plt.close(prev_fig)
        prev_fig = fig
        return metrics_text, fig

    for pressure in eased:
        frame_idx += 1
        p = float(pressure)
        metrics = (
            f"{base_metrics}\n\n"
            f"Deformation pressure : {p * 100:.1f}%  "
            f"▶ animating bow/concave ({frame_idx}/{total_frames})"
        )
        yield _yield_frame(metrics, p)
        time.sleep(0.055)

    if hold < 0.995:
        for pressure in np.linspace(1.0, hold, 8):
            frame_idx += 1
            p = float(pressure)
            metrics = (
                f"{base_metrics}\n\n"
                f"Deformation pressure : {p * 100:.1f}%  "
                f"▶ easing to slider ({frame_idx}/{total_frames})"
            )
            yield _yield_frame(metrics, p)
            time.sleep(0.04)

    if prev_fig is not None:
        plt.close(prev_fig)
        prev_fig = None

    yield run_residual_explorer(
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


