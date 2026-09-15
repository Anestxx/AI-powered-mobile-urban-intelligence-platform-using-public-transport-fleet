# Preserved model checkpoints

All five checkpoints from `origin/main` commit `3c42b44` are preserved byte for byte.
The manifest records their SHA-256 checksums and class names read with Ultralytics.
Run `python tools/check_models.py` from the project root to check file integrity.

| File | Classes found | Use |
| --- | --- | --- |
| `ambulance.pt` | One named ambulance class | Downloaded in the latest pull; class verified, accuracy and connected alert integration pending |
| `pothole.pt` | One named pothole class | Active connected pothole detector |
| `best.pt` | One unnamed class, `0` | Preserved for inspection; class meaning needs confirmation |
| `yolo11n.pt` | 80 general-object classes | General model preview |
| `emergency.pt` | 80 general-object classes; no ambulance, fire-engine or police-vehicle class | Preview of the supplied checkpoint; emergency recognition is not established |

Names such as `best` or `emergency` do not establish the training target. No model
has been retrained, renamed, overwritten or converted during cleanup. Accuracy and
training provenance remain to be evaluated separately.

The two recordings remain in `../videos/`: `road_test.mp4` and
`ambulance_test.mp4`. The preview reads the actual model labels and never turns
general vehicle predictions into asserted emergency detections.
