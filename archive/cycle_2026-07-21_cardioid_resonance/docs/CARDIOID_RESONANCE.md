# Cardioid Resonance — Geometric Probe Layer

**Status:** Mathematical + observational diagnostics. Interpretive language is optional and clearly marked.

This note frames the **cardioid × golden-angle** upgrade to the Mystery resonance laboratory. It does **not** claim that φ² + e² = π², nor that 350/π is a derived physical law. It adds measurable geometric structure on top of existing gauged Hopf lattice probes.

---

## 1. Layers (keep them separate)

| Layer | Content | Where |
|-------|---------|--------|
| **Mathematical** | Cardioid envelope \(r = 1 + \cos\theta\); golden-angle and \(9/\pi\) stepping; cusp curvature; packing metrics | `scripts/cardioid_golden_angle_probe.py`, this §2 |
| **Observational** | Cusp density, vortex 3-6-9 label fractions, burst-threshold κ sweeps, FFT before/after modulation, scale coherence near \(N \sim 350/\pi\) | probe JSON + `cusp_resonance_probe.py` |
| **Interpretive** (optional) | Cusp as model of frequency alignment / burst threshold; golden path as efficient “exit” through complexity; lived integration metaphors | §5 only — not used in score claims |

---

## 2. Mathematical layer

### 2.1 Golden-angle stepping

\[
\theta_k = (k \cdot \theta_\varphi) \bmod 2\pi, \qquad
\theta_\varphi = 2\pi\bigl(1 - \varphi^{-1}\bigr) \approx 137.508^\circ
\]

This is the classical phyllotaxis increment: irrational rotation that minimizes radial overlap and yields low gap coefficient of variation on \(S^1\). Already used in `golden_angle_twist_probe.py` and conduit `golden_angle_steps`.

**Optional comparator:** \(9/\pi\) rad ≈ 164.1° (vortex / mod-9 flavored step, not claimed optimal).

### 2.2 Cardioid modulation

\[
r_k = 1 + \cos\theta_k
\]

| Property | Value |
|----------|--------|
| Shape | Cardioid (heart-shaped polar curve) |
| Cusp | \(\theta = \pi\), \(r = 0\) |
| Far lobe | \(\theta = 0\), \(r = 2\) |
| Chord / curvature | Constant chord length property; **infinite curvature at the cusp** |

The cardioid is applied as a **resonance envelope** on existing angular dynamics — not a replacement for Hopf lattice PDE evolution.

### 2.3 Link to existing constants

| Quantity | Role in Mystery |
|----------|-----------------|
| \(R = \varphi^2 + e^2 - \pi^2 \approx 0.1375\) | Residual; alignment scores are *proximity diagnostics*, not proofs |
| \(\theta_\mathrm{crit} = \pi(1+\kappa)\) | Operational burst sink (PDE) |
| \(\Theta_\mathrm{link} \approx \pi\) | Hopf linking saturation (distinct from \(\theta_\mathrm{crit}\)) |
| \(W_g = 350/\pi \approx 111.408\) | Topological clock / accumulation scale candidate |
| Vortex 3-6-9 | Digital-root labels on step index; clock tens mapping |

The cusp at \(\theta=\pi\) sits at the same angular locus as **linking saturation** geometry, while **burst** remains the lifted threshold \(\pi(1+\kappa)\). See [`theta_crit_reconciliation.md`](theta_crit_reconciliation.md).

### 2.4 Metrics defined by the probes (explicit formulas)

Default cusp half-width \(w = 0.25\) rad. Circular distance:
\(\mathrm{dist}(\theta,\alpha)=\bigl|((\theta-\alpha+\pi)\bmod 2\pi)-\pi\bigr|\).

**Cusp density ratio** \(\rho\)

\[
f_\mathrm{cusp}=\frac{1}{N}\#\{k:\,\mathrm{dist}(\theta_k,\pi)\le w\},
\qquad
f_\mathrm{exp}=\frac{w}{\pi},
\qquad
\rho=\frac{f_\mathrm{cusp}}{f_\mathrm{exp}}.
\]

Equidistributed irrational rotation \(\Rightarrow\rho\approx 1\) (no angular pile-up).

**align_support** (φ-e-π alignment support)

Targets \(\alpha_\varphi,\alpha_e,\alpha_\pi\): law-of-cosines angles (rad) for sides \(\varphi,e,\pi\).
With Gaussian weights \(w_k=\exp\bigl(-\tfrac12(\mathrm{dist}(\theta_k,\alpha)/\sigma)^2\bigr)\), \(\sigma=0.20\):

\[
S(\alpha)=\frac{\sum_k w_k\,r_k}{\sum_k w_k}\Big/2,
\qquad
\mathrm{align\_support}=\frac{S(\alpha_\varphi)+S(\alpha_e)+S(\alpha_\pi)}{3}.
\]

