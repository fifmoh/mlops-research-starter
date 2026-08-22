# mlops-research-starter / `researchops`

## Problem and boundary
Research results often lose their data identity, configuration, and serving provenance. `researchops` 0.1.0 supplies typed orchestration contracts, immutable manifests, deterministic seed control, hash verification, and atomic promotion. The bundled MVTec workflow is a reference application; images and model weights are never redistributed.

## Measured results
No real-data result is committed yet. `make reproduce` emits **synthetic fixture evidence only** and therefore is excluded from measured claims.

## Five-minute quickstart
```sh
uv sync --all-extras
make check test reproduce
make package contract-smoke
```

## Reproduction
The real-data pipeline order is fetch → validate → prepare → embed → train → calibrate → evaluate → register → evidence. Official MVTec download requires license acknowledgement. Seed 42 is designated before evaluation; promotion requires AUROC ≥0.70 and ≤0.02 regression.

## Documentation
- [Licenses](docs/licenses.md)
- [Security](SECURITY.md)
- [Demo](docs/demo-script.md)

## Limitations
Fixture embeddings test contracts, not vision performance. Accelerator extraction uses tolerance `abs_delta <= 1e-6`; CPU reference stages use one thread.

## Re-skin guide
Implement the five public protocols for a new workload; swap dataset/trainer/evaluator configuration, never copy orchestration code or weaken hash/promotion gates.
