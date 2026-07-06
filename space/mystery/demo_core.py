"""Shared φ-e-π analysis helpers for Mystery Gradio and HF Spaces."""

from __future__ import annotations

import base64
import colorsys
import html
import io
import os
import shutil
import subprocess
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
E_INV2 = float(np.exp(-2.0))
GOLDEN_ANGLE_DEG = 360.0 * (1.0 - 1.0 / PHI)
GOLDEN_ANGLE_FRACTION = GOLDEN_ANGLE_DEG / 1000.0
GOLDEN_ANGLE_RAD = float(np.radians(GOLDEN_ANGLE_DEG))
UNIT_CELL_VIEWPORT_PX = 550
UNIT_CELL_FIGSIZE = (6.0, 6.0)
UNIT_CELL_VIEW_ELEV = 26.0
UNIT_CELL_VIEW_AZIM = 45.0
UNIT_CELL_VIEW_DIST = 14.0
UNIT_CELL_AXIS_HALF = 2.35
UNIT_CELL_SHAPE_ONLY_AXIS_HALF = 1.35
UNIT_CELL_SHAPE_ONLY_VIEW_DIST = 9.0
UNIT_CELL_DETAIL_FIGSIZE = (6.5, 6.5)
UNIT_CELL_DETAIL_DPI = 100
UNIT_CELL_DETAIL_AXIS_HALF = 3.05
UNIT_CELL_DETAIL_VIEW_DIST = 30.0
UNIT_CELL_DETAIL_PLOTLY_RADIUS = 3.0
UNIT_CELL_DETAIL_PLOTLY_HEIGHT = 680
# Detail-page typography only (Figures 3×3 grid uses shape_only — unchanged).
UNIT_CELL_DETAIL_LABEL_FONT_MAIN = 15
UNIT_CELL_DETAIL_LABEL_FONT_SMALL = 14
UNIT_CELL_DETAIL_LABEL_EDGE_INSET = 0.12
UNIT_CELL_DETAIL_AXIS_TITLE_FONT = 12
UNIT_CELL_DETAIL_AXIS_TICK_FONT = 11

_DEFAULT_DIMENSION = "D6"
_DIMENSION_IDS: tuple[str, ...] = ("D4", "D6", "D8", "D12", "D20")


def geodesic_face_count(dimension: str) -> int:
    """Face count encoded in Mystery nav ids — D4 → 4 faces, D20 → 20, etc."""
    dim = str(dimension or _DEFAULT_DIMENSION).strip().upper()
    if dim.startswith("D") and dim[1:].isdigit():
        return int(dim[1:])
    return geodesic_face_count(_DEFAULT_DIMENSION)


def resolve_platonic_shape_metric(active_shape: str) -> int | None:
    """Face-count metric for the latched platonic tab: 4, 6, 8, 12, or 20; else None."""
    dim = str(active_shape or "").strip().upper()
    match dim:
        case "D4":
            return 4
        case "D6":
            return 6
        case "D8":
            return 8
        case "D12":
            return 12
        case "D20":
            return 20
        case _:
            return None


def format_platonic_geo_label(active_shape: str) -> str:
    """Nav label from latched shape — ``D4``, ``D6``, …, or empty when none latched."""
    metric = resolve_platonic_shape_metric(active_shape)
    return f"D{metric}" if metric is not None else ""


def format_platonic_preset_header_prefix(active_shape: str) -> str:
    """Presets 3×3 header prefix — ``D4 · `` or empty when no platonic tab latched."""
    label = format_platonic_geo_label(active_shape)
    return f"{label} · " if label else ""


_PLATONIC_SOLID_NAMES: dict[str, str] = {
    "D4": "Tetrahedron",
    "D6": "Cube",
    "D8": "Octahedron",
    "D12": "Dodecahedron",
    "D20": "Icosahedron",
}


def platonic_solid_name(shape: str) -> str:
    """Human-readable Platonic solid name for a latched D* tab."""
    dim = str(shape or "").strip().upper()
    return _PLATONIC_SOLID_NAMES.get(dim, "Geodesic solid")


def build_platonic_viewport_overlay_html(shape: str) -> str:
    """Bottom-left viewport caption — D* label + solid name + config description."""
    dim = str(shape or "").strip().upper()
    if dim not in _PLATONIC_SOLID_NAMES:
        return ""
    config = get_dimension_config(dim)
    title = f"{dim} · {platonic_solid_name(dim)}"
    desc = str(config.get("description", ""))
    return (
        f'<div class="myst-gravity-viewport-overlay-inner" role="status">'
        f'<div class="myst-gravity-viewport-overlay-title">{html.escape(title)}</div>'
        f'<div class="myst-gravity-viewport-overlay-sub">{html.escape(desc)}</div>'
        f"</div>"
    )


def get_dimension_config(dimension: str) -> dict[str, object]:
    """Per geodesic-face-count tab (D* = face count): slider defaults and mesh topology."""
    dim = str(dimension or _DEFAULT_DIMENSION).strip().upper()
    match dim:
        case "D4":
            return {
                "face_count": 4,
                "default_pressure": 0.35,
                "default_phi_scale": 0.98,
                "default_e_scale": 1.02,
                "default_pi_scale": 1.00,
                "default_kappa": KAPPA_DOC,
                "default_delta_z": 0.14,
                "default_alpha": 1.10,
                "default_beta": 1.0,
                "default_view_elev": 28.0,
                "default_view_azim": 38.0,
                "subdiv": 6,
                "deform_bias": "tetra_like",
                "description": "4-face geodesic · tetrahedral emphasis",
            }
        case "D8":
            return {
                "face_count": 8,
                "default_pressure": 0.28,
                "default_phi_scale": 1.01,
                "default_e_scale": 0.99,
                "default_pi_scale": 1.01,
                "default_kappa": KAPPA_DOC,
                "default_delta_z": 0.12,
                "default_alpha": 1.0,
                "default_beta": 1.10,
                "default_view_elev": 24.0,
                "default_view_azim": 52.0,
                "subdiv": 10,
                "deform_bias": "octa_like",
                "description": "8-face geodesic · octahedral emphasis",
            }
        case "D12":
            return {
                "face_count": 12,
                "default_pressure": 0.22,
                "default_phi_scale": 1.00,
                "default_e_scale": 1.01,
                "default_pi_scale": 0.99,
                "default_kappa": KAPPA_DOC,
                "default_delta_z": 0.11,
                "default_alpha": 0.95,
                "default_beta": 1.0,
                "default_view_elev": 26.0,
                "default_view_azim": 45.0,
                "subdiv": 10,
                "deform_bias": "dodeca_like",
                "description": "12-face geodesic · dodecahedral emphasis",
            }
        case "D20":
            return {
                "face_count": 20,
                "default_pressure": 0.18,
                "default_phi_scale": 0.99,
                "default_e_scale": 1.00,
                "default_pi_scale": 1.01,
                "default_kappa": KAPPA_DOC,
                "default_delta_z": 0.09,
                "default_alpha": 1.0,
                "default_beta": 0.92,
                "default_view_elev": 22.0,
                "default_view_azim": 58.0,
                "subdiv": 12,
                "deform_bias": "icosa_like",
                "description": "20-face geodesic · icosahedral emphasis · smooth mesh",
            }
        case "D6" | _:
            return {
                "face_count": 6,
                "default_pressure": 0.0,
                "default_phi_scale": 1.0,
                "default_e_scale": 1.0,
                "default_pi_scale": 1.0,
                "default_kappa": KAPPA_DOC,
                "default_delta_z": 0.1,
                "default_alpha": 1.0,
                "default_beta": 1.0,
                "default_view_elev": UNIT_CELL_VIEW_ELEV,
                "default_view_azim": UNIT_CELL_VIEW_AZIM,
                "subdiv": 8,
                "deform_bias": "cubic",
                "description": "6-face geodesic · cubic (default)",
            }


_PLATONIC_FACE_COUNTS: frozenset[int] = frozenset({4, 6, 8, 12, 20})
_DEFORM_BIAS_FACE_COUNT: dict[str, int] = {
    "tetra_like": 4,
    "cubic": 6,
    "octa_like": 8,
    "dodeca_like": 12,
    "icosa_like": 20,
}


def resolve_face_count(
    *,
    face_count: int | None = None,
    deform_bias: str | None = None,
) -> int:
    """Resolve geodesic face count from explicit count or deform_bias hint."""
    if face_count is not None and int(face_count) in _PLATONIC_FACE_COUNTS:
        return int(face_count)
    if deform_bias:
        return int(_DEFORM_BIAS_FACE_COUNT.get(str(deform_bias), 6))
    return 6


def dimension_config_to_dials(config: dict[str, object]) -> dict[str, float]:
    """Map dimension config keys to the gravity dial bundle."""
    return {
        "phi": float(config["default_phi_scale"]),
        "e": float(config["default_e_scale"]),
        "pi": float(config["default_pi_scale"]),
        "kappa": float(config.get("default_kappa", KAPPA_DOC)),
        "dz": float(config.get("default_delta_z", 0.1)),
        "alpha": float(config.get("default_alpha", 1.0)),
        "beta": float(config.get("default_beta", 1.0)),
        "pressure": float(config["default_pressure"]),
        "elev": float(config.get("default_view_elev", UNIT_CELL_VIEW_ELEV)),
        "azim": float(config.get("default_view_azim", UNIT_CELL_VIEW_AZIM)),
    }


BOOT_QUOTE_STRING = "TEST EVERYTHING, HOLD FAST WHAT IS GOOD AND KNOW YOUR GOD"

HF_SPACE_URL = "https://huggingface.co/spaces/kinaar111/mystery"
GITHUB_URL = "https://github.com/kinaar8340/mystery"
TOE_URL = "https://github.com/kinaar8340/toe"
_SPACE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SPACE_DIR.parent.parent
WALLPAPER_FILENAME = "bg1_mystery.png"
DEMO_A_STARTUP_REPO_FILENAME = "Home_A_startup_page.png"
DEMO_A_STARTUP_ASSET_FILENAME = "home_a_startup_page.png"


def resolve_demo_a_startup_image_source_path() -> str:
    """Filesystem path to Demo A landing PNG — bundled, repo root, or HF download."""
    candidates = (
        _SPACE_DIR / "assets" / DEMO_A_STARTUP_ASSET_FILENAME,
        _SPACE_DIR / DEMO_A_STARTUP_ASSET_FILENAME,
        _REPO_ROOT / DEMO_A_STARTUP_REPO_FILENAME,
    )
    for path in candidates:
        if path.is_file():
            return str(path)
    if is_hf_space():
        import tempfile

        import requests

        cache_path = Path(tempfile.gettempdir()) / "mystery_home_a_startup_page.png"
        if not cache_path.is_file() or cache_path.stat().st_size == 0:
            url = (
                "https://raw.githubusercontent.com/kinaar8340/mystery/main/"
                f"{DEMO_A_STARTUP_REPO_FILENAME}"
            )
            print(f"[startup] fetching Demo A image: {url}", flush=True)
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            cache_path.write_bytes(response.content)
        return str(cache_path)
    raise FileNotFoundError(
        "Demo A startup image not found — expected bundled asset or "
        f"{DEMO_A_STARTUP_REPO_FILENAME} at repo root"
    )


def startup_image_static_paths() -> list[Path]:
    """Directories Gradio may serve for the Demo A landing image."""
    paths: list[Path] = []
    for name in (DEMO_A_STARTUP_ASSET_FILENAME, DEMO_A_STARTUP_REPO_FILENAME):
        for base in (_SPACE_DIR / "assets", _SPACE_DIR, _REPO_ROOT):
            path = base / name
            if path.is_file():
                paths.append(path.parent)
    return list(dict.fromkeys(paths))


def resolve_wallpaper_url() -> str:
    """Prefer bundled/local bg1_mystery.png; fall back to GitHub raw after push."""
    for path in (_SPACE_DIR / WALLPAPER_FILENAME, _REPO_ROOT / WALLPAPER_FILENAME):
        if path.is_file():
            stamp = int(path.stat().st_mtime)
            # Gradio serves set_static_paths() assets via /gradio_api/file= (not /file=<abs path>).
            return f"/gradio_api/file={path.name}?v={stamp}"
    return f"{GITHUB_URL}/raw/main/{WALLPAPER_FILENAME}"


