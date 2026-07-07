# PDE Eigenstructure — Why κ_survival ≈ 0.891

July 2026. Closes the survival-minimum item in [`kappa_sim_interpretation.md`](kappa_sim_interpretation.md) §8 and [`open_questions.md`](open_questions.md). Complements the static Skyrme null [`skyrme_holonomy_derivation.md`](skyrme_holonomy_derivation.md) (κ\* ≈ 0.8513). Canonical summary: [`docs/RESULTS.md`](../docs/RESULTS.md).

**Status:** Proved at zero-mode order; cotangent + diffusion shift verified numerically. κ_sim ≈ 0.891 is a **dynamic spectral** optimum, not the algebraic B(κ) null.

---

## 1. PDE and normalization

The overdamped twist PDE ([`relaxation_survival.py`](../../toe/src/relaxation_survival.py), `pde_relaxation.py`) on \(T^3\) with periodic FD:

\[
\partial_t \theta = D\Delta\theta + \frac{D}{2}\cot\frac{\theta}{2}|\nabla\theta|^2 + \Delta\omega - \kappa\bar\theta - B(\theta),
\qquad \bar\theta = \langle\theta\rangle_{T^3}.
\]

**λt = 2 normalization** (memoryless exponential analog):

\[
\lambda \approx \kappa \;\text{(gauge torque)}, \qquad
T_{\mathrm{phys}} = \frac{2}{\kappa}, \qquad
n_{\mathrm{steps}} = \mathrm{round}\!\left(\frac{2}{\kappa\,\Delta t}\right).
\]

Measured survival:

\[
S(\kappa) = \frac{\bar\theta(T_{\mathrm{phys}})}{\bar\theta_0}.
\]

The κ-survival sweep minimizes \(|S(\kappa) - R|\) over \(\kappa \in [0.80, 0.90]\):

| κ | mean_survival @ λt=2 | Δ% vs R |
|---|----------------------|---------|
| κ_doc 0.850 | 0.137606 | 0.088% |
| κ\* 0.8513 | ≈ 0.1375 | ≈ 0.05% |
| **κ_sim 0.8909** (sweep best) | **0.137506** | **0.015%** |

(JSON: `outputs/kappa_survival_sweep_20260707_055706.json`)

---

## 2. Spectral decomposition on \(T^3\)

Split \(\theta(x,t) = \bar\theta(t) + \delta\theta(x,t)\) with \(\langle\delta\theta\rangle = 0\).

### 2.1 Laplacian eigenvalues (periodic FD, \(n_x = 20\))

For mode \(\mathbf{k} = (k_x, k_y, k_z)\), the stencil eigenvalue (matches `np.roll` laplacian in code) is

\[
\boxed{\;\Lambda_{\mathbf{k}} = \frac{4}{h^2}\sum_{d} \sin^2\!\frac{\pi k_d}{n_x}, \qquad h = \frac{1}{n_x}\;}
\]

Fluctuation decay rate: **\(D\Lambda_{\mathbf{k}}\)**.

| Mode \(\mathbf{k}\) | \(\Lambda_{\mathbf{k}}\) | \(D\Lambda_{\mathbf{k}}\) (\(D=0.05\)) |
|--------------------|--------------------------|----------------------------------------|
| (1,0,0) | ≈ 39.2 | ≈ 1.96 |
| (1,1,0) | ≈ 78.4 | ≈ 3.92 |
| (1,1,1) | ≈ 117.6 | ≈ 5.88 |

At \(T = 2/\kappa \approx 2.25\) s (κ ≈ 0.89), \(\exp(-2 D\Lambda_{(1,0,0)} T) \ll 1\) — gradient energy is damped before horizon end; cot coupling acts mainly in the **early** evolution.

### 2.2 Zero mode (gauge eigenvalue)

Volume average of the linearized PDE:

\[
\frac{d\bar\theta}{dt} = \Delta\omega - \kappa\bar\theta + \frac{D}{2}\,M(t),
\qquad
M(t) = \Big\langle \cot\frac{\theta}{2}\,|\nabla\theta|^2 \Big\rangle \;\ge\; 0.
\]

The gauge term contributes **only** to the \(\mathbf{k}=\mathbf{0}\) mode with decay rate **\(\kappa\)** — this is the eigenstructure identification \(\lambda_0 = \kappa\) used in `LambdaTNormalization`.

Diffusion and bursts do not source the mean at linear order (\(\langle\Delta\theta\rangle = 0\), bursts inactive below \(\theta_{\mathrm{crit}}\)).

