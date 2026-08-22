from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class ArtifactEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    path: str
    sha256: str
    media_type: str
    size: int
    role: str


class RunManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: str = "1.0.0"
    run_id: str
    cell_id: str | None
    attempt: int
    project: str
    git_sha: str
    started_at: datetime
    finished_at: datetime | None
    command: list[str]
    config_sha256: str
    lock_sha256: str
    datasets: dict[str, str]
    models: dict[str, str]
    seeds: list[int]
    hardware: dict[str, str]
    software: dict[str, str]
    metrics: dict[str, float]
    artifacts: list[ArtifactEntry]
    status: str
    warnings: list[str]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def create_run_manifest(
    *,
    project: str,
    git_sha: str,
    cell_id: str | None,
    attempt: int,
    config: dict[str, Any],
    lock_sha256: str,
    datasets: dict[str, str],
    models: dict[str, str],
    seeds: list[int],
    command: list[str],
) -> RunManifest:
    coordinates = {
        "project": project,
        "git_sha": git_sha,
        "cell_id": cell_id,
        "attempt": attempt,
        "config": config,
        "lock_sha256": lock_sha256,
        "datasets": datasets,
        "models": models,
    }
    run_id = canonical_hash(coordinates)[:16]
    return RunManifest(
        run_id=run_id,
        cell_id=cell_id,
        attempt=attempt,
        project=project,
        git_sha=git_sha,
        started_at=datetime.now(UTC),
        finished_at=None,
        command=command,
        config_sha256=canonical_hash(config),
        lock_sha256=lock_sha256,
        datasets=datasets,
        models=models,
        seeds=seeds,
        hardware={"machine": platform.machine(), "processor": platform.processor()},
        software={"python": platform.python_version()},
        metrics={},
        artifacts=[],
        status="running",
        warnings=[],
    )


def current_git_sha(root: str | Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except subprocess.CalledProcessError:
        return "UNCOMMITTED"