def wallpaper_static_paths() -> list[Path]:
    """Directories Gradio may serve for the wallpaper background image."""
    paths: list[Path] = []
    for path in (_SPACE_DIR / WALLPAPER_FILENAME, _REPO_ROOT / WALLPAPER_FILENAME):
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

_TOE_PDF_URL = (
    f"{TOE_URL}/blob/main/papers/Aaron%27s_TOE_Complete.pdf"
)


def build_readme_full_page_html() -> str:
    """Single-scroll README view — black background, white text, embedded figures."""
    fig_labels = (
        "φ-e-π triangle",
        "Residual κ sweep",
        "3-6-9 vortex clock",
        "Conduit angular histogram",
    )
    figure_blocks = "\n".join(
        f'<figure class="myst-readme-figure">'
        f'<img src="{html.escape(url)}" alt="{html.escape(label)}" loading="lazy" />'
        f'<figcaption>{html.escape(label)}</figcaption></figure>'
        for url, label in zip(FIGURE_URLS, fig_labels, strict=True)
    )
    return f"""<article class="myst-readme-fullpage" id="myst-readme-fullpage">
{build_stage6_results_html()}

<section class="myst-readme-exec myst-readme-card">
<h2 class="myst-readme-exec-title">Executive Summary</h2>
<p><strong>Mystery</strong> is an interactive probe asking whether the near-relation
<strong>φ² + e² ≈ π²</strong> (residual <em>R</em> ≈ +0.137) can emerge naturally inside
Aaron&rsquo;s gauged Hopf flux lattice with dual opposing flywheel dynamics. The deforming,
breathing 3D cube is a direct visual metaphor for unit-cell behavior in that lattice &mdash;
not decoration.</p>
<ul class="myst-readme-exec-list">
<li><strong>Start on Home</strong> &mdash; watch Demo&nbsp;A breathe; explore presets B&ndash;I.</li>
<li><strong>Presets</strong> &mdash; nine locked unit-cell shapes (max convex &rarr; rigid &rarr; max concave).</li>
<li><strong>Render</strong> &mdash; 3&times;3 grid of all presets at once.</li>
<li><strong>Shape</strong> &mdash; D4/D6/D8/D12/D20 geodesic face-count selector
(the <em>D</em> is the number of faces: 4, 6, 8, 12, or 20; D6 cube active by default).</li>
<li><strong>Depth</strong> &mdash; full derivations and scripts on
<a href="{html.escape(GITHUB_URL)}">github.com/kinaar8340/mystery</a>.</li>
</ul>
</section>

<section class="myst-readme-walkthrough myst-readme-card">
<h2>First-Time Walkthrough</h2>
<p class="myst-readme-lead">A 90-second path through the Space:</p>
<ol class="myst-readme-steps">
<li><strong>Home &rarr; Demo&nbsp;A</strong> &mdash; the cube breathes through the full deformation cycle
(rigid &rarr; max convex &rarr; rigid &rarr; max concave &rarr; back). This is dual-opposing flywheel
precession made visible.</li>
<li><strong>Try Demo&nbsp;B and Demo&nbsp;C</strong> &mdash; compare <em>MAX CONVEX</em> (expansive flux) with
<em>RIGID CUBE</em> (phase-locked, mass-like rest state).</li>
<li><strong>Open Presets</strong> &mdash; tap any slot in the 3&times;3 grid; use <em>Edit</em> to tune
κ, deformation pressure, and view angles live.</li>
<li><strong>Shape D6</strong> &mdash; default 6-face cube geodesic; try D4 (tetrahedron), D8
(octahedron), D12 (dodecahedron), or D20 (icosahedron).</li>
</ol>
<h3>Example Parameter Settings</h3>
<table class="myst-readme-table">
<thead><tr><th>Goal</th><th>κ</th><th>Pressure</th><th>Preset / Demo</th></tr></thead>
<tbody>
<tr><td>See the breathing loop</td><td>0.85</td><td>0.35</td><td>Home &rarr; Demo&nbsp;F</td></tr>
<tr><td>Max outward curvature</td><td>0.85</td><td>+0.65</td><td>Demo&nbsp;B (MAX CONVEX)</td></tr>
<tr><td>Stable rigid rest state</td><td>0.85</td><td>0.00</td><td>Demo&nbsp;C (RIGID CUBE)</td></tr>
<tr><td>Deep inward pinch</td><td>0.85</td><td>&minus;0.55</td><td>Demo&nbsp;I (MAX CONCAVE)</td></tr>
<tr><td>Stress-test residual null</td><td>0.8513 (κ*)</td><td>varies</td><td>Presets &rarr; Edit sliders</td></tr>
</tbody>
</table>
</section>

<hr class="myst-readme-divider" />

<header class="myst-readme-hero">
<p class="myst-readme-kicker">Mystery &mdash; φ, e, π Emergent Signature</p>
<h1>README &bull; Deep Context &amp; Model Foundation</h1>
</header>

<section class="myst-readme-section">
<h2>Project Purpose</h2>
<p>Mystery is an interactive research notebook and visualization probe. Its goal is to explore a
striking numerical near-harmony:</p>
<p class="myst-readme-formula">φ² + e² ≈ π²</p>
<p>and to test whether this relation can appear as a natural emergent signature inside a deeper
topological and dynamical framework &mdash; specifically Aaron&rsquo;s Theory of Everything based on
the gauged Hopf flux lattice with dual opposing flywheel dynamics.</p>
<p>This is not an attempt to prove an exact mathematical identity. It is an investigation into
whether the small residual and the near-30-60-90 geometry can arise organically from the structure
and dynamics of the underlying model. The 3D deforming cube, breathing animations, and parameter
controls are not mere eye-candy &mdash; they are direct visual metaphors for unit-cell behavior in
the gauged Hopf lattice.</p>
</section>

<hr class="myst-readme-divider" />

<section class="myst-readme-section">
<h2>The Prerequisite Model: Aaron&rsquo;s Theory of Everything</h2>
<p class="myst-readme-muted">Detailed in
<a href="{html.escape(_TOE_PDF_URL)}">Aaron&rsquo;s_TOE_Complete.pdf</a>
&mdash; <a href="{html.escape(TOE_URL)}">{html.escape(TOE_URL)}</a></p>
<p>At the foundation of this work lies a self-consistent topological model of reality called the
<strong>Gauged Hopf Flux Lattice</strong>.</p>

<h3>Core Structure</h3>
<p>The vacuum is modeled as a porous sponge &mdash; a discrete lattice whose fundamental building
blocks are gauged Hopf fibrations. In topological terms, this means circles (S¹) fibered over
spheres (S²) inside a higher-dimensional manifold (classically S³), with gauge fields attached. The
&ldquo;gauging&rdquo; allows the lattice to carry dynamic field strengths, phases, and fluxes that
can braid, twist, and stabilize.</p>

<h3>Dual Opposing Flywheel Dynamics</h3>
<p>The active degrees of freedom in this lattice are <strong>flux flywheels</strong> &mdash; coherent,
rotating or precessing configurations of topological flux that carry angular momentum. These flywheels
do not exist in isolation. The model emphasizes <strong>dual opposing configurations</strong>: pairs
(or larger coupled systems) of flywheels whose rotations or precessions are counter-directed. This
opposition creates:</p>
<ul>
<li>Mechanical and topological stability (analogous to gyroscopic stabilization)</li>
<li>Phase-locking and resonance conditions</li>
<li>Emergent conserved quantities (spin, charge, mass-like invariants)</li>
<li>Breathing / oscillatory modes when the system is excited</li>
</ul>
<p>Stable, locked configurations of these dual opposing flywheels correspond to the particles of the
Standard Model. Different locking patterns, twist rates, and braiding phases produce the different
elements of the periodic table as emergent, stable states within the lattice &ldquo;sponge.&rdquo;</p>

<h3>Key Supporting Concepts</h3>
<ul>
<li><strong>Observer Synchronization</strong> &mdash; Local observers can be phase-desynchronized from
the global lattice rhythm. This explains current experimental null results while predicting
distinctive non-local signatures once synchronization thresholds are crossed.</li>
<li><strong>Holonomy and Curvature</strong> &mdash; The lattice carries intrinsic holonomy. Small
mismatches (holonomy gaps) can be scaled and related to observable residuals.</li>
<li><strong>Gravity-like Effects</strong> &mdash; Lattice excitations and large-scale flux imbalances
produce gravitational signatures (explored in companion papers on GW bursts, echoes, etc.).</li>
<li><strong>Vortex-Math / 3-6-9 Geometry</strong> &mdash; Angular distributions and phase increments
in the lattice naturally map onto positional geometries reminiscent of vortex mathematics.</li>
</ul>
<p>In short, the gauged Hopf flux lattice with dual opposing flywheel dynamics provides a unified
geometric-dynamical substrate from which both matter and certain numerical harmonies can emerge.</p>
</section>

<hr class="myst-readme-divider" />

<section class="myst-readme-section">
<h2>How Mystery Connects to the TOE</h2>
<p>The Mystery app takes the above framework and asks a concrete question:</p>
<blockquote>Can the numerical relation φ² + e² ≈ π² appear as a natural scaling or harmonic
feature when we examine the geometry and dynamics of the lattice&rsquo;s unit cells?</blockquote>
<p>To make this explorable, the app represents lattice unit cells as deformable 3D cubes. These
cubes are not arbitrary &mdash; they stand in for localized regions of the Hopf flux lattice
supporting dual opposing flywheel activity.</p>

<h3>Preset Interpretations (Gravity Unit-Cell Presets)</h3>
<ul>
<li><strong>MAX CONVEX</strong> &mdash; expansive, high-curvature flux states</li>
<li><strong>RIGID CUBE</strong> &mdash; stable, phase-locked configurations (closest to &ldquo;rest&rdquo;
mass-like states)</li>
<li><strong>MAX CONCAVE / Bowl / Pinch</strong> &mdash; contracted or stressed flux regions, modeling
curvature or gravitational-like effects</li>
</ul>

<h3>Breathing Animation</h3>
<p>The rhythmic expansion/contraction of the cube visualizes the natural oscillatory modes that arise
from dual opposing flywheel precession and flux breathing. Parameters such as deformation range,
φ⁺ scale, e⁺ scale, and n² scaling directly modulate how strongly the golden-ratio and Euler-number
influences appear in the deformation field.</p>

<h3>Parameter Controls &amp; Live Probing</h3>
<p>You can adjust the relative weighting of φ, e, and other factors while watching how the unit-cell
geometry responds. This is a direct, visual way to probe whether the near-Pythagorean relation
emerges under specific dynamical regimes of the lattice.</p>

<h3>Analysis Layer (behind the visuals)</h3>
<p>The repository contains multiple quantitative probes:</p>
<ul>
<li>Residual calculation (<em>R</em> ≈ +0.1375)</li>
<li>Meta-optimization of scaling parameters (κ ≈ 0.85 is only 0.16% from the value that nulls the
residual via holonomy-gap scaling)</li>
<li>PDE relaxation simulations of lattice dynamics</li>
<li>Conduit angular histograms linking to 3-6-9 vortex geometry</li>
<li>Rodin-style Hopf fiber mapping</li>
</ul>
<p>Collectively these show that φ² + e² ≈ π² is a compatible emergent signature &mdash; not forced
by any invariant, yet consistently reachable within the model&rsquo;s natural parameter space.</p>
</section>

<hr class="myst-readme-divider" />

<section class="myst-readme-section">
<h2>Project Specifics &amp; Current Capabilities</h2>
<ul>
<li>Live 3D cube rendering with smooth browser-based performance</li>
<li>Preset catalog + fully manual parameter editing</li>
<li>Animated breathing deformations</li>
<li>Demo sequences and custom sequence builder</li>
<li>Clean dark theme with mathematical labels (δ<sub>z</sub> push, δ<sub>side</sub> inward, T<sub>n</sub> terms, etc.)</li>
<li>Reference grid and metric readouts</li>
<li>Figures tab with supporting plots and derivations</li>
<li>Full reproducibility via the GitHub repository (scripts, outputs, and sync tools)</li>
</ul>
<p>The app is deliberately focused. It is a probe, not a complete simulator. Its purpose is to make
the abstract concepts of the gauged Hopf lattice tangible and to invite deeper exploration of the
numerical harmony.</p>
</section>

<hr class="myst-readme-divider" />

<section class="myst-readme-section myst-readme-figures-section">
<h2>Supporting Figures</h2>
<p class="myst-readme-muted">Reference plots from the Mystery probe suite &mdash; regenerate locally
with <code>python run_all.py</code>.</p>
<div class="myst-readme-figure-grid">{figure_blocks}</div>
</section>

<hr class="myst-readme-divider" />

<section class="myst-readme-section">
<h2>Further Reading &amp; Next Steps</h2>
<ul>
<li>Full theoretical foundation:
<a href="{html.escape(_TOE_PDF_URL)}">Aaron&rsquo;s_TOE_Complete.pdf</a> and the entire
<a href="{html.escape(TOE_URL)}">toe</a> repository</li>
<li>Detailed analysis, scripts, and derivations:
<a href="{html.escape(GITHUB_URL)}">github.com/kinaar8340/mystery</a></li>
<li>Notes on angle derivation, emergent signatures, holonomy-gap scaling, and open questions are
available in the <code>notes/</code> folder of the mystery repo</li>
</ul>
</section>

<hr class="myst-readme-divider" />

<footer class="myst-readme-section myst-readme-footer">
<h2>Thank You for Exploring</h2>
<p>Mystery exists because the near-relation between φ, e, and π feels too elegant to be pure
coincidence, and because the gauged Hopf flux lattice with dual opposing flywheels offers a coherent
geometric home in which such harmonies can arise naturally.</p>
<p>Tweak the parameters. Watch the cube breathe. Ask what the deformations are telling you about the
underlying lattice.</p>
<p class="myst-readme-tagline"><em>Curiosity is the only prerequisite.</em></p>
<p class="myst-readme-signature">&mdash; Aaron</p>
</footer>
</article>"""


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


