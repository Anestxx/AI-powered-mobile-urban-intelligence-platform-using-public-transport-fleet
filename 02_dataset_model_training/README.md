# Pothole dataset and model handoff

The active training contract is exactly **class 0 = pothole**. The bundled general
YOLO11n weights are a local lightweight initialization. Training automatically uses
CUDA if available, otherwise CPU. The currently usable `pothole.pt` is a provisional
model whose provenance and holdout accuracy are not established.

No labeled dataset is present. Do not report example precision/recall values as
measured results. Start by collecting labeled potholes and normal-road negatives,
with sources representing shadows, puddles, patches, water-filled potholes and
different camera/lighting conditions.

## Prepare and check data

To prepare frames from the bundled road recording for human annotation:

```powershell
python 02_dataset_model_training/scripts/prepare_review_set.py --output "02_dataset_model_training/review_sets/my-road-review"
```

Open the generated `index.html` to inspect frames and proposed boxes. Original
images, unreviewed proposals and recording groups are saved separately. This does
not generate training labels or retrain weights. Annotate the originals, correct
missed objects and review negative frames before importing a labeled dataset.
Keep a recording in one split and collect independent validation/test recordings.

The prepared `review_sets/road-review-20260915` contains 31 sampled frames and 55
unreviewed pothole proposals. These are labeling candidates, not measured accuracy.
The newly pulled `ambulance.pt` exposes `{0: 'ambulance'}`; its training dataset and
evaluation have not been supplied. Accident training still needs labeled examples.

Use existing source splits only if they have a trustworthy holdout separation:

```powershell
python 02_dataset_model_training/scripts/import_dataset.py --source "D:/potholes/split-source"
```

The source contains `train`, `valid`, `test`, each with `images` and `labels`.
Existing destination files are not overwritten. Alternatively, create a grouped
split from flat `images/` and `labels/` with a CSV containing `file,group`. Keep
frames from the same recording/source in one group:

```powershell
python 02_dataset_model_training/scripts/split_dataset.py --source "D:/potholes/labeled" --groups "D:/potholes/groups.csv" --output "02_dataset_model_training/dataset" --dry-run
python 02_dataset_model_training/scripts/split_dataset.py --source "D:/potholes/labeled" --groups "D:/potholes/groups.csv" --output "02_dataset_model_training/dataset"
python 02_dataset_model_training/scripts/audit_images.py --images "02_dataset_model_training/dataset/images" --report "02_dataset_model_training/training/runs/image-review.json"
python 02_dataset_model_training/scripts/validate_dataset.py --verify-images
```

The grouped split targets 70/20/10 percent of source groups, not exact image counts;
the manifest records actual counts. At least three independent groups are required.
Exact duplicate images are rejected by splitting. Image audit flags duplicates,
darkness and low edge detail for manual review, without deleting anything. These
heuristics do not establish label correctness or catch all near-duplicate images.
Empty labels are valid background examples; the overall dataset still needs objects.

## Train and evaluate

```powershell
python 02_dataset_model_training/scripts/check_gpu.py
python 02_dataset_model_training/training/train.py --check
python 02_dataset_model_training/training/train.py --epochs 30
python 02_dataset_model_training/training/validate_model.py --model "02_dataset_model_training/training/runs/pothole_v1/weights/best.pt" --report "02_dataset_model_training/training/runs/pothole_v1/model-report.md"
```

Use the project virtual environment. Training validates labels/images first, runs
with a Windows main guard, and writes to a new run directory. Later run names are
numbered; select the corresponding checkpoint explicitly for evaluation. The report
contains measured precision, recall, mAP and timing, plus the weight checksum.
Keep the dataset manifest/provenance and an error review beside the report.

Test unseen road videos separately, choose the operating confidence threshold from
the error tradeoff, and hand off versioned weights exposing `{0: 'pothole'}` with
image size, software versions, checksum and known limitations. Configure Member 1
with `--model` rather than overwriting the provisional model. `training/data.yaml`
resolves its dataset relative to its own location.
