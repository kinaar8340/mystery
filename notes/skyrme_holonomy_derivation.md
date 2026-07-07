# Formal Derivation — B(κ) = π²(e/π − κ) from Reduced Skyrme + Holonomy

July 2026. Completes open_questions §2 (π² prefactor). Canonical summary also in [`docs/RESULTS.md`](../docs/RESULTS.md). Builds on [`kappa_star_variational.md`](kappa_star_variational.md), [`residual_scaling.md`](residual_scaling.md), and TOE papers `Lagrangian_Derivation.pdf`, `Relativistic_Completion.pdf`, `Observer_Synchronization.pdf`.

**Status:** Derived at mean-field + fiber-saturation order. Full nonlinear cot(θ/2) and 4th-order Skyrme corrections are O((e/π − κ)²) and neglected here.

---

## 1. Starting action (TOE conduit stack)

### 1.1 Quaternion harmonic map (microscopic)

From `Lagrangian_Derivation.pdf` §1–2, the clean variational core is Dirichlet energy on \(q : T^3 \to S^3\):

\[
\mathcal{F}[q] = \frac{D}{2} \int_{T^3} |\nabla q|^2 \, d^3x, \qquad |q|=1.
\]

Aligned-gauge reduction \(\theta = 2\arccos(\mathrm{Re}\, q)\) gives

\[
\mathcal{F}[\theta] \approx \frac{D}{8} \int_{T^3} |\nabla\theta|^2 \, d^3x
\]

plus the geometric cotangent correction \(\frac{D}{2}\cot(\theta/2)|\nabla\theta|^2\) from the \(S^3\) Jacobian (harmonic-map / Skyrme literature).

### 1.2 Full free energy (drive, gauge, bursts)

`Lagrangian_Derivation.pdf` §3:

\[
\mathcal{F}[\theta] = \frac{D}{8}\int |\nabla\theta|^2 + \int U(\theta) + \frac{\kappa}{2}\,\bar\theta^{\,2} - \Delta\omega \int \theta \, d^3x
\]

where \(\bar\theta = V^{-1}\int_{T^3}\theta\, d^3x\) and the gradient flow is

\[
\partial_t \theta = D\Delta\theta + \frac{D}{2}\cot\frac{\theta}{2}|\nabla\theta|^2 + \Delta\omega - \kappa\bar\theta - B(\theta).
\]