def steps_for_lambda_t(
    lambda_t_target: float = 2.0,
    kappa: float = KAPPA_DOC,
    dt: float = 0.001,
) -> int:
    """Discrete PDE steps for λt = lambda_t_target with λ ≈ κ."""
    return max(1, int(round(lambda_t_target / (kappa * dt))))


def quick_mean_survival_at_lambda_t(
    kappa: float = KAPPA_DOC,
    lambda_t: float = 2.0,
    dt: float = 0.001,
    seed: int = 42,
) -> float:
    """Lightweight PDE mean_survival at λt (for HF Space TUI / explorer)."""
    toe_rs = Path.home() / "Projects" / "toe" / "src" / "relaxation_survival.py"
    if toe_rs.is_file():
        try:
            import importlib.util
            import sys

            spec = importlib.util.spec_from_file_location("relaxation_survival", toe_rs)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                result = mod.simulate_twist_pde_survival(
                    normalize_to_lambda_t=lambda_t,
                    kappa=kappa,
                    dt=dt,
                    seed=seed,
                )
                return float(result["survival"]["mean_survival"])
        except Exception:
            pass

    rng = np.random.default_rng(seed)
    nx, nt = 20, steps_for_lambda_t(lambda_t, kappa, dt)
    theta = rng.uniform(0.1, 2.0, (nx, nx, nx))
    theta0_mean = float(theta.mean())
    theta_crit = PI * (1.0 + kappa)
    D, delta_omega = 0.05, 0.002
    for _ in range(nt):
        lap = (
            np.roll(theta, 1, 0) + np.roll(theta, -1, 0)
            + np.roll(theta, 1, 1) + np.roll(theta, -1, 1)
            + np.roll(theta, 1, 2) + np.roll(theta, -1, 2) - 6 * theta
        ) / (1.0 / nx) ** 2
        bar_theta = float(theta.mean())
        gauge = -kappa * bar_theta
        burst = np.where(theta > theta_crit, -50.0 * (theta - theta_crit), 0.0)
        theta += dt * (D * lap + delta_omega + gauge + burst)
        theta = np.clip(theta, 0.01, 2 * PI - 0.01)
    if abs(theta0_mean) < 1e-12:
        return 0.0
    return float(theta.mean() / theta0_mean)


def hybrid_analog_delta_pct(measured: float) -> tuple[float, float]:
    """60% golden + 40% e⁻² weighted Δ%. Returns (hybrid_delta_pct, hybrid_score)."""
    golden_d = 100.0 * abs(measured - GOLDEN_ANGLE_FRACTION) / GOLDEN_ANGLE_FRACTION
    e_d = 100.0 * abs(measured - E_INV2) / E_INV2
    hybrid_d = 0.6 * golden_d + 0.4 * e_d
    golden_c = 1.0 / (1.0 + abs(measured - GOLDEN_ANGLE_FRACTION))
    e_c = 1.0 / (1.0 + abs(measured - E_INV2))
    return hybrid_d, 0.6 * golden_c + 0.4 * e_c


def _append_golden_unit_circle_mpl(ax, *, radius: float = 1.15, n_ticks: int = 8) -> None:
    """Axial unit circle + golden-angle tick marks (rigid-cube + S¹ visualization)."""
    t = np.linspace(0.0, 2.0 * PI, 200)
    ax.plot(
        radius * np.cos(t),
        radius * np.sin(t),
        np.zeros_like(t),
        color=_UNIT_CELL_GOLD,
        linewidth=1.8,
        alpha=0.85,
        zorder=6,
    )
    for k in range(n_ticks):
        ang = (k * GOLDEN_ANGLE_RAD) % (2.0 * PI)
        ax.plot(
            [0.0, radius * np.cos(ang)],
            [0.0, radius * np.sin(ang)],
            [0.0, 0.0],
            color=_UNIT_CELL_GOLD,
            linewidth=1.2,
            alpha=0.65,
            zorder=6,
        )


