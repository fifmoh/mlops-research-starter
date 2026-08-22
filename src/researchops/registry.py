from __future__ import annotations

import json
import os
from pathlib import Path

from .contracts import MetricsArtifact, ModelArtifact, Promotion
from .manifest import sha256_file


class AtomicRegistry:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def promote(
        self, model: ModelArtifact, metrics: MetricsArtifact, policy: dict[str, object]
    ) -> Promotion:
        if sha256_file(model.path) != model.sha256 or sha256_file(metrics.path) != metrics.sha256:
            return Promotion(
                promoted=False, model_sha256=model.sha256, reason="artifact hash mismatch"
            )
        lineage: list[set[str]] = []
        for split in ("support", "calibration", "evaluation"):
            descriptor = policy.get(f"{split}_manifest")
            if not isinstance(descriptor, dict):
                return Promotion(
                    promoted=False,
                    model_sha256=model.sha256,
                    reason=f"missing split manifest: {split}",
                )
            path_value = descriptor.get("path")
            expected_hash = descriptor.get("sha256")
            if not isinstance(path_value, str) or not isinstance(expected_hash, str):
                return Promotion(
                    promoted=False,
                    model_sha256=model.sha256,
                    reason=f"invalid split manifest descriptor: {split}",
                )
            manifest_path = Path(path_value)
            if not manifest_path.is_file() or sha256_file(manifest_path) != expected_hash:
                return Promotion(
                    promoted=False,
                    model_sha256=model.sha256,
                    reason=f"split manifest hash mismatch: {split}",
                )
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("split") != split or not isinstance(manifest.get("identities"), list):
                return Promotion(
                    promoted=False,
                    model_sha256=model.sha256,
                    reason=f"invalid split manifest content: {split}",
                )
            identities = {
                identity["content_hash"]
                for identity in manifest["identities"]
                if isinstance(identity, dict) and isinstance(identity.get("content_hash"), str)
            }
            if len(identities) != len(manifest["identities"]) or not identities:
                return Promotion(
                    promoted=False,
                    model_sha256=model.sha256,
                    reason=f"invalid split identities: {split}",
                )
            lineage.append(identities)
        if any(lineage[left] & lineage[right] for left in range(3) for right in range(left + 1, 3)):
            return Promotion(
                promoted=False,
                model_sha256=model.sha256,
                reason="support/calibration/evaluation lineage overlaps",
            )
        values = json.loads(metrics.path.read_text())
        auroc = float(values["auroc"])
        minimum_value = policy.get("minimum_auroc", 0.70)
        baseline = policy.get("baseline_auroc")
        if not isinstance(minimum_value, (int, float)):
            raise TypeError("minimum_auroc must be numeric")
        if baseline is not None and not isinstance(baseline, (int, float)):
            raise TypeError("baseline_auroc must be numeric")
        minimum = float(minimum_value)
        if auroc < minimum:
            return Promotion(
                promoted=False, model_sha256=model.sha256, reason="minimum AUROC not met"
            )
        if baseline is not None and auroc < float(baseline) - 0.02:
            return Promotion(
                promoted=False, model_sha256=model.sha256, reason="baseline regression exceeds 0.02"
            )
        pointer = self.root / "current.json"
        temporary = pointer.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "model": str(model.path),
                    "sha256": model.sha256,
                    "metrics_sha256": metrics.sha256,
                },
                sort_keys=True,
            )
            + "\n"
        )
        os.replace(temporary, pointer)
        return Promotion(
            promoted=True, model_sha256=model.sha256, reason="policy passed", pointer=pointer
        )
