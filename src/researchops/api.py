from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from .manifest import sha256_file


class State:
    model: dict[str, object] | None = None


state = State()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pointer = Path("artifacts/registry/current.json")
    if pointer.exists():
        payload = json.loads(pointer.read_text())
        path = Path(str(payload["model"]))
        if path.exists() and sha256_file(path) == payload["sha256"]:
            state.model = payload
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def ready() -> dict[str, str]:
    if state.model is None:
        raise HTTPException(503, "promoted artifact absent or hash-mismatched")
    return {"status": "ready"}


@app.get("/model-card")
def card() -> dict[str, object]:
    return {"fixture": True, "limitations": ["Reference smoke evidence is synthetic"]}


@app.post("/v1/predict")
async def predict(file: Annotated[UploadFile, File(...)]) -> dict[str, object]:
    started = time.perf_counter()
    body = await file.read(10 * 1024 * 1024 + 1)
    if len(body) > 10 * 1024 * 1024 or file.content_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(413, "one PNG/JPEG up to 10 MiB required")
    try:
        with Image.open(BytesIO(body)) as image:
            image.verify()
            image_format = image.format
            width, height = image.size
        if (
            image_format not in {"PNG", "JPEG"}
            or width < 1
            or height < 1
            or width > 10_000
            or height > 10_000
            or width * height > 50_000_000
        ):
            raise ValueError("unsupported image dimensions or format")
        expected_type = "image/png" if image_format == "PNG" else "image/jpeg"
        if file.content_type != expected_type:
            raise ValueError("declared MIME does not match decoded image")
        with Image.open(BytesIO(body)) as decoded:
            decoded.load()
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise HTTPException(422, "malformed or unsafe image") from exc
    if state.model is None:
        raise HTTPException(503, "model not ready")
    score = int(hashlib.sha256(body).hexdigest()[:8], 16) / 0xFFFFFFFF
    return {
        "score": score,
        "label": "defect" if score >= 0.5 else "normal",
        "threshold": 0.5,
        "model_version": state.model["sha256"],
        "request_id": str(uuid.uuid4()),
        "latency_ms": (time.perf_counter() - started) * 1000,
    }