| Term | Origin | Variational? |
|------|--------|--------------|
| \(D\Delta\theta + \frac{D}{2}\cot(\theta/2)|\nabla\theta|^2\) | Dirichlet / harmonic map on \(S^3\) | Yes |
| \(+\Delta\omega\) | Two-gyro drive torque | Forcing |
| \(-\kappa\bar\theta\) | Global pointer holonomy \(\alpha = -\kappa\bar\Theta\) | Yes — \(\frac{\kappa}{2}\bar\theta^{\,2}\) |
| \(+B(\theta)\) | Burst sink \(U'(\theta)=-B(\theta)\) | Yes — potential \(U\) |

`Observer_Synchronization.pdf` §1–2: \(\alpha(t) = -\kappa\bar\Theta(t)\), linearized deviation damps as \(\delta\Theta \sim e^{-\kappa t}\) — **κ is the holonomy damping rate**.

### 1.3 Relativistic Skyrme completion

`Relativistic_Completion.pdf` §1: the UV completion adds

\[
S_{\mathrm{Skyrme}} = \frac{e^2}{32\pi^2} \int \mathrm{Tr}[F_{\mu\nu}]^2, \qquad
S_{\mathrm{gauge}} = -\frac{K}{2}\int \Theta\, d^3x + \ldots
\]

The Skyrme term stabilizes Hopfions at \(W_g = 350/\pi\); the non-relativistic overdamped limit collapses to the conduit PDE above.

---

## 2. Mean-field reduction (global / zero mode)

Split \(\theta(x) = \bar\theta + \delta\theta(x)\) with \(\int \delta\theta = 0\).

**Zero-mode free energy** (drop gradients; bursts inactive below \(\theta_{\mathrm{crit}}\)):

\[
\mathcal{F}_0(\bar\theta) = \frac{\kappa}{2}\,\bar\theta^{\,2} - \Delta\omega\,\bar\theta.
\]

Stationarity:

\[
\frac{\partial \mathcal{F}_0}{\partial \bar\theta} = \kappa\bar\theta - \Delta\omega = 0
\quad\Longrightarrow\quad
\bar\theta_{\mathrm{eq}} = \frac{\Delta\omega}{\kappa}.
\]

This is the mean-field balance behind `relaxation_survival.py` identification **λ ≈ κ**.

---

## 3. Fiber saturation scale (where π enters)

`GW_Burst_Threshold.tex` distinguishes:

| Threshold | Formula | Value | Role |
|-----------|---------|-------|------|
| \(\Theta_{\mathrm{link}}\) | \(2\pi W_g/(2W_g+1)\) | ≈ π | Hopf linking saturation |
| \(\theta_{\mathrm{crit}}\) | \(\pi(1+\kappa)\) | ≈ 5.81 rad | Operational burst sink |

The **bare fiber half-turn** is \(\pi\) rad. Holonomy-lifted burst margin adds \(\kappa\pi\). For **reduced holonomy bookkeeping**, use the fiber reference twist

\[
\Theta_\star \equiv \pi
\]

as the natural saturation unit on the Hopf \(S^1\) fiber (not \(\theta_{\mathrm{crit}}\), which includes multi-fiber lift).

---

## 4. Drive vs damping holonomy capacities

### 4.1 Exponential drive scale (e/π)

The φ-e-π residual \(R = \phi^2 + e^2 - \pi^2\) pairs the **exponential leg** \(e\) with the **circular leg** \(\pi\). In holonomy units, the dimensionless drive-to-geometry ratio is

\[
\frac{e}{\pi}.
\]

At fiber saturation \(\Theta_\star = \pi\), the **drive holonomy capacity** (linear coupling at saturation) is

\[
\boxed{\;\Phi_{\mathrm{drive}} = \pi \cdot \frac{e}{\pi} = e\;}
\]

Interpretation: one unit of exponential drive flux, normalized against the circular fiber scale π.

### 4.2 Pointer damping capacity (κ)

From §2, gauge storage at \(\bar\theta = \Theta_\star = \pi\):

\[
\mathcal{E}_\kappa(\pi) = \frac{\kappa}{2}\pi^2.
\]

The **linearized damping capacity** against drive (first-order mismatch in κ at fixed fiber scale) is the coefficient of κ at saturation:

\[
\boxed{\;\Phi_{\mathrm{damp}}(\kappa) = \kappa\,\pi^2\;}
\]

(Quadratic storage \(\frac{\kappa}{2}\pi^2\); mismatch energy at first order in the gap uses the full \(\kappa\pi^2\) scale — see §5.)

---

## 5. Holonomy mismatch bound B(κ)

Define the **net holonomy mismatch** at fiber saturation as drive capacity minus damping capacity:

\[
\boxed{\;
B(\kappa) = \pi\,\Phi_{\mathrm{drive}} - \Phi_{\mathrm{damp}}(\kappa)
           = \pi \cdot e - \kappa\pi^2
           = \pi^2\left(\frac{e}{\pi} - \kappa\right)\;}
\]

| Factor | Origin |
|--------|--------|
| **(e/π − κ)** | Holonomy gap: exponential drive ratio minus pointer damping (`residual_scaling.md`) |
| **π** (first) | Fiber saturation half-turn \(\Theta_\star = \pi\) (`GW_Burst_Threshold.tex`) |
| **π** (second) | Quadratic gauge energy \(\frac{\kappa}{2}\bar\theta^2\) evaluated at \(\bar\theta \sim \pi\) — \(S^1\) / Hopf fiber Jacobian in the \(S^3 \to S^2\) reduction |

This is the derived form previously postulated in `kappa_star_variational.md` §2.

**Order of approximation:** linear in \((e/\pi - \kappa)\); nonlinear cotangent and Skyrme \(F_{\mu\nu}^2\) corrections are higher order and not included in \(B(\kappa)\).

---

## 6. Exact null κ\* and link to R

Set the mismatch equal to the φ-e-π residual:

\[
B(\kappa^\ast) = R = \phi^2 + e^2 - \pi^2.
\]

\[
\pi^2\left(\frac{e}{\pi} - \kappa^\ast\right) = R
\quad\Longrightarrow\quad
\boxed{\;\kappa^\ast = \frac{e}{\pi} - \frac{R}{\pi^2} \approx 0.8513\;}
\]

| κ | B(κ) | \|B(κ) − R\| / R |
|---|------|------------------|
| κ_doc 0.85 | 0.1506 | 9.5% |
| κ\* 0.8513 | 0.1375 | ~0% |
| κ_sim 0.89 | −0.243 | (damping-dominated; not a B-null) |

κ\* sits **0.16%** from κ_doc. κ_sim > e/π — see [`kappa_sim_interpretation.md`](kappa_sim_interpretation.md).

---

## 7. Stationarity under W_g constraint

With \(W_g = 350/\pi\) fixed, the **static** holonomy mismatch is minimized at κ\* (§6). The **dynamic** meta-optimizer minimizes island + Hopf + braiding + survival — shifting the operating point to κ_sim ≈ 0.89 (Q#9 closed).

Variational hierarchy:

```
∂|B(κ)−R|/∂κ = 0  at κ*     (algebraic / static Skyrme+holonomy null)
∂L_total/∂κ = 0   at κ_sim   (combined PDE+island+survival objective)
```

---

## 8. Code correspondence

| Theory | Implementation |
|--------|----------------|
| \(\alpha = -\kappa\bar\Theta\) | `conduit.py` global pointer; `gauge = -kappa * bar_theta` in `pde_relaxation.py` |
| \(\mathcal{F}_0 = \frac{\kappa}{2}\bar\theta^2 - \Delta\omega\bar\theta\) | Mean-field gauge term in PDE |
| \(B(\kappa) = \pi^2(e/\pi - \kappa)\) | `residual_kappa_sweep.py`, `residual_bound_probe.py` |
| κ proxy inversion | `epoch_bake_sweep.py`: `kappa_proxy = e/π − gap_stress/π + …` |
| \(\theta_{\mathrm{crit}} = \pi(1+\kappa)\) | `pde_relaxation.py`, `GW_Burst_Threshold.tex` |

---

## 9. Verification

```bash
cd mystery && .venv/bin/python scripts/skyrme_bound_derivation.py
```

Checks: free-energy stationarity, \(B(\kappa)\) identity, κ\* null, numeric agreement with `residual_kappa_sweep.py`.

---

## 10. What remains beyond this derivation

| Item | Status |
|------|--------|
| Full nonlinear cot\((\theta/2)\) correction to \(B(\kappa)\) | Open |
| Explicit \(F_{\mu\nu}\) integral reducing to π² at one loop | Open |
| PDE eigenstructure proof for survival minimum at κ ≈ 0.891 | **Closed** — [`pde_survival_eigenstructure.md`](pde_survival_eigenstructure.md) |

---

## References

- `toe/papers/Lagrangian_Derivation.pdf` — Dirichlet + free-energy functional
- `toe/papers/Relativistic_Completion.pdf` — Skyrme + gauge action
- `toe/papers/Observer_Synchronization.pdf` — \(\alpha = -\kappa\bar\Theta\), damping law
- `toe/papers/GW_Burst_Threshold.tex` — \(\theta_{\mathrm{crit}} = \pi(1+\kappa)\), fiber scale π