# Provisional model status

The repository includes `01_ai_edge/models/pothole.pt` with class `{0: pothole}`.
It runs in the local edge pipeline. The separate `best.pt` exposes `{0: '0'}` and
is rejected by the single-class detector.

The pipeline check used 12 recorded frames starting at frame 560, four inferences,
and a deliberately reduced 0.25 confidence threshold to exercise delivery. It
created four tracked observations and delivered them successfully to a test backend.
This is execution evidence, not detection accuracy or an unseen-video evaluation.
The normal default remains 0.70, pending evaluation.

| Handoff item | Status |
| --- | --- |
| Labeled training/validation/test dataset | Not supplied |
| Training provenance of bundled pothole weights | Unknown |
| Precision, recall, mAP | Not measured |
| Selected operating threshold | Provisional, not validated |
| Unseen-video/negative-case review | Pending |
| Custom training and evaluated model release | Pending dataset and evaluation |

The evaluation command generates a measured report once data and weights are
available. Do not replace the pending entries with illustrative metrics.
