# GitHub — kinaar8340

## This repository

| Repo | URL | Role |
|------|-----|------|
| **mystery** | https://github.com/kinaar8340/mystery | φ, e, π emergent signature probes and synthesis |

## Shared core (install this first)

| Repo | URL | Role |
|------|-----|------|
| **flux_hopf_lib** | https://github.com/kinaar8340/flux_hopf_lib | Single source of truth: quaternions, Hopf, flux/gauge, λt survival, κ, conduit mixins |

```bash
# Local editable
pip install -e ../flux_hopf_lib
# Or from GitHub
pip install "flux-hopf-lib @ git+https://github.com/kinaar8340/flux_hopf_lib.git@main"
```

## Upstream simulation stacks

| Repo | URL | Relevance to Mystery |
|------|-----|----------------------|
| **toe** | https://github.com/kinaar8340/toe | Full RubikConeConduit (torch), flux flywheels, papers — still needed for conduit probes |
| **hfb** | https://github.com/kinaar8340/hfb | Hopf fibration, flux bubbles, topological defects |
| **vqc_proto** | https://github.com/kinaar8340/vqc_proto | Orbital Braille — helical OAM, quaternion codec |
| **vqc_sims_public** | https://github.com/kinaar8340/vqc_sims_public | Parent VQC OAM simulation stack |
| **qvpic** | https://github.com/kinaar8340/qvpic | Quaternion vortex persistent identity conduit |
| **pic** | https://github.com/kinaar8340/pic | Persistent Identity Conduit (RubikCone lineage) |
| **6-string-optimizer** | https://github.com/kinaar8340/6-string-optimizer | Riemannian optimizer (meta-search tooling) |

## Hugging Face (live demos)

| Space | URL |
|-------|-----|
| **Mystery** (φ-e-π) | https://huggingface.co/spaces/kinaar111/mystery |
| Orbital Braille VQC | https://huggingface.co/spaces/kinaar111/orbital-braille-vqc |
| Hopf Flux Bubble | https://huggingface.co/spaces/kinaar111/hopf-flux-bubble |

Deploy Mystery Space: `bash scripts/deploy_hf_space.sh` — see [`docs/HF_SPACE.md`](../docs/HF_SPACE.md).