---

## 3. Zero-mode survival at λt = 2

Drop cot and diffusion (pure gauge + drive):

\[
\frac{d\bar\theta}{dt} = \Delta\omega - \kappa\bar\theta.
\]

With \(\kappa T = 2\):

\[
\bar\theta(T) = \frac{\Delta\omega}{\kappa} + \Big(\bar\theta_0 - \frac{\Delta\omega}{\kappa}\Big)e^{-2}.
\]

Survival:

\[
\boxed{\;
S_0(\kappa) = \frac{\Delta\omega}{\kappa\bar\theta_0} + \Big(1 - \frac{\Delta\omega}{\kappa\bar\theta_0}\Big)e^{-2}\;}
\]

### 3.1 Algebraic null \(\kappa_0\)

Solve \(S_0(\kappa_0) = R\). With \(\alpha \equiv \Delta\omega/(\kappa\bar\theta_0)\):

\[
\alpha(1 - e^{-2}) + e^{-2} = R
\quad\Longrightarrow\quad
\boxed{\;\kappa_0 = \frac{\Delta\omega\,(1 - e^{-2})}{(R - e^{-2})\,\bar\theta_0}\;}
\]

**Seed 42 defaults** (\(\bar\theta_0 \approx 1.042\), \(\Delta\omega = 0.002\)):

| Quantity | Value |
|----------|-------|
| \(\kappa_0\) | **≈ 0.7717** |
| \(R\) | 0.137486 |
| \(e^{-2}\) | 0.135335 |

**Interpretation:** pure zero-mode dynamics would null \(S\) against \(R\) near **κ ≈ 0.77**, not κ_doc (0.85) or κ\* (0.8513). The static B(κ) null and the dynamic survival null are **different observables**.

Discrete Euler (\(\Delta t = 0.001\), \(n_{\mathrm{steps}} = \mathrm{round}(2/\kappa\Delta t)\)) shifts the zero-mode minimum to **κ ≈ 0.80** on the sweep grid — already **below** the full-PDE optimum.

---

## 4. Cotangent flux — why κ must rise

The Skyrme Jacobian term produces a **non-negative** mean source:

\[
\frac{D}{2}\,M(t) = \frac{D}{2}\,\Big\langle \cot\frac{\theta}{2}\,|\nabla\theta|^2 \Big\rangle \;\ge\; 0.
\]

At second order in fluctuations (\(\theta = \bar\theta + \delta\theta\)):

\[
M(t) \approx \cot\frac{\bar\theta}{2}\,\langle|\nabla\delta\theta|^2\rangle(t),
\qquad
\langle|\nabla\delta\theta|^2\rangle(t) \sim \sum_{\mathbf{k}\neq 0} |\hat\theta_{\mathbf{k}}|^2 \Lambda_{\mathbf{k}}\, e^{-2D\Lambda_{\mathbf{k}} t}.
\]

**Effect:** \(M(t) > 0\) pushes \(\bar\theta\) **up** relative to \(S_0(\kappa)\). For fixed κ, \(S(\kappa) > S_0(\kappa)\). To recover \(S(\kappa) \approx R\), the optimizer must use **larger κ** (stronger gauge damping).

Seed-42 initial cot flux: \(M_0 = \langle\frac{D}{2}\cot(\theta/2)|\nabla\theta|^2\rangle \approx 4.6\times 10^{-2}\).

### 4.1 Linear spectral surrogate (underestimates shift)

A fast linear model evolving \(\bar\theta\) with spectral decay of \(\langle|\nabla\delta\theta|^2\rangle\) finds its best match near **κ ≈ 0.80**, not 0.89 (`scripts/pde_survival_eigenstructure.py`). The remaining **Δκ ≈ +0.09** requires **nonlinear** cot on the co-evolving field:

- cot evaluated at **local** \(\theta(x)\), not only \(\bar\theta\);
- cot feeds back into **fluctuation** evolution, reshaping \(|\nabla\theta|^2\) beyond linear diffusion-only decay.

### 4.2 Diffusion is necessary

Ablation **\(D = 0\)** (cot only): \(S \approx 0.24\) — gradients do not dissipate; cot flux dominates unphysically. With **\(D = 0.05\)**, the optimum returns to **κ ≈ 0.89–0.91**. Diffusion supplies the fluctuation spectrum that cot couples to.

---

## 5. Why κ_sim ≈ 0.891 and not κ_doc / κ\*

