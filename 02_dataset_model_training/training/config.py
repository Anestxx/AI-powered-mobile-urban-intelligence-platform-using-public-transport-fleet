"""Resolve portable dataset configuration before handing it to Ultralytics."""

from pathlib import Path
import importlib.util
import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_YAML = BASE_DIR / "training" / "data.yaml"
RUNS_DIR = BASE_DIR / "training" / "runs"
DEFAULT_MODEL = BASE_DIR.parent / "01_ai_edge" / "models" / "yolo11n.pt"
TRAINED_MODEL = RUNS_DIR / "pothole_v1" / "weights" / "best.pt"


def resolve_dataset(config_path=DATA_YAML, splits=("train", "val")):
    config_path = Path(config_path).resolve()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if data.get("names") not in ({0: "pothole"}, ["pothole"]):
        raise ValueError("The prototype requires exactly one class: 0 = pothole")
    root = (config_path.parent / data.get("path", ".")).resolve()
    data["path"] = str(root)
    for split in splits:
        if split not in data:
            raise ValueError(f"Dataset config has no {split!r} split: {config_path}")
        image_dir = root / data[split]
        if not image_dir.is_dir() or not any(
            p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
            for p in image_dir.iterdir()
        ):
            raise FileNotFoundError(f"Dataset split is missing or empty: {image_dir}. Import a labeled pothole dataset first.")
    return data


def write_runtime_config(data):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / "dataset.resolved.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return str(path)


def validate_training_inputs(data):
    spec = importlib.util.spec_from_file_location("pothole_dataset_validator", BASE_DIR / "scripts" / "validate_dataset.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    errors = validator.validate_dataset(Path(data["path"]), verify_images=True)
    if errors:
        raise ValueError("Dataset validation failed: " + "; ".join(errors[:3]))
