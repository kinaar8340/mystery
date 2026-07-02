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

Use the **interactive 3D unit cell** below (drag to rotate; arrows update with the Residual explorer).
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


def _plotly_arrow(
    fig,
    start: tuple[float, float, float],
    direction: tuple[float, float, float],
    *,
    color: str,
    name: str,
    width: int = 6,
) -> None:
    import plotly.graph_objects as go

    end = (
        start[0] + direction[0],
        start[1] + direction[1],
        start[2] + direction[2],
    )
    fig.add_trace(
        go.Scatter3d(
            x=[start[0], end[0]],
            y=[start[1], end[1]],
            z=[start[2], end[2]],
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=width),
            marker=dict(size=[3, 8], color=color, symbol=["circle", "diamond"]),
            hovertemplate=f"{name}<extra></extra>",
        )
    )


def build_unit_cell_plotly(
    delta_z: float = 0.15,
    delta_side: float = 0.08,
) -> dict:
    """Interactive 3D unit cell: semi-transparent cube, tensions, δ_z / δ_side arrows."""
    import plotly.graph_objects as go

    s = 1.0
    verts = [
        (-s, -s, -s),
        (s, -s, -s),
        (s, s, -s),
        (-s, s, -s),
        (-s, -s, s),
        (s, -s, s),
        (s, s, s),
        (-s, s, s),
    ]
    x, y, z = zip(*verts)
    # Two triangles per cube face (vertex indices).
    i = (0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1)
    j = (1, 2, 5, 6, 3, 7, 3, 6, 4, 5, 5, 6)
    k = (2, 3, 6, 7, 7, 4, 6, 7, 5, 1, 6, 2)
    edges = (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    )
    fig = go.Figure()
    fig.add_trace(
        go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            color="#8ecae6",
            opacity=0.28,
            flatshading=True,
            hoverinfo="skip",
            showlegend=False,
        )
    )
    for i_edge, j_edge in edges:
        fig.add_trace(
            go.Scatter3d(
                x=[verts[i_edge][0], verts[j_edge][0]],
                y=[verts[i_edge][1], verts[j_edge][1]],
                z=[verts[i_edge][2], verts[j_edge][2]],
                mode="lines",
                line=dict(color="#457b9d", width=5),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    tension_labels = (
        (1.55, 0.0, 0.0, "T<sub>φ</sub> ∝ φ²", "#c9a227"),
        (0.0, 1.55, 0.0, "T<sub>e</sub> ∝ e²", "#2a9d8f"),
        (0.0, 0.0, 1.55, "T<sub>π</sub> ∝ π²", "#e63946"),
    )
    for tx, ty, tz, label, color in tension_labels:
        fig.add_trace(
            go.Scatter3d(
                x=[tx],
                y=[ty],
                z=[tz],
                mode="text",
                text=[label],
                textfont=dict(color=color, size=12),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    _plotly_arrow(
        fig,
        (0.0, 0.0, s + 0.05),
        (0.0, 0.0, -delta_z * 2.5),
        color="#c9a227",
        name="δ_z — π-face push",
    )
    _plotly_arrow(
        fig,
        (-s - 0.05, 0.0, 0.0),
        (delta_side * 2.5, 0.0, 0.0),
        color="#457b9d",
        name="δ_side — φ-face",
    )
    _plotly_arrow(
        fig,
        (s + 0.05, 0.0, 0.0),
        (-delta_side * 2.5, 0.0, 0.0),
        color="#2a9d8f",
        name="δ_side — e-face",
    )

    fig.add_trace(
        go.Scatter3d(
            x=[0],
            y=[0],
            z=[0],
            mode="markers+text",
            name="R imbalance",
            marker=dict(size=6, color="#e63946"),
            text=[f"R ≈ {R:+.3f}"],
            textposition="bottom center",
            textfont=dict(color="#e63946", size=12),
            hovertemplate="R = φ²+e²−π²<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text=(
                f"Unit cell deformation — R = φ²+e²−π² ≈ {R:+.3f} drives net δ_side contraction"
            ),
            font=dict(color="#e8e0f8", size=13),
        ),
        paper_bgcolor="rgba(10, 8, 24, 0)",
        plot_bgcolor="rgba(10, 8, 24, 0)",
        scene=dict(
            xaxis=dict(title="φ-face", color="#a89ec8", gridcolor="rgba(255,255,255,0.08)"),
            yaxis=dict(title="e-face", color="#a89ec8", gridcolor="rgba(255,255,255,0.08)"),
            zaxis=dict(title="π-face", color="#a89ec8", gridcolor="rgba(255,255,255,0.08)"),
            bgcolor="rgba(10, 8, 24, 0.35)",
            aspectmode="cube",
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.1)),
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(font=dict(color="#e8e0f8"), bgcolor="rgba(18,10,28,0.7)"),
        height=420,
    )
    return fig.to_plotly_json()


def run_residual_explorer(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
) -> tuple[str, dict]:
    """Return explorer metrics text and updated Plotly unit-cell figure."""
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    metrics = format_residual_explorer(
        phi_sq_scale, e_sq_scale, pi_sq_scale, kappa, delta_z, alpha, beta
    )
    fig = build_unit_cell_plotly(delta_z=delta_z, delta_side=abs(d_side) * 0.5)
    return metrics, fig


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