Unit circle \(r\equiv 1\Rightarrow\mathrm{align\_support}=1/2\). Cardioid elevates \(S\) on the **body** (where \(r=1+\cos\theta>1\)); triangle angles are not at the cusp.

> **Separation:** `align_support` increase is driven by **cardioid-body weighting** at φ-e-π-relevant angles; `radial_collapse` and `burst_fraction` capture the **cusp singularity** itself. Do not read the align rise as angular pile-up into the cusp (\(\rho\) stays \(\approx 1\)).

> **Optimal focusing:** Geometric burst amplification peaks at **intermediate amplitude** \(A \approx 0.7\)–\(0.8\); higher \(A\) increases radial collapse dramatically but can reduce net burst gain due to over-collapse at the cusp (\(r\to 0\)). Documented operating point \(A=0.5\) is on the rising flank.

**radial_collapse**

\[
\mathrm{radial\_collapse}=\frac{\langle r\rangle_\mathrm{bulk}}{\langle r\rangle_\mathrm{cusp}}.
\]

**burst_fraction** (`cusp_resonance_probe`)

\[
a_k=1+A\cos\theta_k,\quad
\mathrm{holonomy}_k=(a_k\theta_k)\bmod 2\pi(1+\kappa),\quad
\theta_\mathrm{crit}=\pi(1+\kappa),
\]
\[
\mathrm{burst\_fraction}=\frac{1}{N}\#\{k:\,\mathrm{holonomy}_k>\theta_\mathrm{crit}\}.
\]

**cusp_coherence** (geometric scale sweep)

\[
\mathrm{cusp\_coherence}=\rho\cdot\frac{1}{1+\mathrm{gap\_cv}}\cdot\bigl(0.5+0.5\,\mathrm{frac}_{369}\bigr).
\]

**cusp_coherence** (dynamical / cusp_resonance scale sweep)

\[
\mathrm{sens}=(\mathrm{curvature\_ratio})\cdot(\mathrm{radial\_collapse}),
\quad
\mathrm{cusp\_coherence}=\mathrm{sens}\cdot(1+\mathrm{burst\_frac})\cdot\frac{1}{1+|\mathrm{align}-R|}.
\]

Polar curvature proxy: \(\kappa_\mathrm{curve}=|r^2+2(r')^2-r r''|/(r^2+(r')^2)^{3/2}\).

Also reported: vortex 3-6-9 label fractions in the cusp; FFT cusp power ratio (modulated / raw).

---

## 3. Observational layer

Reproduce:

```bash
cd mystery
.venv/bin/python scripts/cardioid_golden_angle_probe.py
.venv/bin/python scripts/cusp_resonance_probe.py
```

Outputs:

| Artifact | Description |
|----------|-------------|
| `outputs/cardioid_golden_angle_probe.png` | Side-by-side: unit golden vs cardioid-golden vs cardioid-9/π; metrics; scale sweep |
| `outputs/cardioid_three_way_star.png` | Star figure: three-way clouds + density + formula card |
| `outputs/cardioid_cusp_density.png` | Hexbin density + cusp zoom |
| `outputs/cusp_resonance_probe.png` | Envelope, burst mask, κ sweep, 350/π scale, FFT bars |
| `outputs/pde_cardioid_compare.png` | PDE baseline vs cardioid-modulated drive (optional flag) |
| `outputs/cardioid_golden_angle_probe_*.json` | Full metrics + `metric_formulas` |
| `outputs/cusp_resonance_probe_*.json` | Burst / FFT / scale metrics + formulas |

**What to look for (falsifiable):**

- Golden packing keeps **gap_cv** controlled (low-discrepancy stepping).
- Cardioid forces **radial collapse** at \(\theta\approx\pi\) (\(\mathrm{radial\_collapse}>1\)); first derivative \(r'\) vanishes at the cusp — sensitivity is curvature/collapse, not \(|r'|\).
- Irrational rotation keeps **angular** cusp density near-uniform (\(\rho\approx 1\)); the *interesting* signal is radial collapse + align_support + FFT, not angular pile-up.
- Scale sweep: peaks or plateaus of coherence near \(N \sim 350/\pi\) (or simple multiples) are **empirical** — confirm or reject with more \(N\).
- **Different observables peak at different multiples of \(350/\pi\):** geometric `cusp_coherence` often prefers \(N\approx 2\times 350/\pi\) (≈223), while dynamical `cusp_resonance` coherence peaks near \(N\approx 350/\pi\) (≈111). The accumulation scale interacts with the specific diagnostic (packing/labels vs burst/FFT/gradient).
- PDE compare: does envelope \(1+A\cos\theta\) on non-diffusive drive shift cusp-site fraction or residual-linked survival?

