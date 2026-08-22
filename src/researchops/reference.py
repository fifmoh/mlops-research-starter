from __future__ import annotations

import json

import numpy as np
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.metrics import roc_auc_score  # type: ignore[import-untyped]

from .contracts import DatasetArtifact, MetricsArtifact, ModelArtifact
from .manifest import RunManifest, sha256_file


class FixtureTrainer:
    def fit(
        self, dataset: DatasetArtifact, config: dict[str, object], run: RunManifest
    ) -> ModelArtifact:
        data = np.load(dataset.path)
        x = data["support_x"]
        y = data["support_y"]
        model = LogisticRegression(
            class_weight="balanced", C=1, max_iter=1000, random_state=run.seeds[0]
        ).fit(x, y)
        calibration_scores = model.decision_function(data["cal_x"]).reshape(-1, 1)
        platt = LogisticRegression(C=1e6, random_state=run.seeds[0]).fit(
            calibration_scores, data["cal_y"]
        )
        target = dataset.path.with_name("model.json")
        target.write_text(
            json.dumps(
                {
                    "coef": model.coef_.tolist(),
                    "intercept": model.intercept_.tolist(),
                    "platt_coef": platt.coef_.tolist(),
                    "platt_intercept": platt.intercept_.tolist(),
                },
                sort_keys=True,
            )
            + "\n"
        )
        return ModelArtifact(path=target, sha256=sha256_file(target), metadata={"fixture": True})


class FixtureEvaluator:
    def evaluate(
        self, model: ModelArtifact, dataset: DatasetArtifact, run: RunManifest
    ) -> MetricsArtifact:
        data = np.load(dataset.path)
        payload = json.loads(model.path.read_text())
        raw_score = data["eval_x"] @ np.array(payload["coef"])[0] + payload["intercept"][0]
        calibrated_logit = (
            raw_score * np.array(payload["platt_coef"])[0][0] + payload["platt_intercept"][0]
        )
        score = 1 / (1 + np.exp(-calibrated_logit))
        target = dataset.path.with_name("metrics.json")
        target.write_text(
            json.dumps(
                {"auroc": float(roc_auc_score(data["eval_y"], score)), "fixture": True},
                sort_keys=True,
            )
            + "\n"
        )
        return MetricsArtifact(path=target, sha256=sha256_file(target), metadata={"fixture": True})
