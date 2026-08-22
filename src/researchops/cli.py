from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import mlflow
import numpy as np

from .contracts import DatasetArtifact
from .determinism import set_determinism
from .manifest import ArtifactEntry, RunManifest, create_run_manifest, sha256_file
from .reference import FixtureEvaluator, FixtureTrainer
from .registry import AtomicRegistry


def reproduce() -> None:
    root = Path(__file__).parents[2]
    set_determinism(42)
    rng = np.random.default_rng(42)
    support_x = np.r_[rng.normal(-1, 0.2, (8, 4)), rng.normal(1, 0.2, (8, 4))]
    support_y = np.r_[np.zeros(8), np.ones(8)]
    cal_x = np.r_[rng.normal(-1, 0.2, (4, 4)), rng.normal(1, 0.2, (4, 4))]
    cal_y = np.r_[np.zeros(4), np.ones(4)]
    eval_x = np.r_[rng.normal(-1, 0.3, (10, 4)), rng.normal(1, 0.3, (10, 4))]
    eval_y = np.r_[np.zeros(10), np.ones(10)]
    temporary = root / "artifacts/.fixture-reference.npz"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        temporary,
        support_x=support_x,
        support_y=support_y,
        cal_x=cal_x,
        cal_y=cal_y,
        eval_x=eval_x,
        eval_y=eval_y,
    )
    dataset_hash = sha256_file(temporary)
    run = create_run_manifest(
        project="mlops-research-starter",
        git_sha="FIXTURE",
        cell_id=None,
        attempt=1,
        config={"seed": 42, "candidate_seed": 42},
        lock_sha256=sha256_file(root / "uv.lock"),
        datasets={"fixture": dataset_hash},
        models={},
        seeds=[42],
        command=["make", "reproduce"],
    )
    out = root / "artifacts/runs" / run.run_id
    existing_manifest = out / "manifest.json"
    if existing_manifest.exists():
        existing = RunManifest.model_validate_json(existing_manifest.read_text())
        if existing.datasets.get("fixture") != dataset_hash or not existing.artifacts:
            raise RuntimeError("immutable run manifest does not match resolved inputs")
        for artifact in existing.artifacts:
            artifact_path = (out / artifact.path).resolve()
            if (
                out.resolve() not in artifact_path.parents
                or not artifact_path.is_file()
                or sha256_file(artifact_path) != artifact.sha256
            ):
                raise RuntimeError(f"immutable run artifact failed verification: {artifact.path}")
        temporary.unlink()
        print(json.dumps({"manifest": str(existing_manifest), "reused": True}, sort_keys=True))
        return
    if out.exists():
        raise RuntimeError(f"immutable run directory is incomplete: {out}")
    out.mkdir(parents=True)
    dataset_path = out / "fixture.npz"
    temporary.replace(dataset_path)
    data = DatasetArtifact(
        path=dataset_path,
        sha256=dataset_hash,
        metadata={"synthetic_fixture": True, "disjoint": True},
    )
    split_arrays = {
        "support": (support_x, support_y),
        "calibration": (cal_x, cal_y),
        "evaluation": (eval_x, eval_y),
    }
    split_descriptors: dict[str, dict[str, str]] = {}
    split_paths: list[Path] = []
    for split, (features, labels) in split_arrays.items():
        identities = [
            {
                "row": index,
                "label": int(labels[index]),
                "content_hash": hashlib.sha256(
                    features[index].tobytes() + labels[index].tobytes()
                ).hexdigest(),
            }
            for index in range(len(labels))
        ]
        split_path = out / f"{split}-identities.json"
        split_path.write_text(
            json.dumps(
                {"split": split, "identities": identities},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
        split_paths.append(split_path)
        split_descriptors[split] = {
            "path": str(split_path),
            "sha256": sha256_file(split_path),
        }
    model = FixtureTrainer().fit(data, {}, run)
    metrics = FixtureEvaluator().evaluate(model, data, run)
    promotion = AtomicRegistry(root / "artifacts/registry").promote(
        model,
        metrics,
        {
            "minimum_auroc": 0.70,
            "support_manifest": split_descriptors["support"],
            "calibration_manifest": split_descriptors["calibration"],
            "evaluation_manifest": split_descriptors["evaluation"],
        },
    )
    if not promotion.promoted:
        raise RuntimeError(promotion.reason)
    artifact_paths = [dataset_path, model.path, metrics.path, *split_paths]
    artifacts = [
        ArtifactEntry(
            path=str(path.relative_to(out)),
            sha256=sha256_file(path),
            media_type="application/json" if path.suffix == ".json" else "application/octet-stream",
            size=path.stat().st_size,
            role=(
                "model"
                if path == model.path
                else "metrics"
                if path == metrics.path
                else "split_manifest"
                if "identities" in path.name
                else "dataset"
            ),
        )
        for path in artifact_paths
    ]
    manifest = run.model_copy(
        update={
            "finished_at": __import__("datetime").datetime.now(__import__("datetime").UTC),
            "metrics": json.loads(metrics.path.read_text()),
            "status": "success",
            "artifacts": artifacts,
            "warnings": ["SYNTHETIC FIXTURE — NOT A MEASURED RESULT"],
        }
    )
    existing_manifest.write_text(manifest.model_dump_json(indent=2) + "\n")
    mlflow.set_tracking_uri(f"sqlite:///{root / 'artifacts/mlflow.db'}")
    mlflow.set_experiment("mvtec-reference-fixture")
    with mlflow.start_run(run_name=run.run_id):
        mlflow.log_params({"seed": 42, "fixture": True, "candidate_seed": 42})
        mlflow.log_metrics(
            {
                key: float(value)
                for key, value in manifest.metrics.items()
                if isinstance(value, (int, float))
            }
        )
        mlflow.log_artifact(str(existing_manifest), artifact_path="evidence")
        mlflow.log_artifact(str(model.path), artifact_path="model")
        mlflow.log_artifact(str(metrics.path), artifact_path="metrics")
    print(
        json.dumps(
            {
                "promotion": promotion.model_dump(mode="json"),
                "manifest": str(existing_manifest),
                "reused": False,
            },
            sort_keys=True,
        )
    )


def package() -> None:
    root = Path(__file__).parents[2]
    subprocess.run(["uv", "build", "--wheel"], cwd=root, check=True)
    wheel = next((root / "dist").glob("*.whl"))
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    (root / "dist/wheel.sha256").write_text(f"{digest}  {wheel.name}\n")
    (root / "dist/sbom.cdx.json").write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "component": {"name": "researchops", "version": "0.1.0", "sha256": digest},
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    print(digest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["smoke", "docs", "demo", "reproduce", "package"])
    args = parser.parse_args()
    package() if args.command == "package" else reproduce()


if __name__ == "__main__":
    main()
