import csv
import os
import tempfile
import zipfile
from pathlib import Path
import yaml
from huggingface_hub import hf_hub_download

ALPASIM_ROOT = Path(__file__).resolve().parents[2]
HUGGINGFACE_REPO = "nvidia/PhysicalAI-Autonomous-Vehicles-NuRec"
csv_path = ALPASIM_ROOT / "data/scenes/sim_scenes.csv"
out_dir = ALPASIM_ROOT / "data/nre-artifacts/all-usdzs"
out_dir.mkdir(parents=True, exist_ok=True)

with open(csv_path, newline="") as f:
    reader = csv.DictReader(f)
    downloaded = 0
    for row in reader:
        if downloaded >= 100:
            break
        uuid = row["uuid"]
        hf_filepath = row["path"]
        revision = row.get("hf_revision", "26.01")
        target_path = out_dir / f"{uuid}.usdz"

        if target_path.exists() and target_path.stat().st_size > 100_000_000:
            downloaded += 1
            continue

        print(f"[{downloaded + 1}/100] Downloading {uuid}...")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                dl_file = hf_hub_download(
                    repo_id=HUGGINGFACE_REPO,
                    repo_type="dataset",
                    filename=hf_filepath,
                    revision=revision,
                    local_dir=tmpdir,
                    token=os.environ.get("HF_TOKEN"),
                )
                with zipfile.ZipFile(dl_file, "r") as usdz_zip:
                    with usdz_zip.open("metadata.yaml") as mf:
                        meta = yaml.safe_load(mf)
                        actual_uuid = meta.get("uuid")
                        if actual_uuid != uuid:
                            raise ValueError(f"UUID mismatch: {actual_uuid} != {uuid}")
                os.rename(dl_file, target_path)
            downloaded += 1
        except Exception as e:
            print(f"Failed {uuid}: {e}")
            err_str = str(e)
            if any(code in err_str for code in ["401", "403", "GatedRepo"]):
                print("\nAccess error: Login with an authorized token via `uv run huggingface-cli login`.")
                break

print(f"Complete: {downloaded} scenes available in {out_dir}.")
