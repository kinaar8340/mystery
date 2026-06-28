# φ-e-π triangle angles — step-by-step derivation

This note gives an explicit, reproducible derivation of the Mystery triangle angles. It covers **geometry only** (law of cosines on side lengths φ, e, π). The step from “near 30°-60°-90°” to vortex 3-6-9 **interpretation** is thematic, not a theorem — see [synthesis.md](synthesis.md).

Implementation: `phi_e_pi_triangle()` in `space/mystery/demo_core.py` and `scripts/phi_e_pi_analysis.py`.

---

## Step 0 — Constants (exact definitions)

| Symbol | Definition | Decimal (float64) |
|--------|------------|-------------------|
| φ | (1 + √5) / 2 | 1.618033988749895 |
| e | exp(1) | 2.718281828459045 |
| π | arccos(−1) | 3.141592653589793 |

Squared lengths:

```
φ² = 2.618033988749895
e² = 7.389056098930649
π² = 9.869604401089358
```

Pythagorean residual (used later):

```
R = φ² + e² − π² = +0.137485686460186
Relative error vs π²: |R|/π² ≈ 1.39%
```

---

## Step 1 — Assign sides and check the triangle

Treat **φ, e, π as side lengths** (not angles). Ordering:

```
φ < e < π   →   shortest = φ, middle = e, longest = π
```

Triangle inequalities (all satisfied):

```
φ + e  > π   (4.336 > 3.142)
φ + π  > e   (4.760 > 2.718)
e + π  > φ   (5.860 > 1.618)
```

Label vertices so that side **opposite** angle A has length φ, side opposite B has length e, side opposite C has length π. Then C is the largest angle (opposite the longest side).

---

## Step 2 — Law of cosines

For a triangle with sides a, b, c and angle γ opposite side c:

```
c² = a² + b² − 2ab cos(γ)
⟹  cos(γ) = (a² + b² − c²) / (2ab)
⟹  γ° = arccos( clip(cos(γ), −1, 1) ) × 180/π
```

`clip` avoids rare float edge cases outside [−1, 1].

---

## Step 3 — Angle opposite φ (≈ 31.0°)

Adjacent sides: **e** and **π**. Opposite side: **φ**.

```
cos(A_φ) = (e² + π² − φ²) / (2eπ)
         = (7.389056099 + 9.869604401 − 2.618033989) / (2 × 2.718281828 × 3.141592654)
         = 14.640626511 / 17.079468385
         = 0.857269...

A_φ = arccos(0.857269) ≈ 30.996°
```

Rounded display: **31.0°**.

---

## Step 4 — Angle opposite e (≈ 59.9°)

Adjacent sides: **φ** and **π**. Opposite side: **e**.

```
cos(A_e) = (φ² + π² − e²) / (2φπ)
         = (2.618033989 + 9.869604401 − 7.389056099) / (2 × 1.618033989 × 3.141592654)
         = 5.098582291 / 10.166406676
         = 0.501508...

A_e = arccos(0.501508) ≈ 59.900°
```

Rounded display: **59.9°**.

---

## Step 5 — Angle opposite π (≈ 89.1°)

Adjacent sides: **φ** and **e**. Opposite side: **π**.

```
cos(A_π) = (φ² + e² − π²) / (2φe)
         = R / (2φe)
         = 0.137485686 / (2 × 1.618033989 × 2.718281828)
         = 0.137485686 / 8.794228409
         = 0.015634...

A_π = arccos(0.015634) ≈ 89.104°
```

Rounded display: **89.1°**.

Sanity check: **30.996 + 59.900 + 89.104 ≈ 180.000°**.

---

## Step 6 — Side ratios (normalized to φ)

```
φ : e : π  =  1 : e/φ : π/φ
           ≈  1 : 1.6795 : 1.9410
```

Exact 30°-60°-90° with shortest side 1:

```
1 : √3 : 2  ≈  1 : 1.7321 : 2.0000
```

Each Mystery ratio is ~3% below the corresponding 30-60-90 ratio — consistent with R > 0 (hypotenuse π is slightly “too short” for a perfect right triangle).

---

## Step 7 — 3-6-9 “tens” mapping (interpretive)

**Definition (probe convention):** divide each angle by 10°:

| Leg | Angle (°) | ÷ 10° | Nearest 3-6-9 axis |
|-----|-----------|-------|---------------------|
| φ | 30.996 | **3.10** | 3 |
| e | 59.900 | **5.99** | 6 |
| π | 89.104 | **8.91** | 9 |

Exact 30-60-90 would give **3.00 / 6.00 / 9.00**. Offsets: +0.10, −0.01, −0.09 (tens of degrees).

This is a **positional reading** aligned with vortex-math clock geometry — not a consequence of Step 2–5. No extra calculation beyond `angle ÷ 10` is required; the interpretive leap is choosing 10° as the unit and 3-6-9 as the target axes.

---

## What remains open (not derived here)

| Topic | Status |
|-------|--------|
| Why φ² + e² ≈ π² at all | Numerical near-miss; no closed identity |
| Holonomy bound B(κ) = π²(e/π − κ) | Algebraic fit; variational derivation in progress — [residual_scaling.md](residual_scaling.md) |
| 3-6-9 as physical control axes | Thematic link to Rodin / toroidal geometry — [synthesis.md](synthesis.md) |
| Conduit angular histogram peaks | Simulation probe; modest ~8%/6%/4% within 5° of 30/60/90 |

---

## Reproduce

```bash
cd mystery
.venv/bin/python scripts/phi_e_pi_analysis.py
# or import phi_e_pi_triangle from space/mystery/demo_core.py
```

Expected angles (4 decimal places): **30.9960° / 59.9000° / 89.1040°**.