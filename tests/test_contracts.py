from pathlib import Path

from fastapi.testclient import TestClient

from researchops.api import app
from researchops.cli import reproduce
from researchops.splits import Identity, split_mvtec


def test_split_disjoint() -> None:
    rows = [
        Identity("bottle", "normal", f"/train/normal/{index}.png", f"normal-{index}")
        for index in range(12)
    ]
    rows.extend(
        Identity(
            "bottle",
            "normal",
            f"/test/normal/{index}.png",
            f"test-normal-{index}",
        )
        for index in range(4)
    )
    rows.extend(
        Identity("bottle", "defect", f"/test/defect/{index}.png", f"defect-{index}")
        for index in range(16)
    )
    split = split_mvtec(rows)
    sets = [{x.content_hash for x in split[n]} for n in split]
    assert not sets[0] & sets[1] and not sets[0] & sets[2] and not sets[1] & sets[2]


def test_fixture_reproduction(tmp_path: Path, monkeypatch) -> None:
    reproduce()
    manifests = list(Path("artifacts/runs").glob("*/manifest.json"))
    assert manifests and any("SYNTHETIC FIXTURE" in path.read_text() for path in manifests)


def test_prediction_rejects_fake_image_bytes() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/v1/predict",
            files={"file": ("fake.png", b"not-an-image", "image/png")},
        )
    assert response.status_code == 422