| Constant | Role | Survival null? |
|----------|------|----------------|
| **κ\*** ≈ 0.8513 | Static \(B(\kappa) = R\) | Algebraic holonomy gap |
| **κ_doc** 0.85 | Design anchor (\(\theta_{\mathrm{crit}}\), docs) | 0.088% from R at λt=2 |
| **κ₀** ≈ 0.772 | Zero-mode \(S_0(\kappa) = R\) | Pure gauge eigenvalue |
| **κ_sim** ≈ 0.891 | Full PDE + λt=2 | **0.015%** from R (best) |

Hierarchy:

```
κ₀  <  κ*  ≈ κ_doc  <  κ_sim
0.77    0.8513  0.85     0.891
 |        |       |         |
zero   static   design   dynamic
mode   B-null   anchor   PDE+cot+diff
```

**κ_sim is not wrong relative to κ\*** — they optimize **different functionals**. κ\* nulls the static Skyrme bookkeeping \(B(\kappa)\); κ_sim nulls **simulated mean survival** after cotangent flux and diffusion reshape the zero mode.

The Stage 6 meta-optimizer lands near κ_sim because the survival penalty measures this **dynamic** \(S(\kappa)\), not \(B(\kappa)\) — see [`kappa_sim_interpretation.md`](kappa_sim_interpretation.md).

---

## 6. λt discretization ripple

κ enters survival **twice**:

1. **Decay rate** \(\kappa\) in \(-\kappa\bar\theta\).
2. **Horizon** \(n_{\mathrm{steps}}(\kappa) = \mathrm{round}(2/\kappa\Delta t)\) (Euler error, step-count resonance).

Example (\(\Delta t = 0.001\)):

| κ | \(n_{\mathrm{steps}}\) | \(T_{\mathrm{achieved}}\) |
|---|------------------------|---------------------------|
| 0.850 | 2353 | 2.353 |
| 0.891 | 2244 | 2.244 |
| 0.905 | 2209 | 2.209 |

This weakly modulates \(S(\kappa)\), **broadening** the Δ% vs R basin around 0.89–0.91 (not a sharp spike at κ_doc).

---

## 7. Synthesis

At λt = 2 the mean twist \(\bar\theta\) obeys a **drive-shifted zero mode** with eigenvalue \(\lambda_0 = \kappa\), plus a **positive cotangent flux** sourced by diffusing fluctuations on \(T^3\). The pure zero-mode null is **κ₀ ≈ 0.77**. Cotangent coupling and nonlinear spatial feedback raise \(S(\kappa)\) at fixed κ, moving the Δ% vs R minimum to **κ_sim ≈ 0.891** — consistent with κ-survival sweeps and Stage 6–7 production tuning.

This is the **dynamic** counterpart to the static κ\* null: same PDE, different projection (mean survival vs holonomy capacity).

---

## 8. Verification

```bash
cd mystery && .venv/bin/python scripts/pde_survival_eigenstructure.py
cd mystery && .venv/bin/python scripts/kappa_survival_sweep.py
```

Checks: \(\kappa_0\) formula, Laplacian spectrum, model hierarchy (zero-mode < spectral < full PDE), sweep best near 0.891.

---

## 9. Code correspondence

| Theory | Implementation |
|--------|----------------|
| \(\lambda_0 = \kappa\) | `LambdaTNormalization.characteristic_rate` |
| \(S_0(\kappa)\) at λt=2 | `zero_mode_survival_continuous()` in verifier |
| \(\Lambda_{\mathbf{k}}\) FD spectrum | `laplacian_eigenvalue()` in verifier |
| \(M(t)\) cot flux | `(D/2)*cot(θ/2)*|∇θ|²` mean in PDE loop |
| κ survival sweep | `scripts/kappa_survival_sweep.py` |

---

## 10. What remains beyond this proof

| Item | Status |
|------|--------|
| Closed-form κ_sim from fully coupled cot nonlinearity | Open (transcendental; numeric optimum ≈ 0.891) |
| Structured-IC robustness of κ_sim | Recommended (`pde_structured_ic_probe.py`) |
| Full nonlinear cot correction to \(B(\kappa)\) | Open (Skyrme note §10) |

---

## References

- [`kappa_sim_interpretation.md`](kappa_sim_interpretation.md) — κ_doc / κ\* / κ_sim roles (Q#9)
- [`skyrme_holonomy_derivation.md`](skyrme_holonomy_derivation.md) — static B(κ) null at κ\*
- [`residual_scaling.md`](residual_scaling.md) — φ-e-π scaling context
- `toe/src/relaxation_survival.py` — PDE + λt normalization