### Structured IC cardioid tests

Uniform IC is a **negative control** (fully dissipative; cardioid only amplifies damping). Positive tests use structured seeds (auto early-time `nt=400` unless `--nt` is set):

```bash
.venv/bin/python scripts/pde_relaxation_probe.py --compare-cardioid --ic hopfion
.venv/bin/python scripts/pde_relaxation_probe.py --compare-cardioid --ic helical
.venv/bin/python scripts/pde_relaxation_probe.py --compare-cardioid --ic helical --nt 50   # cusp still occupied
```

Logged: `cusp_frac`, field `align_support`, vortex 3-6-9 fractions (all + cusp window), σ, FFT. IC metrics recorded at t=0 in JSON (`ic_stats`).

| IC / window | Observation (A=0.5 vs baseline) |
|-------------|----------------------------------|
| uniform / long | Negative control: faster mean decay, σ→0 |
| helical / nt=50 | cusp_frac≈0.08 retained; σ↑; frac_369 **0.370→0.385** |
| helical / nt=400 | cusp emptied by damping; σ still ↑ (**0.055→0.071**); 369 **0.415→0.430** |
| hopfion / nt=400 | Mild σ retention; little cusp occupancy after relaxation |

**Takeaway:** Cardioid envelope is a modulator of existing structure, not a generator. Helical ICs show the clearest positive response (variance + mild 3-6-9 coherence). Cusp occupation under pure dissipation is **early-time** only.

---

## 4. Relation to the dynamical substrate

```
Golden-angle stepping  →  Fibonacci-optimal, non-overlapping S¹ paths
        +
Cardioid cusp          →  sharp high-sensitivity locus (r→0, infinite curvature)
        +
Hopf lattice PDE / κ   →  relaxation, burst sink θ_crit, survival @ λt=2
        +
φ-e-π residual R       →  numerical near-miss used as alignment ruler
```

This turns the repo from “a residual on a lattice” into a **resonance laboratory**: angular packing + directional envelope + threshold dynamics.

### 4.1 PDE cardioid coupling (implemented)

In `pde_relaxation_probe.py`:

\[
\partial_t\theta = D\nabla^2\theta + \underbrace{\bigl(1+A\cos\theta\bigr)}_{\text{envelope}}
\cdot(\text{cot term}+\delta\omega-\kappa\langle\theta\rangle+\text{burst}).
\]

```bash
.venv/bin/python scripts/pde_relaxation_probe.py --compare-cardioid
# or: CARDIOID_AMP=0.5 COMPARE_CARDIOID=1 ...
```

Diffusion stays unmodulated; only the non-diffusive drive is enveloped. Default suite run keeps \(A=0\) (baseline behaviour unchanged).

---

## 5. Interpretive layer (optional — not evidence)

*Marked speculation. Do not cite as results.*

- The cusp as a geometric cartoon of a **frequency-alignment** or **burst** gate: paths that approach the high-curvature zone experience a sharp change of radial scale.
- Golden-angle stepping as an **efficient exit** through angular complexity (minimal overlap, maximal coverage).
- \(350/\pi\) as a recurring **accumulation clock** already locked in \(W_g\); using it as \(N\)-scale is a rhyme with meta-optimizer / conduit conventions, not a proof of magic islands.

Lived or spiritual readings of the same diagrams are out of scope for probe scores and JSON fields.

---

## 6. Scripts & suite position

| Script | Priority | Role |
|--------|----------|------|
| `cardioid_golden_angle_probe.py` | P1 (quick win) | Envelope, plots, cusp stats, 350/π scale |
| `cusp_resonance_probe.py` | P2 | Burst κ sweep, FFT, gradient, scale |
| `cardioid_kappa_amp_sweep.py` | P2b | κ × A geometric + PDE helical early-time |
| `golden_angle_twist_probe.py` | existing | Conduit helix + S¹ histograms |
| `vortex_369_clock.py` | existing | 3-6-9 tens + Rodin cycle |
| `pde_relaxation_probe.py` | existing | Full lattice PDE + FFT + `--ic` / `--compare-cardioid` |

`run_all.py` includes the cardioid probes after the golden-angle twist probe.

HF-facing summary tables: [`docs/CARDIOID_RESONANCE_HF.md`](../docs/CARDIOID_RESONANCE_HF.md) (also rendered in Space README via `build_cardioid_resonance_html()`).

---

## 7. Core figure

After running the P1 probe, promote:

```text
docs/figures/cardioid_golden_angle_probe.png
docs/figures/cusp_resonance_probe.png
```

Use these as the visual anchor for “resonant geometric attractors and alignment thresholds” in README and the HF Space figures list.
