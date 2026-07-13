# Local Reference Index

Paths relative to `~/Projects/` when working locally. After cloning [mystery](https://github.com/kinaar8340/mystery), place sibling repos under the same parent directory (e.g. `~/Projects/toe`, `~/Projects/flux_hopf_lib`).

## flux_hopf_lib — Shared core (preferred imports)

| Import | Description |
|--------|-------------|
| `flux_hopf_lib.simulation` | λt survival, twist PDE, κ helpers (replaces toe `relaxation_survival.py`) |
| `flux_hopf_lib.constants` | φ, e, π, R residual, κ defaults, W_g lock |
| `flux_hopf_lib.quaternion` | Unit quaternions / rotors |
| `flux_hopf_lib.hopf` | Hopf map, hopfions, linking |
| `flux_hopf_lib.flux` | Flux lattice config, gauge steps, defects |
| `flux_hopf_lib.conduit` | ConduitConfig, golden-angle / gauge mixins |

```python
from flux_hopf_lib.simulation import simulate_twist_pde_survival, compare_to_analogs
# Mystery scripts also re-export via scripts/_common.py
```

Local path: `flux_hopf_lib/` — `pip install -e ../flux_hopf_lib`

## TOE — Gauged Hopf Lattice / Flux Flywheels

| File | Description |
|------|-------------|
| `toe/src/conduit.py` | RubikConeConduit v10.8 — full torch model (still loaded for conduit probes) |
| `toe/src/relaxation_survival.py` | **Legacy** — prefer `flux_hopf_lib.simulation` |
| `toe/src/emeraldSunConduit.py` | Golden-ratio harmonic on topological clock |
| `toe/scripts/meta_optimize_invariants.py` | Optuna/Ray search for emergent W_g, κ, braiding phase |
| `toe/scripts/pde_relaxation.py` | 3-torus twist PDE demo script (core math in flux_hopf_lib) |
| `toe/scripts/two_gyro_lattice_demo.py` | Two-gyro lattice visualization |
| `toe/scripts/run_reproduction.py` | One-command W_g / φ_b reproduction |
| `toe/scripts/epoch_bake_sweep.py` | Parameter sweep with invariant locks |
| `toe/scripts/2d_higgs_prototype.py` | 2D Higgs-mode analogy (Nature Materials 2026 link) |
| `toe/configs/default.yaml` | Default conduit configuration |

## TOE Papers (PDF)

| File | Topic |
|------|-------|
| `111_docs/toe/toe_swarm/papers/Aaron's_TOE_Complete.pdf` | Complete TOE |
| `111_docs/toe/toe_swarm/papers/GW_Burst_Threshold.pdf` | Burst threshold derivation |
| `111_docs/toe/toe_swarm/papers/GW_Echo.pdf` | GW echo predictions |
| `111_docs/toe/toe_swarm/papers/GW_Echo_Derivation.pdf` | Echo amplitude derivation |
| `111_docs/toe/toe_swarm/papers/Lagrangian_Derivation.pdf` | Skyrme-like Lagrangian |
| `111_docs/toe/toe_swarm/papers/Observer_Synchronization.pdf` | Global pointer / holonomy |
| `111_docs/toe/toe_swarm/papers/Relativistic_Completion.pdf` | QED + Einstein-Cartan completion |
| `111_docs/toe/Aaron's Theory of Everything.pdf` | Standalone TOE summary |
| `111_docs/toe/Derivation of wg_base equals 350 from First Principles.pdf` | W_g = 350/π origin |
| `111_docs/toe/Observer Sync.pdf` | Observer synchronization |

## Related Simulation Stacks

| Path | Role |
|------|------|
| `qvpic/src/conduit.py` | Quaternion Vortex Persistent Identity Conduit |
| `pic/src/conduit.py` | Persistent Identity Conduit (PIC lineage) |
| `hfb/` | Hopf Flux Bubble — analog gravity, Hopfions, defect metrics |
| `vqc_proto/` | Orbital Braille VQC typehead (OAM / quaternion encoding) |
| `vqc/` | Parent VQC OAM simulations |
| `rhythm/scripts/meta_optimize_rhythm.py` | Rhythm meta-optimizer (related invariant search) |

## Vortex / 3-6-9 Context

| Path | Notes |
|------|-------|
| `toe/src/conduit.py` | `toroidal_modulo9=True`, `vortex_math_369=True` flags |
| `toe/scripts/vortex_swarm.py` | Vortex swarm with gauge α = −0.85 × imbalance |