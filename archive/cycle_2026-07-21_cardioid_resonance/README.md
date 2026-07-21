# Cycle Archive: Cardioid Resonance Layer

**Date**: 2026-07-21  
**Status**: Ready for / deployed to HF Space (see `metadata/deployment.txt` for SHAs)

## Summary

This cycle added a full **resonance laboratory** layer on top of the existing gauged Hopf lattice work:

- Geometric probes using cardioid envelope on golden-angle stepping
- Quantifiable resonance metrics (explicit formulas)
- Dynamical coupling via PDE (optional cardioid envelope on non-diffusive drive)
- Structured initial-condition validation (uniform control, helical, hopfion)
- Comprehensive κ/A sweeps
- Optimal-amplitude note (burst peaks at A ≈ 0.7–0.8)

## Key Files

| Path | Contents |
|------|----------|
| `json_reports/` | All run outputs and metrics from 2026-07-21 |
| `figures/` | Polished visualization suite |
| `scripts/` | New and modified probe scripts (snapshot) |
| `docs/` | `CARDIOID_RESONANCE.md` + HF summary markdown |
| `metadata/deployment.txt` | SHAs, Space URL, reproduce commands |

## Main Outcomes

- Cardioid acts as a **modulator** of existing structure (strongest on helical ICs)
- Optimal burst amplification at **A ≈ 0.7–0.8** (over-collapse at A → 1)
- Helical seeds are the cleanest dynamical testbed; uniform IC is the negative control
- Cusp occupation is primarily early-time (~nt=50); longer-term benefit in σ and 369
- Full documentation and HF Space section completed

## Core Numbers (anchor)

| Metric | Value |
|--------|-------|
| Cusp pts (N=512, w=0.25) | 40, ρ ≈ 0.982 |
| align_support unit → cardioid | 0.50 → 0.72 |
| Burst raw → mod (A=0.5, κ_doc) | 0.074 → 0.199 |
| PDE helical Δσ / Δ369 (A=0.5, nt=50) | +0.013 / +0.015 |

## Deployment

See `metadata/deployment.txt` for current GitHub / HF SHAs and the Space URL:

https://huggingface.co/spaces/kinaar111/mystery

This archive preserves the state of the **July 21, 2026** Cardioid Resonance development cycle.