def _append_golden_unit_circle_plotly(traces: list, *, radius: float = 1.15, n_ticks: int = 8) -> None:
    import plotly.graph_objects as go

    t = np.linspace(0.0, 2.0 * PI, 200)
    traces.append(
        go.Scatter3d(
            x=(radius * np.cos(t)).tolist(),
            y=(radius * np.sin(t)).tolist(),
            z=np.zeros_like(t).tolist(),
            mode="lines",
            line=dict(color=_UNIT_CELL_GOLD, width=5),
            name="S¹ unit circle",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    for k in range(n_ticks):
        ang = (k * GOLDEN_ANGLE_RAD) % (2.0 * PI)
        traces.append(
            go.Scatter3d(
                x=[0.0, radius * np.cos(ang)],
                y=[0.0, radius * np.sin(ang)],
                z=[0.0, 0.0],
                mode="lines",
                line=dict(color=_UNIT_CELL_GOLD, width=3),
                hoverinfo="skip",
                showlegend=False,
            )
        )


def format_residual_explorer(
    phi_sq_scale: float,
    e_sq_scale: float,
    pi_sq_scale: float,
    kappa: float,
    delta_z: float,
    alpha: float,
    beta: float,
    *,
    normalize_lambda_t: bool = True,
    golden_angle_steps: bool = False,
) -> str:
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    k_star = kappa_star_from_r(r_val)
    b_k = bound(kappa)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    rel_err = 100 * abs(r_val) / PI**2
    gap = b_k - r_val
    lines = [
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
    if normalize_lambda_t:
        mean_surv = quick_mean_survival_at_lambda_t(kappa=kappa, lambda_t=2.0)
        hybrid_d, hybrid_s = hybrid_analog_delta_pct(mean_surv)
        n_steps = steps_for_lambda_t(2.0, kappa)
        lines.extend([
            "",
            "=== λt = 2 survival (λ ≈ κ) ===",
            f"n_steps        : {n_steps}  (dt=0.001)",
            f"mean_survival  : {mean_surv:.6f}",
            f"e⁻² reference  : {E_INV2:.6f}",
            f"golden/1000    : {GOLDEN_ANGLE_FRACTION:.6f}",
            f"Δ% vs R        : {100 * abs(mean_surv - r_val) / abs(r_val):.3f}%",
            f"hybrid Δ%      : {hybrid_d:.3f}%  (60% golden + 40% e⁻²)",
            f"hybrid score   : {hybrid_s:.4f}",
        ])
    if golden_angle_steps:
        lines.extend([
            "",
            f"Golden steps   : ON ({GOLDEN_ANGLE_DEG:.2f}° / S¹ ticks)",
        ])
    if normalize_lambda_t and golden_angle_steps:
        mean_surv = quick_mean_survival_at_lambda_t(kappa=kappa, lambda_t=2.0)
        hybrid_d, hybrid_s = hybrid_analog_delta_pct(mean_surv)
        lines.extend([
            "",
            "=== Dual analog (golden + λt=2) ===",
            f"combined hybrid: {hybrid_s:.4f}  (Δ% {hybrid_d:.3f}%)",
            "Interpretation  : rotational packing + dissipative survival",
        ])
    if normalize_lambda_t or golden_angle_steps:
        lines.extend(["", stage6_results_explorer_footer()])
    return "\n".join(lines)


_UNIT_CELL_MATRIX_GREEN = "#33ff66"
_UNIT_CELL_GOLD = "#c9a227"
_UNIT_CELL_RED = "#e63946"
_UNIT_CELL_GREEN = "#22c55e"
_UNIT_CELL_BLUE = "#2563eb"
_UNIT_CELL_BOTTOM_CONVEX = "#5a9ef2"
_UNIT_CELL_LABEL_TEXT = "#ffffff"

# Matplotlib mathtext (detail render only).
_DETAIL_LABEL_T_PHI_MPL = r"$T_{\phi} \propto \phi^{2}$"
_DETAIL_LABEL_T_E_MPL = r"$T_{e} \propto e^{2}$"
_DETAIL_LABEL_T_PI_MPL = r"$T_{\pi} \propto \pi^{2}$"
_DETAIL_LABEL_DELTA_SIDE_MPL = r"$\delta_{\mathrm{side}}$ (inward)"
_DETAIL_LABEL_DELTA_Z_MPL = r"$\delta_{z}$ (push)"
_DETAIL_AXIS_PHI_MPL = r"$\phi$-face"
_DETAIL_AXIS_E_MPL = r"$e$-face"
_DETAIL_AXIS_PI_MPL = r"$\pi$-face"

# Plotly Scatter3d text (no LaTeX) — ISO-style Unicode for detail render only.
_DETAIL_LABEL_T_PHI_PLY = "T_φ ∝ φ²"
_DETAIL_LABEL_T_E_PLY = "T_e ∝ e²"
_DETAIL_LABEL_T_PI_PLY = "T_π ∝ π²"
_DETAIL_LABEL_DELTA_SIDE_PLY = "δ_side (inward)"
_DETAIL_LABEL_DELTA_Z_PLY = "δ_z (push)"
_DETAIL_AXIS_PHI_PLY = "φ-face"
_DETAIL_AXIS_E_PLY = "e-face"
_DETAIL_AXIS_PI_PLY = "π-face"


def _detail_exterior_label_positions(
    half: float = UNIT_CELL_DETAIL_AXIS_HALF,
) -> dict[str, tuple[float, float, float]]:
    """Place detail equation labels on the ±half grid faces, inset inside the axis cube.

    Plotly clips 3D text outside axis range, so labels must stay within [-half, half]
    even when sitting on the grid perimeter.
    """
    edge = float(half) - float(UNIT_CELL_DETAIL_LABEL_EDGE_INSET)
    return {
        "t_phi": (edge, 0.52, 0.28),
        "t_e": (0.52, edge, 0.28),
        "t_pi": (0.52, 0.28, edge),
        "delta_side": (-edge, -0.62, 0.38),
        "delta_z": (0.48, -2.72, edge),
    }


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


def _scale_platonic_vertices(
    vertices: list[tuple[float, float, float]],
    s: float,
) -> list[tuple[float, float, float]]:
    max_abs = max(abs(c) for vtx in vertices for c in vtx)
    if max_abs < 1e-12:
        return list(vertices)
    scale = float(s) / max_abs
    return [(vtx[0] * scale, vtx[1] * scale, vtx[2] * scale) for vtx in vertices]


def _polyhedron_dual(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    """Build the dual polyhedron (face centroids become vertices)."""
    vert_array = np.asarray(vertices, dtype=float)
    dual_vertices = [
        tuple(vert_array[list(face)].mean(axis=0)) for face in faces
    ]
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
            angle = float(
                np.arctan2(np.dot(delta, tangent_b), np.dot(delta, tangent_a))
            )
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


def _platonic_topology(
    face_count: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    """Unit-scale vertex list and face index loops for each geodesic face count."""
    count = resolve_face_count(face_count=face_count)
    if count == 4:
        vertices = [
            (1.0, 1.0, 1.0),
            (1.0, -1.0, -1.0),
            (-1.0, 1.0, -1.0),
            (-1.0, -1.0, 1.0),
        ]
        faces = ((0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2))
        return vertices, list(faces)
    if count == 8:
        vertices = [
            (1.0, 0.0, 0.0),
            (-1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, -1.0),
        ]
        faces = (
            (4, 2, 0),
            (4, 0, 3),
            (4, 3, 1),
            (4, 1, 2),
            (5, 0, 2),
            (5, 3, 0),
            (5, 1, 3),
            (5, 2, 1),
        )
        return vertices, list(faces)
    if count == 12:
        return _polyhedron_dual(*_icosahedron_topology())
    if count == 20:
        return _icosahedron_topology()
    # D6 cube — π top (+z), φ left (−x), e right (+x)
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
    faces = (
        (4, 5, 6, 7),
        (0, 3, 2, 1),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (0, 4, 7, 3),
        (1, 2, 6, 5),
    )
    return vertices, list(faces)


def _platonic_face_corners(
    face_count: int,
    s: float,
) -> list[tuple[tuple[float, float, float], ...]]:
    raw_vertices, faces = _platonic_topology(face_count)
    vertices = _scale_platonic_vertices(raw_vertices, s)
    return [tuple(vertices[idx] for idx in face) for face in faces]


def _cube_face_quads(s: float) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    """Cube-only quad corners (compat helper)."""
    return tuple(
        face for face in _platonic_face_corners(6, s) if len(face) == 4
    )


def _barycentric_point(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    i: int,
    j: int,
    n: int,
) -> tuple[float, float, float]:
    k = n - i - j
    u, v, w = i / n, j / n, k / n
    return (
        u * p0[0] + v * p1[0] + w * p2[0],
        u * p0[1] + v * p1[1] + w * p2[1],
        u * p0[2] + v * p1[2] + w * p2[2],
    )


def _subdivide_triangle(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    subdiv: int,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    n = max(1, int(subdiv))
    if n == 1:
        return [(p0, p1, p2)]
    tris: list[
        tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    ] = []
    for i in range(n):
        for j in range(n - i):
            if n - i - j <= 0:
                continue
            a = _barycentric_point(p0, p1, p2, i, j, n)
            b = _barycentric_point(p0, p1, p2, i + 1, j, n)
            c = _barycentric_point(p0, p1, p2, i, j + 1, n)
            tris.append((a, b, c))
            if j < n - i - 1:
                d = _barycentric_point(p0, p1, p2, i + 1, j + 1, n)
                tris.append((b, d, c))
    return tris


def _subdivide_quad(
    p00: tuple[float, float, float],
    p10: tuple[float, float, float],
    p11: tuple[float, float, float],
    p01: tuple[float, float, float],
    subdiv: int,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    n = max(1, int(subdiv))
    tris: list[
        tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    ] = []
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        for j in range(n):
            v0, v1 = j / n, (j + 1) / n
            a = _bilinear_face(p00, p10, p11, p01, u0, v0)
            b = _bilinear_face(p00, p10, p11, p01, u1, v0)
            c = _bilinear_face(p00, p10, p11, p01, u1, v1)
            d = _bilinear_face(p00, p10, p11, p01, u0, v1)
            tris.append((a, b, c))
            tris.append((a, c, d))
    return tris


def _pentagon_fan_triangles(
    corners: tuple[tuple[float, float, float], ...],
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    cx = sum(pt[0] for pt in corners) / len(corners)
    cy = sum(pt[1] for pt in corners) / len(corners)
    cz = sum(pt[2] for pt in corners) / len(corners)
    center = (cx, cy, cz)
    return [
        (center, corners[i], corners[(i + 1) % len(corners)])
        for i in range(len(corners))
    ]


def _subdivide_face_corners(
    corners: tuple[tuple[float, float, float], ...],
    subdiv: int,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    if len(corners) == 3:
        return _subdivide_triangle(corners[0], corners[1], corners[2], subdiv)
    if len(corners) == 4:
        return _subdivide_quad(corners[0], corners[1], corners[2], corners[3], subdiv)
    tris: list[
        tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    ] = []
    for fan_tri in _pentagon_fan_triangles(corners):
        tris.extend(_subdivide_triangle(*fan_tri, subdiv))
    return tris


_PLATONIC_MESH_CACHE: dict[tuple[int, int], list[
    tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
]] = {}


def _platonic_mesh_triangles(
    face_count: int,
    s: float,
    *,
    subdiv: int = 8,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    """Cached subdivided surface triangles for a geodesic Platonic solid."""
    count = resolve_face_count(face_count=face_count)
    subdiv = max(1, int(subdiv))
    key = (count, subdiv)
    if key not in _PLATONIC_MESH_CACHE:
        unit_tris: list[
            tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
        ] = []
        for corners in _platonic_face_corners(count, 1.0):
            unit_tris.extend(_subdivide_face_corners(corners, subdiv))
        _PLATONIC_MESH_CACHE[key] = unit_tris
    if abs(s - 1.0) < 1e-12:
        return _PLATONIC_MESH_CACHE[key]
    return [
        (
            (a[0] * s, a[1] * s, a[2] * s),
            (b[0] * s, b[1] * s, b[2] * s),
            (c[0] * s, c[1] * s, c[2] * s),
        )
        for a, b, c in _PLATONIC_MESH_CACHE[key]
    ]


def _cube_mesh_topology(
    s: float,
    *,
    subdiv: int = 8,
) -> list[tuple[tuple[float, float, float], ...]]:
    """Legacy quad-patch topology for the D6 cube."""
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
    return patches


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


_SOLID_MESH_LIGHT_DIR = np.array([0.32, 0.58, 0.75], dtype=float)
_SOLID_MESH_LIGHT_DIR /= float(np.linalg.norm(_SOLID_MESH_LIGHT_DIR))


def _triangle_unit_normal(tri: list[tuple[float, float, float]]) -> np.ndarray:
    a = np.array(tri[0], dtype=float)
    b = np.array(tri[1], dtype=float)
    c = np.array(tri[2], dtype=float)
    n = np.cross(b - a, c - a)
    norm = float(np.linalg.norm(n))
    if norm < 1e-9:
        return _SOLID_MESH_LIGHT_DIR.copy()
    return n / norm


def _shade_solid_mesh_rgba(
    rgba: tuple[float, float, float, float],
    normal: np.ndarray,
    *,
    min_shade: float = 0.34,
    max_shade: float = 1.0,
) -> tuple[float, float, float, float]:
    """Normal-based shading for shape_only solid mesh — depth without cluttering edges."""
    ndotl = float(np.clip(np.dot(normal, _SOLID_MESH_LIGHT_DIR), 0.0, 1.0))
    shade = min_shade + (max_shade - min_shade) * ndotl
    r, g, b, a = rgba
    lit_a = min(0.88, 0.42 + 0.46 * abs(a) + 0.12 * ndotl)
    return (float(r) * shade, float(g) * shade, float(b) * shade, lit_a)


def _deformed_platonic_surface(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    face_count: int = 6,
    subdiv: int = 8,
) -> tuple[list[list[tuple[float, float, float]]], list[tuple[float, float, float, float]]]:
    """Subdivided Platonic surface triangles and per-triangle RGBA colors."""
    triangles: list[list[tuple[float, float, float]]] = []
    colors: list[tuple[float, float, float, float]] = []
    for tri in _platonic_mesh_triangles(face_count, s, subdiv=subdiv):
        displaced: list[tuple[float, float, float]] = []
        mode_triplet: list[dict[str, float]] = []
        for x, y, z in tri:
            dx, dy, dz, modes = _displacement_components(
                x, y, z, s, pressure, delta_z, delta_side
            )
            displaced.append((x + dx, y + dy, z + dz))
            mode_triplet.append(modes)
        ma, mb, mc = mode_triplet
        triangles.append(list(displaced))
        colors.append(_triangle_mode_color((ma, mb, mc), pressure=pressure))
    return triangles, colors


def _deformed_cube_surface(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    face_count: int = 6,
    subdiv: int = 8,
) -> tuple[list[list[tuple[float, float, float]]], list[tuple[float, float, float, float]]]:
    """Compat alias — cube was the original D6 mesh."""
    return _deformed_platonic_surface(
        s,
        pressure,
        delta_z,
        delta_side,
        face_count=face_count,
        subdiv=subdiv,
    )


def _deformed_cube_triangles(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    face_count: int = 6,
    subdiv: int = 8,
) -> list[list[tuple[float, float, float]]]:
    """Subdivided surface triangles for a pressure-deformed geodesic."""
    triangles, _colors = _deformed_platonic_surface(
        s,
        pressure,
        delta_z,
        delta_side,
        face_count=face_count,
        subdiv=subdiv,
    )
    return triangles


def _triangle_curvature_grid(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    subdiv: int,
    grid_step: int,
) -> list[list[tuple[float, float, float]]]:
    n = max(1, int(subdiv))
    step = max(1, int(grid_step))
    polylines: list[list[tuple[float, float, float]]] = []
    for i in range(0, n + 1, step):
        line = [
            _displace_vertex(
                *_barycentric_point(p0, p1, p2, i, j, n),
                s,
                pressure,
                delta_z,
                delta_side,
            )
            for j in range(n - i + 1)
        ]
        polylines.append(line)
    for j in range(0, n + 1, step):
        line = [
            _displace_vertex(
                *_barycentric_point(p0, p1, p2, i, j, n),
                s,
                pressure,
                delta_z,
                delta_side,
            )
            for i in range(n - j + 1)
        ]
        polylines.append(line)
    return polylines


def _deformed_face_curvature_grid(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    face_count: int = 6,
    subdiv: int = 8,
    grid_step: int = 2,
) -> list[list[tuple[float, float, float]]]:
    """Iso-parameter lines on each geodesic face — bend visibly under pressure."""
    polylines: list[list[tuple[float, float, float]]] = []
    for corners in _platonic_face_corners(face_count, s):
        if len(corners) == 4:
            p00, p10, p11, p01 = corners
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
        elif len(corners) == 3:
            polylines.extend(
                _triangle_curvature_grid(
                    corners[0],
                    corners[1],
                    corners[2],
                    s,
                    pressure,
                    delta_z,
                    delta_side,
                    subdiv=subdiv,
                    grid_step=grid_step,
                )
            )
        else:
            for fan_tri in _pentagon_fan_triangles(corners):
                polylines.extend(
                    _triangle_curvature_grid(
                        fan_tri[0],
                        fan_tri[1],
                        fan_tri[2],
                        s,
                        pressure,
                        delta_z,
                        delta_side,
                        subdiv=subdiv,
                        grid_step=grid_step,
                    )
                )
    return polylines


def _platonic_edge_index_pairs(face_count: int) -> list[tuple[int, int]]:
    _vertices, faces = _platonic_topology(face_count)
    edges: set[tuple[int, int]] = set()
    for face in faces:
        for i in range(len(face)):
            a, b = face[i], face[(i + 1) % len(face)]
            edges.add(tuple(sorted((a, b))))
    return list(edges)


def _deformed_platonic_edge_polylines(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    face_count: int = 6,
    samples: int = 18,
) -> list[list[tuple[float, float, float]]]:
    raw_vertices, _faces = _platonic_topology(face_count)
    vertices = _scale_platonic_vertices(raw_vertices, s)
    polylines: list[list[tuple[float, float, float]]] = []
    for i0, i1 in _platonic_edge_index_pairs(face_count):
        p0, p1 = vertices[i0], vertices[i1]
        pts = []
        for t in np.linspace(0.0, 1.0, samples):
            raw = _lerp3(p0, p1, float(t))
            pts.append(_displace_vertex(*raw, s, pressure, delta_z, delta_side))
        polylines.append(pts)
    return polylines


def _deformed_cube_edge_polylines(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    face_count: int = 6,
    samples: int = 18,
) -> list[list[tuple[float, float, float]]]:
    return _deformed_platonic_edge_polylines(
        s,
        pressure,
        delta_z,
        delta_side,
        face_count=face_count,
        samples=samples,
    )


_CUBE_GEODESIC_FACE_COUNT = 6


def _wireframe_edge_samples(pressure: float) -> int:
    """Vertex-to-vertex edges need few samples when rigid; more when bowed."""
    if abs(_clamp_deform_pressure(pressure)) < 0.04:
        return 2
    return 12


def _wireframe_edge_color_hex(
    edge_index: int,
    total_edges: int,
    *,
    t_along: float = 0.5,
) -> str:
    """Gold → rainbow gradient keyed to polyhedron edge index."""
    span = (edge_index + float(t_along) * 0.35) / max(1.0, float(total_edges))
    hue = 0.11 + span * 0.78
    red, green, blue = colorsys.hsv_to_rgb(hue % 1.0, 0.92, 1.0)
    return f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"


def _platonic_wireframe_edge_polylines(
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    *,
    face_count: int,
) -> list[list[tuple[float, float, float]]]:
    """True polyhedron edges only — no face diagonals or mesh triangulation."""
    return _deformed_platonic_edge_polylines(
        s,
        pressure,
        delta_z,
        delta_side,
        face_count=face_count,
        samples=_wireframe_edge_samples(pressure),
    )


def _append_platonic_wireframe_plotly_traces(
    traces: list,
    *,
    s: float,
    pressure: float,
    delta_z: float,
    delta_side: float,
    face_count: int,
) -> None:
    """Rainbow gradient edge traces — true polyhedron edges for every geodesic."""
    import plotly.graph_objects as go

    polylines = _platonic_wireframe_edge_polylines(
        s,
        pressure,
        delta_z,
        delta_side,
        face_count=face_count,
    )
    total = len(polylines)
    for edge_idx, edge_pts in enumerate(polylines):
        if len(edge_pts) < 2:
            continue
        ex, ey, ez = zip(*edge_pts, strict=True)
        n_pts = len(edge_pts)
        point_colors = [
            _wireframe_edge_color_hex(
                edge_idx,
                total,
                t_along=(pt / max(1, n_pts - 1)),
            )
            for pt in range(n_pts)
        ]
        traces.append(
            go.Scatter3d(
                x=list(ex),
                y=list(ey),
                z=list(ez),
                mode="lines",
                line=dict(color=point_colors, width=5),
                hoverinfo="skip",
                showlegend=False,
            )
        )


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


def _hide_unit_cell_scene_axes(ax) -> None:
    """Hide matplotlib 3D axes, panes, ticks, and grid — shape-only Figures grid."""
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_zlabel("")
    ax.grid(False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor((0.0, 0.0, 0.0, 0.0))
        axis.pane.set_alpha(0.0)
        axis._axinfo["grid"].update({"linewidth": 0})
        axis.line.set_color((0.0, 0.0, 0.0, 0.0))
        axis.set_tick_params(
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labeltop=False,
            labelleft=False,
            labelright=False,
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


def startup_viewport_file_html(served_path: str) -> str:
    """Demo A landing PNG — full-width crisp img on opaque black panel."""
    src = str(served_path or "").strip()
    if not src.startswith("/gradio_api/file="):
        src = f"/gradio_api/file={src}"
    return (
        '<div class="myst-gravity-viewport-inner myst-gravity-startup-wrap">'
        f'<img src="{src}" alt="Mystery startup README" '
        'class="myst-gravity-startup-img myst-gravity-startup-image" '
        'loading="eager" decoding="sync" />'
        "</div>"
    )


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


def _ffmpeg_normalize_clip_to_mp4(
    src_path: str | os.PathLike[str],
    dst_path: str | os.PathLike[str],
    *,
    fps: int = 10,
) -> None:
    """Re-encode any clip (GIF/MP4) to browser-safe H.264 mp4."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src_path),
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-r",
            str(int(fps)),
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-movflags",
            "+faststart",
            str(dst_path),
        ],
        check=True,
        capture_output=True,
    )


def _encode_loop_video(rgb_frames: list[np.ndarray], *, fps: int = 12) -> str:
    """Write frames to H.264 mp4 (browser-playable); fall back to looping GIF."""
    if not rgb_frames:
        raise ValueError("no frames to encode")

    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="mystery-encode-") as tmp_dir:
        tmp = Path(tmp_dir)
        for idx, frame in enumerate(rgb_frames):
            Image.fromarray(_ensure_even_frame(frame)).save(
                tmp / f"frame_{idx:05d}.png",
                format="PNG",
            )
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as out_tmp:
            mp4_path = out_tmp.name
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(int(fps)),
                    "-i",
                    str(tmp / "frame_%05d.png"),
                    "-vf",
                    "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:v",
                    "libx264",
                    "-movflags",
                    "+faststart",
                    mp4_path,
                ],
                check=True,
                capture_output=True,
            )
            return mp4_path
        except subprocess.CalledProcessError:
            try:
                os.unlink(mp4_path)
            except OSError:
                pass

    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        gif_path = tmp.name
    pil_frames = [Image.fromarray(_ensure_even_frame(frame)) for frame in rgb_frames]
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
    shape_only: bool = False,
    solid_mesh: bool = False,
    figsize: tuple[float, float] | None = None,
    dpi: int = 150,
    subdiv: int = 8,
    face_count: int = 6,
    show_golden_circle: bool = False,
) -> plt.Figure:
    """Server-rendered deformable geodesic — bowing π-face, concave φ/e sides."""
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
    if shape_only:
        font_main = 12
        font_small = 11
        font_tick = 10
        font_axis = 12
    else:
        font_main = UNIT_CELL_DETAIL_LABEL_FONT_MAIN
        font_small = UNIT_CELL_DETAIL_LABEL_FONT_SMALL
        font_tick = UNIT_CELL_DETAIL_AXIS_TICK_FONT
        font_axis = UNIT_CELL_DETAIL_AXIS_TITLE_FONT
    caption_neutral = _UNIT_CELL_LABEL_TEXT

    frame_size = UNIT_CELL_FIGSIZE if figsize is None else figsize
    fig = plt.figure(figsize=frame_size, dpi=dpi, facecolor=bg)
    ax = fig.add_subplot(111, projection="3d", facecolor=bg)

    geodesic_faces = resolve_face_count(face_count=face_count)
    wireframe_only = not solid_mesh and geodesic_faces != _CUBE_GEODESIC_FACE_COUNT
    if wireframe_only:
        edge_polylines = _platonic_wireframe_edge_polylines(
            s,
            p,
            delta_z,
            side,
            face_count=geodesic_faces,
        )
        total_edges = len(edge_polylines)
        for edge_idx, edge_pts in enumerate(edge_polylines):
            xs, ys, zs = zip(*edge_pts, strict=True)
            ax.plot(
                xs,
                ys,
                zs,
                color=_wireframe_edge_color_hex(edge_idx, total_edges),
                linewidth=2.4,
                solid_capstyle="round",
                alpha=1.0,
                zorder=5,
            )
    else:
        triangles, tri_colors = _deformed_platonic_surface(
            s,
            p,
            delta_z,
            side,
            face_count=geodesic_faces,
            subdiv=subdiv,
        )
        if solid_mesh and shape_only:
            face_rgba = [
                _shade_solid_mesh_rgba(c, _triangle_unit_normal(tri))
                for tri, c in zip(triangles, tri_colors, strict=True)
            ]
        else:
            face_rgba = [to_rgba(c) for c in tri_colors]
        ax.add_collection3d(
            Poly3DCollection(
                triangles,
                facecolors=face_rgba,
                edgecolors=(0, 0, 0, 0),
                linewidths=0.0,
            )
        )
        if show_curvature_grid and p_abs > 0.02:
            grid_alpha = 0.25 + 0.55 * p_abs
            for grid_line in _deformed_face_curvature_grid(
                s,
                p,
                delta_z,
                side,
                face_count=geodesic_faces,
                subdiv=subdiv,
            ):
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
        edge_polylines = _platonic_wireframe_edge_polylines(
            s,
            p,
            delta_z,
            side,
            face_count=geodesic_faces,
        )
        total_edges = len(edge_polylines)
        for edge_idx, edge_pts in enumerate(edge_polylines):
            xs, ys, zs = zip(*edge_pts, strict=True)
            ax.plot(
                xs,
                ys,
                zs,
                color=_wireframe_edge_color_hex(edge_idx, total_edges),
                linewidth=2.4,
                solid_capstyle="round",
                alpha=1.0,
                zorder=5,
            )

    if not shape_only:
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
        label_pos = _detail_exterior_label_positions(float(max(2.0, axis_half)))
        _draw_leader_label(
            ax,
            phi_face,
            label_pos["t_phi"],
            _DETAIL_LABEL_T_PHI_MPL,
            eq_red,
            fontsize=font_main,
        )
        _draw_leader_label(
            ax,
            e_face,
            label_pos["t_e"],
            _DETAIL_LABEL_T_E_MPL,
            eq_green,
            fontsize=font_main,
        )
        _draw_leader_label(
            ax,
            pi_face,
            label_pos["t_pi"],
            _DETAIL_LABEL_T_PI_MPL,
            eq_blue,
            fontsize=font_main,
        )
        _draw_leader_label(
            ax,
            _anchor_point((-s, 0.0, 0.0), s, p, delta_z, side),
            label_pos["delta_side"],
            _DETAIL_LABEL_DELTA_SIDE_MPL,
            eq_green,
            fontsize=font_small,
        )
        _draw_leader_label(
            ax,
            pi_face,
            label_pos["delta_z"],
            _DETAIL_LABEL_DELTA_Z_MPL,
            eq_blue,
            fontsize=font_small,
        )

    if show_golden_circle:
        _append_golden_unit_circle_mpl(ax, radius=1.15)

    if shape_only:
        half = float(UNIT_CELL_SHAPE_ONLY_AXIS_HALF)
        frame_dist = float(UNIT_CELL_SHAPE_ONLY_VIEW_DIST)
    else:
        half = float(max(2.0, axis_half))
        frame_dist = float(view_dist)
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_zlim(-half, half)
    if shape_only:
        _hide_unit_cell_scene_axes(ax)
    else:
        ax.set_xlabel(_DETAIL_AXIS_PHI_MPL, color=caption_neutral, fontsize=font_axis, labelpad=4)
        ax.set_ylabel(_DETAIL_AXIS_E_MPL, color=caption_neutral, fontsize=font_axis, labelpad=4)
        ax.set_zlabel(_DETAIL_AXIS_PI_MPL, color=caption_neutral, fontsize=font_axis, labelpad=4)
        ax.tick_params(colors=caption_neutral, labelsize=font_tick)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.fill = False
            axis.pane.set_edgecolor("#333333")
        ax.grid(True, color="#505050")
    elev = float(np.clip(view_elev, 5.0, 85.0))
    azim = float(view_azim) % 360.0
    ax.view_init(elev=elev, azim=azim)
    ax.dist = float(max(8.0, frame_dist))
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


def _plotly_detail_axis(half: float, *, title: str) -> dict:
    return dict(
        range=[-half, half],
        title=dict(
            text=title,
            font=dict(color="#b0b0b0", size=UNIT_CELL_DETAIL_AXIS_TITLE_FONT),
        ),
        visible=True,
        showgrid=True,
        showline=True,
        zeroline=True,
        showticklabels=True,
        showbackground=True,
        gridcolor="#505050",
        linecolor="#b0b0b0",
        zerolinecolor="#505050",
        tickfont=dict(color="#b0b0b0", size=UNIT_CELL_DETAIL_AXIS_TICK_FONT),
        backgroundcolor="rgba(0,0,0,0)",
    )


def _plotly_leader_trace(
    anchor: tuple[float, float, float],
    label_pos: tuple[float, float, float],
    text: str,
    line_color: str,
    *,
    font_size: float = UNIT_CELL_DETAIL_LABEL_FONT_MAIN,
):
    import plotly.graph_objects as go

    return (
        go.Scatter3d(
            x=[anchor[0], label_pos[0]],
            y=[anchor[1], label_pos[1]],
            z=[anchor[2], label_pos[2]],
            mode="lines",
            line=dict(color=line_color, width=4),
            hoverinfo="skip",
            showlegend=False,
        ),
        go.Scatter3d(
            x=[label_pos[0]],
            y=[label_pos[1]],
            z=[label_pos[2]],
            mode="text",
            text=[text],
            textfont=dict(
                color=_UNIT_CELL_LABEL_TEXT,
                size=int(font_size),
                family="Arial, Helvetica, sans-serif",
            ),
            hoverinfo="skip",
            showlegend=False,
        ),
    )


def _append_plotly_detail_overlays(
    traces: list,
    *,
    s: float,
    p: float,
    delta_z: float,
    side: float,
) -> None:
    phi_face = _anchor_point((s, 0.0, 0.0), s, p, delta_z, side)
    e_face = _anchor_point((0.0, s, 0.0), s, p, delta_z, side)
    pi_face = _anchor_point((0.0, 0.0, s), s, p, delta_z, side)
    label_pos = _detail_exterior_label_positions()
    overlays = [
        _plotly_leader_trace(
            phi_face,
            label_pos["t_phi"],
            _DETAIL_LABEL_T_PHI_PLY,
            _UNIT_CELL_RED,
        ),
        _plotly_leader_trace(
            e_face,
            label_pos["t_e"],
            _DETAIL_LABEL_T_E_PLY,
            _UNIT_CELL_GREEN,
        ),
        _plotly_leader_trace(
            pi_face,
            label_pos["t_pi"],
            _DETAIL_LABEL_T_PI_PLY,
            _UNIT_CELL_BLUE,
        ),
        _plotly_leader_trace(
            _anchor_point((-s, 0.0, 0.0), s, p, delta_z, side),
            label_pos["delta_side"],
            _DETAIL_LABEL_DELTA_SIDE_PLY,
            _UNIT_CELL_GREEN,
            font_size=UNIT_CELL_DETAIL_LABEL_FONT_SMALL,
        ),
        _plotly_leader_trace(
            pi_face,
            label_pos["delta_z"],
            _DETAIL_LABEL_DELTA_Z_PLY,
            _UNIT_CELL_BLUE,
            font_size=UNIT_CELL_DETAIL_LABEL_FONT_SMALL,
        ),
    ]
    for line_trace, text_trace in overlays:
        traces.append(line_trace)
        traces.append(text_trace)


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
    detail_scene: bool = False,
    camera_radius: float | None = None,
    subdiv: int = 8,
    face_count: int = 6,
    show_golden_circle: bool = False,
):
    """Interactive Plotly geodesic mesh for Render preset detail view."""
    import plotly.graph_objects as go

    _ = r_val
    s = 1.0
    side = abs(delta_side)
    p = _clamp_deform_pressure(pressure)
    p_abs = abs(p)
    geodesic_faces = resolve_face_count(face_count=face_count)
    traces: list[go.Mesh3d | go.Scatter3d] = []
    wireframe_only = geodesic_faces != _CUBE_GEODESIC_FACE_COUNT

    if wireframe_only:
        _append_platonic_wireframe_plotly_traces(
            traces,
            s=s,
            pressure=p,
            delta_z=delta_z,
            delta_side=side,
            face_count=geodesic_faces,
        )
    else:
        triangles, tri_colors = _deformed_platonic_surface(
            s,
            p,
            delta_z,
            side,
            face_count=geodesic_faces,
            subdiv=subdiv,
        )

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

        traces.append(
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
        )

        if show_curvature_grid and p_abs > 0.02:
            grid_alpha = 0.25 + 0.55 * p_abs
            for grid_line in _deformed_face_curvature_grid(
                s,
                p,
                delta_z,
                side,
                face_count=geodesic_faces,
                subdiv=subdiv,
            ):
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

        _append_platonic_wireframe_plotly_traces(
            traces,
            s=s,
            pressure=p,
            delta_z=delta_z,
            delta_side=side,
            face_count=geodesic_faces,
        )

    if detail_scene:
        _append_plotly_detail_overlays(traces, s=s, p=p, delta_z=delta_z, side=side)

    half = float(max(2.0, axis_half))
    cam_radius = (
        float(UNIT_CELL_DETAIL_PLOTLY_RADIUS)
        if camera_radius is None and detail_scene
        else (2.35 if camera_radius is None else float(camera_radius))
    )
    if detail_scene:
        scene_axes = dict(
            xaxis=_plotly_detail_axis(half, title=_DETAIL_AXIS_PHI_PLY),
            yaxis=_plotly_detail_axis(half, title=_DETAIL_AXIS_E_PLY),
            zaxis=_plotly_detail_axis(half, title=_DETAIL_AXIS_PI_PLY),
            bgcolor="#000000",
            aspectmode="cube",
            camera=_plotly_camera_from_view(view_elev, view_azim, radius=cam_radius),
            dragmode="orbit",
        )
        layout_margin = dict(l=4, r=4, t=4, b=4, pad=0)
        layout_height = UNIT_CELL_DETAIL_PLOTLY_HEIGHT
    else:
        scene_axes = dict(
            xaxis=dict(
                range=[-half, half],
                visible=False,
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            yaxis=dict(
                range=[-half, half],
                visible=False,
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            zaxis=dict(
                range=[-half, half],
                visible=False,
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            bgcolor="#000000",
            aspectmode="cube",
            camera=_plotly_camera_from_view(view_elev, view_azim, radius=cam_radius),
            dragmode="orbit",
        )
        layout_margin = dict(l=0, r=0, t=0, b=0, pad=0)
        layout_height = None

    if show_golden_circle:
        _append_golden_unit_circle_plotly(traces)

    fig = go.Figure(data=traces)
    layout_kw: dict = dict(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=layout_margin,
        autosize=True,
        scene=scene_axes,
        showlegend=False,
        uirevision="mystery-unit-cell",
    )
    if layout_height is not None:
        layout_kw["height"] = int(layout_height)
    fig.update_layout(**layout_kw)
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
    detail_scene: bool = False,
    subdiv: int = 8,
    face_count: int = 6,
    show_golden_circle: bool = False,
    normalize_lambda_t: bool = True,
):
    """Return an interactive Plotly unit-cell figure for preset detail view."""
    _ = normalize_lambda_t  # survival shown in metrics text via run_residual_explorer
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    return build_unit_cell_plotly_figure(
        delta_z=delta_z,
        delta_side=abs(d_side) * 0.5,
        r_val=r_val,
        pressure=deform_pressure,
        view_elev=view_elev,
        view_azim=view_azim,
        axis_half=UNIT_CELL_DETAIL_AXIS_HALF if detail_scene else UNIT_CELL_AXIS_HALF,
        detail_scene=detail_scene,
        camera_radius=UNIT_CELL_DETAIL_PLOTLY_RADIUS if detail_scene else None,
        subdiv=subdiv,
        face_count=face_count,
        show_golden_circle=show_golden_circle,
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


def plotly_figure_to_gravity_viewport_html(fig, *, autoplay: bool = False) -> str:
    """Embed Plotly in Home viewport — HTML path works for animated frames (gr.Plot does not)."""
    import plotly.io as pio

    has_frames = bool(getattr(fig, "frames", None))
    should_autoplay = bool(autoplay and has_frames)
    div = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn",
        auto_play=should_autoplay,
        animation_opts={
            "frame": {"duration": 70, "redraw": True},
            "transition": {"duration": 0},
            "mode": "immediate",
        },
        config={
            "responsive": True,
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
        },
        div_id="myst-gravity-viewport-plotly",
    )
    loop_script = ""
    if should_autoplay:
        loop_script = """
<script>
(function() {
    function mystGravityBreathingLoop() {
        var plot = document.getElementById('myst-gravity-viewport-plotly');
        if (!plot || !window.Plotly) { setTimeout(mystGravityBreathingLoop, 300); return; }
        var n = (plot._transitionData && plot._transitionData.frames && plot._transitionData.frames.length) || 0;
        if (n < 2) { setTimeout(mystGravityBreathingLoop, 300); return; }
        var opts = {frame: {duration: 70, redraw: true}, transition: {duration: 0}, mode: 'immediate'};
        plot.on('plotly_animated', function() { Plotly.animate(plot, null, opts); });
    }
    setTimeout(mystGravityBreathingLoop, 900);
})();
</script>
"""
    return (
        '<div class="myst-gravity-viewport-plot-host">'
        f"{div}{loop_script}</div>"
    )


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
    view_dist: float | None = None,
    axis_half: float | None = None,
    figsize: tuple[float, float] | None = None,
    dpi: int | None = None,
    shape_only: bool = False,
    subdiv: int = 8,
    face_count: int = 6,
    show_golden_circle: bool = False,
    normalize_lambda_t: bool = True,
    golden_angle_steps: bool = False,
) -> tuple[str, str, plt.Figure]:
    """Return explorer metrics, viewport header HTML, and unit-cell figure."""
    r_val = residual_from_scales(phi_sq_scale, e_sq_scale, pi_sq_scale)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    metrics = format_residual_explorer(
        phi_sq_scale,
        e_sq_scale,
        pi_sq_scale,
        kappa,
        delta_z,
        alpha,
        beta,
        normalize_lambda_t=normalize_lambda_t,
        golden_angle_steps=golden_angle_steps,
    )
    p = _clamp_deform_pressure(deform_pressure)
    mode = _deform_pressure_hint(p)
    metrics = (
        f"{metrics}\n\n"
        f"Deformation pressure : {p * 100:.1f}%  ({mode})\n"
        f"View                 : elev {view_elev:.0f}° · azim {view_azim:.0f}°\n"
        f"Geodesic faces       : {resolve_face_count(face_count=face_count)}\n"
        f"Mesh subdiv          : {int(subdiv)}"
    )
    fig_kwargs: dict[str, float | bool] = {
        "view_elev": view_elev,
        "view_azim": view_azim,
        "shape_only": shape_only,
        "show_golden_circle": show_golden_circle or golden_angle_steps,
    }
    if view_dist is not None:
        fig_kwargs["view_dist"] = float(view_dist)
    if axis_half is not None:
        fig_kwargs["axis_half"] = float(axis_half)
    if figsize is not None:
        fig_kwargs["figsize"] = figsize
    if dpi is not None:
        fig_kwargs["dpi"] = int(dpi)
    fig = build_unit_cell_figure(
        delta_z=delta_z,
        delta_side=abs(d_side) * 0.5,
        r_val=r_val,
        pressure=p,
        subdiv=subdiv,
        face_count=face_count,
        **fig_kwargs,
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
        # Single Mesh3d trace per frame — mixed trace counts break Plotly.animate.
        mesh_trace = frame_fig.data[0]
        if first_data is None:
            first_data = [mesh_trace]
        frames.append(go.Frame(data=[mesh_trace], name=str(idx)))

    fig = go.Figure(data=first_data, frames=frames)
    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, t=8, b=0),
        height=650,
        autosize=True,
        scene=dict(
            xaxis=dict(
                range=[-half, half],
                visible=False,
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            yaxis=dict(
                range=[-half, half],
                visible=False,
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            zaxis=dict(
                range=[-half, half],
                visible=False,
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            bgcolor="#000000",
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


# Diagnostic: test_cube = stable-topology Mesh3d; unit_cell = full deformation path.
BREATHING_ANIMATION_MODE = os.environ.get("MYST_BREATHING_MODE", "test_cube")


def create_simple_breathing_test_animation():
    """Stable-topology Mesh3d cube — only vertex coords change (Plotly-safe animate)."""
    import plotly.graph_objects as go

    base_vertices = np.array(
        [
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1],
        ]
    )
    i = [0, 0, 0, 1, 1, 2, 2, 3, 4, 4, 5, 6]
    j = [1, 2, 3, 2, 3, 3, 0, 0, 5, 6, 6, 7]
    k = [2, 3, 0, 3, 0, 0, 1, 1, 6, 7, 4, 4]

    frames = []
    n_frames = 60
    for t in np.linspace(0, 2 * np.pi, n_frames):
        scale = 1 + 0.35 * np.sin(t)
        vertices = base_vertices * scale
        frames.append(
            go.Frame(
                data=[
                    go.Mesh3d(
                        x=vertices[:, 0],
                        y=vertices[:, 1],
                        z=vertices[:, 2],
                        i=i,
                        j=j,
                        k=k,
                        color="#5eb3ff",
                        opacity=1.0,
                        flatshading=True,
                        lighting=dict(
                            ambient=0.62,
                            diffuse=0.92,
                            specular=0.35,
                            roughness=0.45,
                        ),
                        lightposition=dict(x=3, y=4, z=2),
                        hoverinfo="skip",
                        showscale=False,
                    )
                ],
                name=str(t),
            )
        )

    half = 2.5
    fig = go.Figure(data=frames[0].data, frames=frames)
    fig.update_layout(
        height=620,
        autosize=True,
        margin=dict(l=0, r=0, t=36, b=0),
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#0a0a0f",
        showlegend=False,
        scene=dict(
            aspectmode="cube",
            bgcolor="#0a0a0f",
            xaxis=dict(
                visible=False,
                range=[-half, half],
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            yaxis=dict(
                visible=False,
                range=[-half, half],
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            zaxis=dict(
                visible=False,
                range=[-half, half],
                showgrid=False,
                showline=True,
                zeroline=False,
                showticklabels=True,
                showbackground=False,
            ),
            camera=_plotly_camera_from_view(UNIT_CELL_VIEW_ELEV, UNIT_CELL_VIEW_AZIM),
            dragmode="orbit",
        ),
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "y": 1.02,
                "x": 0.02,
                "buttons": [
                    {
                        "label": "▶ Breathing",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 70, "redraw": True},
                                "fromcurrent": False,
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    }
                ],
            }
        ],
    )
    print(
        f"[breathing] create_simple_breathing_test_animation: {len(frames)} frames",
        flush=True,
    )
    return fig


def create_breathing_animation(*, fresh: bool = False):
    """Viewport-ready Plotly breathing figure for Demo F."""
    import plotly.graph_objects as go

    if BREATHING_ANIMATION_MODE == "test_cube":
        fig = create_simple_breathing_test_animation()
        if fresh:
            fig = go.Figure(fig.to_dict())
        return fig

    fig = build_breathing_animation_figure()
    if not fig.frames:
        print("WARNING: No frames found in breathing animation!", flush=True)
    else:
        print(f"[breathing] create_breathing_animation: {len(fig.frames)} frames", flush=True)

    fig.update_layout(
        height=620,
        transition={"duration": 0},
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶ Breathing",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 80, "redraw": True},
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
    return fig


def render_breathing_demo_video(
    *,
    fps: int = 12,
    dpi: int = 88,
    n_per_segment: int = 12,
) -> str:
    """MP4 breathing cycle for Demo A — Gradio cannot animate Plotly frames reliably."""
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
    rgb_frames: list[np.ndarray] = []
    for pressure_val in pressures:
        fig = build_unit_cell_figure(
            delta_z=delta_z,
            delta_side=side,
            r_val=r_val,
            pressure=float(pressure_val),
            view_elev=view_elev,
            view_azim=view_azim,
            show_curvature_grid=False,
            shape_only=True,
            solid_mesh=True,
            face_count=6,
            dpi=dpi,
        )
        rgb_frames.append(_figure_to_rgb(fig, dpi=dpi))
        plt.close(fig)
    print(f"[breathing] render_breathing_demo_video: {len(rgb_frames)} frames", flush=True)
    return _encode_loop_video(rgb_frames, fps=fps)


def _video_render_profile(dimension: str) -> dict[str, int]:
    """Per-shape encode settings — lighter mesh for dense D12/D20 deformation loops."""
    dim = str(dimension or _DEFAULT_DIMENSION).strip().upper()
    config = get_dimension_config(dim)
    subdiv = int(config.get("subdiv", 8))
    match dim:
        case "D20":
            return {"fps": 9, "dpi": 68, "n_per_segment": 5, "subdiv": min(subdiv, 8)}
        case "D12":
            return {"fps": 10, "dpi": 72, "n_per_segment": 6, "subdiv": min(subdiv, 8)}
        case _:
            return {"fps": 10, "dpi": 80, "n_per_segment": 8, "subdiv": subdiv}


def render_platonic_deformation_demo_video(
    dimension: str,
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """MP4 platonic convex→rigid→concave loop — shape_only solid mesh (Figures preset sweep)."""
    dim = str(dimension or _DEFAULT_DIMENSION).strip().upper()
    profile = _video_render_profile(dim)
    fps = int(profile.get("fps", fps))
    dpi = int(profile.get("dpi", dpi))
    n_per_segment = int(profile.get("n_per_segment", n_per_segment))
    config = get_dimension_config(dim)
    face_count = int(config.get("face_count", geodesic_face_count(dim)))
    subdiv = int(profile.get("subdiv", config.get("subdiv", 8)))
    phi = 1.0
    e = 1.0
    pi = 1.0
    kappa = KAPPA_DOC
    delta_z = 0.1
    alpha = 1.0
    beta = 1.0
    view_elev = 26.0
    view_azim = 45.0
    r_val = residual_from_scales(phi, e, pi)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    side = abs(d_side) * 0.5
    pressures = _breathing_deformation_path(n_per_segment=n_per_segment)
    rgb_frames: list[np.ndarray] = []
    for pressure_val in pressures:
        fig = build_unit_cell_figure(
            delta_z=delta_z,
            delta_side=side,
            r_val=r_val,
            pressure=float(pressure_val),
            view_elev=view_elev,
            view_azim=view_azim,
            show_curvature_grid=False,
            shape_only=True,
            solid_mesh=True,
            dpi=dpi,
            face_count=face_count,
            subdiv=subdiv,
        )
        rgb_frames.append(_figure_to_rgb(fig, dpi=dpi))
        plt.close(fig)
    print(
        f"[demo-{dim.lower()}] render_platonic_deformation_demo_video: {len(rgb_frames)} frames",
        flush=True,
    )
    return _encode_loop_video(rgb_frames, fps=fps)


def render_demo_e_d4_deformation_video(
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """MP4 D4 tetrahedron convex→rigid→concave loop for Demo E."""
    return render_platonic_deformation_demo_video(
        "D4", fps=fps, dpi=dpi, n_per_segment=n_per_segment
    )


def render_demo_g_d8_deformation_video(
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """MP4 D8 octahedron convex→rigid→concave loop for Demo G."""
    return render_platonic_deformation_demo_video(
        "D8", fps=fps, dpi=dpi, n_per_segment=n_per_segment
    )


def render_demo_h_d12_deformation_video(
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """MP4 D12 dodecahedron convex→rigid→concave loop for Demo H."""
    return render_platonic_deformation_demo_video(
        "D12", fps=fps, dpi=dpi, n_per_segment=n_per_segment
    )


def _convex_preset_pressure_path(
    target: float,
    *,
    n_per_segment: int = 8,
) -> list[float]:
    """Rigid → preset convex → rigid loop for Demo C/D."""

    def _segment(start: float, end: float, n: int, *, skip_first: bool = False) -> list[float]:
        vals = np.linspace(float(start), float(end), max(2, int(n)), endpoint=True)
        if skip_first and len(vals) > 1:
            vals = vals[1:]
        return [_clamp_deform_pressure(float(v)) for v in vals]

    target = _clamp_deform_pressure(float(target))
    path: list[float] = []
    path += _segment(0.0, target, n_per_segment)
    path += _segment(target, 0.0, n_per_segment, skip_first=True)
    return path


def render_d6_convex_preset_demo_video(
    target_pressure: float,
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """D6 cube rigid↔preset convex loop — shape_only solid mesh for Demo C/D."""
    config = get_dimension_config("D6")
    face_count = int(config.get("face_count", 6))
    subdiv = int(config.get("subdiv", 8))
    phi = 1.0
    e = 1.0
    pi = 1.0
    kappa = KAPPA_DOC
    delta_z = 0.1
    alpha = 1.0
    beta = 1.0
    view_elev = 26.0
    view_azim = 45.0
    r_val = residual_from_scales(phi, e, pi)
    d_side = delta_side_contraction(delta_z, r_val, kappa, alpha=alpha, beta=beta)
    side = abs(d_side) * 0.5
    pressures = _convex_preset_pressure_path(
        target_pressure,
        n_per_segment=n_per_segment,
    )
    rgb_frames: list[np.ndarray] = []
    for pressure_val in pressures:
        fig = build_unit_cell_figure(
            delta_z=delta_z,
            delta_side=side,
            r_val=r_val,
            pressure=float(pressure_val),
            view_elev=view_elev,
            view_azim=view_azim,
            show_curvature_grid=False,
            shape_only=True,
            solid_mesh=True,
            dpi=dpi,
            face_count=face_count,
            subdiv=subdiv,
        )
        rgb_frames.append(_figure_to_rgb(fig, dpi=dpi))
        plt.close(fig)
    print(
        f"[demo-preset] render_d6_convex_preset_demo_video({target_pressure:.2f}): "
        f"{len(rgb_frames)} frames",
        flush=True,
    )
    return _encode_loop_video(rgb_frames, fps=fps)


def render_demo_c_d6_moderate_convex_video(
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """MP4 Preset 03 moderate convex loop for Demo C."""
    return render_d6_convex_preset_demo_video(
        0.50, fps=fps, dpi=dpi, n_per_segment=n_per_segment
    )


def render_demo_d_d6_mild_convex_video(
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """MP4 Preset 04 mild convex loop for Demo D."""
    return render_d6_convex_preset_demo_video(
        0.25, fps=fps, dpi=dpi, n_per_segment=n_per_segment
    )


def render_demo_i_d20_deformation_video(
    *,
    fps: int = 10,
    dpi: int = 80,
    n_per_segment: int = 8,
) -> str:
    """MP4 D20 icosahedron convex→rigid→concave loop for Demo I."""
    return render_platonic_deformation_demo_video(
        "D20", fps=fps, dpi=dpi, n_per_segment=n_per_segment
    )


_PIPELINE_DEMO_CLIP_CANDIDATES: tuple[tuple[str, ...], ...] = (
    ("demo_e_d4_tetrahedron.mp4",),
    ("demo_f_d6_breathing.mp4", "demo_a_breathing.gif"),
    ("demo_g_d8_octahedron.mp4",),
    ("demo_h_d12_dodecahedron.mp4",),
    ("demo_i_d20_icosahedron.mp4",),
)


def _resolve_pipeline_demo_clip_paths(
    *,
    assets_dir: str | os.PathLike[str] | None = None,
) -> list[str]:
    """Filesystem paths for E→F→G→H→I clips — bundled assets or fresh renders."""
    base = Path(assets_dir or Path(__file__).resolve().parent / "assets")
    clip_renderers: dict[str, object] = {
        "demo_e_d4_tetrahedron.mp4": lambda: render_demo_e_d4_deformation_video(
            n_per_segment=8, fps=10, dpi=80
        ),
        "demo_f_d6_breathing.mp4": lambda: render_breathing_demo_video(
            n_per_segment=8, fps=10, dpi=80
        ),
        "demo_a_breathing.gif": lambda: render_breathing_demo_video(
            n_per_segment=8, fps=10, dpi=80
        ),
        "demo_g_d8_octahedron.mp4": lambda: render_demo_g_d8_deformation_video(
            n_per_segment=8, fps=10, dpi=80
        ),
        "demo_h_d12_dodecahedron.mp4": lambda: render_demo_h_d12_deformation_video(
            n_per_segment=8, fps=10, dpi=80
        ),
        "demo_i_d20_icosahedron.mp4": lambda: render_demo_i_d20_deformation_video(
            n_per_segment=8, fps=10, dpi=80
        ),
    }
    paths: list[str] = []
    for candidates in _PIPELINE_DEMO_CLIP_CANDIDATES:
        chosen: Path | None = None
        for name in candidates:
            bundled = base / name
            if bundled.is_file():
                chosen = bundled
                break
        if chosen is None:
            renderer = clip_renderers.get(candidates[0])
            if renderer is None:
                raise FileNotFoundError(
                    f"no pipeline renderer for clip candidates: {candidates}"
                )
            paths.append(str(renderer()))
            continue
        paths.append(str(chosen.resolve()))
    return paths


def render_demo_b_pipeline_video(
    *,
    assets_dir: str | os.PathLike[str] | None = None,
    source_paths: list[str] | None = None,
) -> str:
    """Stitch Demo E→F→G→H→I clips into one browser-playable MP4 for Demo B."""
    sources = [
        Path(path)
        for path in (source_paths or _resolve_pipeline_demo_clip_paths(assets_dir=assets_dir))
    ]
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"pipeline stitch sources missing: {missing}")

    with tempfile.TemporaryDirectory(prefix="mystery-pipeline-") as tmp_dir:
        tmp = Path(tmp_dir)
        normalized: list[Path] = []
        for idx, src in enumerate(sources):
            seg_path = tmp / f"seg_{idx:02d}.mp4"
            _ffmpeg_normalize_clip_to_mp4(src, seg_path, fps=10)
            normalized.append(seg_path)
        list_path = tmp / "concat.txt"
        list_path.write_text(
            "".join(f"file '{path}'\n" for path in normalized),
            encoding="utf-8",
        )
        mp4_path = tmp / "pipeline.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(mp4_path),
            ],
            check=True,
            capture_output=True,
        )
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as out_tmp:
            out_path = out_tmp.name
        shutil.copy2(mp4_path, out_path)

    print(
        f"[demo-b] render_demo_b_pipeline_video: stitched {len(sources)} clips -> {out_path}",
        flush=True,
    )
    return out_path


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
    ("brackish_clock.py", "Gauged clock + brackish heartbeat"),
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


RESULTS_MD_URL = f"{GITHUB_URL}/blob/main/docs/RESULTS.md"

STAGE6_BEST = {
    "kappa": 0.89,
    "wg_base": 350.0,
    "W_g": 111.41,
    "braiding_target": 0.798,
    "w_s": 5.0,
    "golden_reward_weight": 0.3,
    "mean_survival": 0.137651,
    "delta_pct_vs_R": 0.121,
    "hybrid": 0.9990,
    "dual_analog_loss": 56.98,
    "golden_reward": 0.275,
}

STAGE6_TIMELINE = (
    {"run": "Pilot", "trials": 8, "w_s": 1, "loss": 63.64, "kappa": 0.77, "delta_pct_vs_R": 0.355, "hybrid": 0.9987, "note": "baseline"},
    {"run": "30-trial", "trials": 30, "w_s": 5, "loss": 56.98, "kappa": 0.89, "delta_pct_vs_R": 0.121, "hybrid": 0.9990, "note": "big improvement"},
    {"run": "50-trial", "trials": 50, "w_s": 5, "loss": 56.98, "kappa": 0.89, "delta_pct_vs_R": 0.121, "hybrid": 0.9990, "note": "identical to 30-trial"},
    {"run": "w_s sweep", "trials": 25, "w_s": "5–12", "loss": 56.98, "kappa": 0.89, "delta_pct_vs_R": 0.121, "hybrid": 0.9990, "note": "stable; w_s=5 best"},
    {"run": "Robustness", "trials": "—", "w_s": "—", "loss": "—", "kappa": 0.89, "delta_pct_vs_R": 0.121, "hybrid": 0.9990, "note": "18 grid points"},
)

STAGE6_MODES = {
    "baseline": {"loss": 57.22, "kappa": 0.89, "mean_survival": None, "delta_pct_vs_R": None, "hybrid": None, "golden_reward": None},
    "survival_penalty": {"loss": 57.26, "kappa": 0.89, "mean_survival": 0.137651, "delta_pct_vs_R": 0.121, "hybrid": 0.9990, "golden_reward": None},
    "dual_analog": {"loss": 56.98, "kappa": 0.89, "mean_survival": 0.137651, "delta_pct_vs_R": 0.121, "hybrid": 0.9990, "golden_reward": 0.275},
}

STAGE6_ROBUSTNESS = {
    "n_runs": 18,
    "kappa": 0.89,
    "W_g": 111.41,
    "best_delta_pct_vs_R": 0.121,
    "best_hybrid": 0.9990,
    "mean_survival_at_lambda_t2": 0.137651,
    "golden_packing": 0.78,
    "json": "analog_comparative_sweep_20260706_233723.json",
}


def stage6_results_explorer_footer() -> str:
    b = STAGE6_BEST
    return "\n".join([
        "=== Stage 6 — current best (50-trial confirmed) ===",
        f"κ              : {b['kappa']:.2f}  (pilot 0.77 → |κ−0.85| halved)",
        f"W_g            : {b['W_g']:.2f}  (wg_base {b['wg_base']:.0f})",
        f"mean_survival  : {b['mean_survival']:.6f}  (Δ% vs R {b['delta_pct_vs_R']:.3f}%)",
        f"hybrid score   : {b['hybrid']:.4f}",
        f"dual_analog    : loss {b['dual_analog_loss']:.2f}  golden_reward {b['golden_reward']:.3f}",
        f"Robustness     : {STAGE6_ROBUSTNESS['n_runs']} grid pts @ κ=0.89 — stable",
        f"Full docs      : {RESULTS_MD_URL}",
    ])


def _stage6_timeline_rows_html() -> str:
    rows = []
    for r in STAGE6_TIMELINE:
        loss = "—" if r["loss"] == "—" else f"{r['loss']:.2f}"
        if r["run"] in ("30-trial", "50-trial", "w_s sweep"):
            loss = f"<strong>{loss}</strong>"
        d_r = f"{r['delta_pct_vs_R']:.3f}%"
        hybrid = f"{r['hybrid']:.4f}"
        w_s = html.escape(str(r["w_s"]))
        rows.append(
            f"<tr><td>{html.escape(r['run'])}</td><td>{r['trials']}</td><td>{w_s}</td>"
            f"<td>{loss}</td><td>{r['kappa']:.2f}</td>"
            f"<td>{d_r}</td><td>{hybrid}</td><td>{html.escape(r['note'])}</td></tr>"
        )
    return "\n".join(rows)


def _stage6_modes_rows_html() -> str:
    rows = []
    for mode, data in STAGE6_MODES.items():
        ms = f"{data['mean_survival']:.6f}" if data["mean_survival"] is not None else "—"
        d_r = f"{data['delta_pct_vs_R']:.3f}%" if data["delta_pct_vs_R"] is not None else "—"
        hybrid = f"{data['hybrid']:.4f}" if data["hybrid"] is not None else "—"
        golden = f"{data['golden_reward']:.3f}" if data.get("golden_reward") else "—"
        loss = f"<strong>{data['loss']:.2f}</strong>" if mode == "dual_analog" else f"{data['loss']:.2f}"
        rows.append(
            f"<tr><td>{html.escape(mode)}</td><td>{loss}</td>"
            f"<td>{data['kappa']:.2f}</td><td>{ms}</td>"
            f"<td>{d_r}</td><td>{hybrid}</td><td>{golden}</td></tr>"
        )
    return "\n".join(rows)


def build_stage6_results_html(*, compact: bool = False) -> str:
    b = STAGE6_BEST
    rob = STAGE6_ROBUSTNESS
    link = html.escape(RESULTS_MD_URL)
    if compact:
        return (
            f'<div class="myst-stage6-card myst-stage6-compact">'
            f'<p class="myst-stage6-title">Stage 6 — Current Best Parameters</p>'
            f'<p class="myst-stage6-best">'
            f'κ <strong>{b["kappa"]:.2f}</strong> · W<sub>g</sub> <strong>{b["W_g"]:.2f}</strong> · '
            f'w<sub>s</sub> <strong>{b["w_s"]:.0f}</strong> · loss <strong>{b["dual_analog_loss"]:.2f}</strong>'
            f'</p>'
            f'<p>mean_survival <strong>{b["mean_survival"]:.6f}</strong> · '
            f'Δ% vs R <strong>{b["delta_pct_vs_R"]:.3f}%</strong> · '
            f'hybrid <strong>{b["hybrid"]:.4f}</strong></p>'
            f'<p class="myst-stage6-robust">'
            f'Robustness: <strong>{rob["n_runs"]}</strong> grid points @ κ=0.89 — '
            f'Δ% and hybrid stable across IC/twist/λt/step modes.'
            f'</p>'
            f'<p><a href="{link}" target="_blank" rel="noopener">Full RESULTS.md on GitHub →</a></p>'
            f"</div>"
        )
    timeline = _stage6_timeline_rows_html()
    modes = _stage6_modes_rows_html()
    return f"""<section class="myst-stage6-card" id="myst-stage6-results">
<h2>Stage 6 — Analog Objective (tuning complete)</h2>
<p class="myst-readme-muted">50-trial confirmed · w<sub>s</sub> = 5 · dual-analog objective</p>

<h3>Current best parameters</h3>
<table class="myst-readme-table myst-stage6-table">
<tbody>
<tr><td>κ</td><td><strong>{b['kappa']:.2f}</strong></td><td>W<sub>g</sub></td><td><strong>{b['W_g']:.2f}</strong></td></tr>
<tr><td>wg_base</td><td>{b['wg_base']:.0f}</td><td>φ_b target</td><td>{b['braiding_target']:.3f}</td></tr>
<tr><td>w<sub>s</sub></td><td>{b['w_s']:.0f}</td><td>golden_reward</td><td>{b['golden_reward']:.3f}</td></tr>
<tr><td>mean_survival</td><td>{b['mean_survival']:.6f}</td><td>Δ% vs R</td><td>{b['delta_pct_vs_R']:.3f}%</td></tr>
<tr><td>hybrid score</td><td>{b['hybrid']:.4f}</td><td>dual_analog loss</td><td><strong>{b['dual_analog_loss']:.2f}</strong></td></tr>
</tbody>
</table>

<h3>Tuning timeline</h3>
<table class="myst-readme-table myst-stage6-table">
<thead><tr>
<th>Run</th><th>Trials</th><th>w<sub>s</sub></th><th>Loss (dual)</th><th>κ</th>
<th>Δ% vs R</th><th>Hybrid</th><th>Notes</th>
</tr></thead>
<tbody>{timeline}</tbody>
</table>

<h3>50-trial mode comparison (w<sub>s</sub> = 5)</h3>
<table class="myst-readme-table myst-stage6-table">
<thead><tr>
<th>Mode</th><th>Loss</th><th>κ</th><th>mean_survival</th>
<th>Δ% vs R</th><th>Hybrid</th><th>Golden</th>
</tr></thead>
<tbody>{modes}</tbody>
</table>

<h3>Robustness @ κ = 0.89, W<sub>g</sub> = 111.41</h3>
<p>{rob['n_runs']} runs (3 IC × 2 λt + 3 twist × 2 λt × 2 step modes). Best Δ% vs R =
<strong>{rob['best_delta_pct_vs_R']:.3f}%</strong>, hybrid <strong>{rob['best_hybrid']:.4f}</strong>,
mean_survival @ λt=2 = <strong>{rob['mean_survival_at_lambda_t2']:.6f}</strong>
(golden+λt=2 packing ≈ {rob['golden_packing']:.2f}).</p>

<p class="myst-stage6-links">
<a href="{link}" target="_blank" rel="noopener">View full RESULTS.md on GitHub →</a>
</p>
</section>"""


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
            "",
            stage6_results_explorer_footer(),
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


