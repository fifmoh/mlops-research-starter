from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .manifest import RunManifest


class Artifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = {}


class DatasetArtifact(Artifact):
    pass


class ModelArtifact(Artifact):
    pass


class MetricsArtifact(Artifact):
    pass


class Promotion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    promoted: bool
    model_sha256: str
    reason: str
    pointer: Path | None = None


class Prediction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    score: float
    label: str
    metadata: dict[str, Any] = {}


class DatasetStage(Protocol):
    def prepare(self, config: dict[str, Any]) -> DatasetArtifact: ...


class Trainer(Protocol):
    def fit(
        self, dataset: DatasetArtifact, config: dict[str, Any], run: RunManifest
    ) -> ModelArtifact: ...


class Evaluator(Protocol):
    def evaluate(
        self, model: ModelArtifact, dataset: DatasetArtifact, run: RunManifest
    ) -> MetricsArtifact: ...


class Registry(Protocol):
    def promote(
        self, model: ModelArtifact, metrics: MetricsArtifact, policy: dict[str, Any]
    ) -> Promotion: ...


class Predictor(Protocol):
    def predict(self, batch: Any) -> list[Prediction]: ...
