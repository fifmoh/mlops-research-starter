from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Identity:
    category: str
    label: str
    relative_path: str
    content_hash: str


def _order(row: Identity) -> str:
    return hashlib.sha256(
        f"42\0{row.category}\0{row.label}\0{row.relative_path}\0{row.content_hash}".encode()
    ).hexdigest()


def split_mvtec(rows: list[Identity]) -> dict[str, list[Identity]]:
    result: dict[str, list[Identity]] = {
        "support": [],
        "calibration": [],
        "evaluation": [],
    }
    categories = sorted({r.category for r in rows})
    for category in categories:
        local = [row for row in rows if row.category == category]
        normal_train = sorted(
            (row for row in local if row.label == "normal" and "/train/" in row.relative_path),
            key=_order,
        )
        normal_test = sorted(
            (row for row in local if row.label == "normal" and "/test/" in row.relative_path),
            key=_order,
        )
        defects = sorted(
            (row for row in local if row.label == "defect" and "/test/" in row.relative_path),
            key=_order,
        )
        if len(normal_train) < 12 or len(defects) < 12 or not normal_test:
            raise ValueError(f"{category} lacks required official split candidates")
        result["support"].extend(normal_train[:8] + defects[:8])
        result["calibration"].extend(normal_train[8:12] + defects[8:12])
        result["evaluation"].extend(normal_test + defects[12:])
    hashes = [{x.content_hash for x in result[name]} for name in result]
    if any(hashes[i] & hashes[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("split content hash overlap")
    return result
