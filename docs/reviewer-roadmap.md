# Reviewer prototype: gaps, differentiation and efficiency

The working demonstration is recorded pothole detection, explicitly simulated GPS,
durable alert delivery, grouped issues and synchronized Python/web review. A real
CCTV installation, physical repairs and evaluated AI accuracy are outside this demo.

## Improvements implemented

- Resolution notes and persistent status history in both interfaces. Old records
  remain unchanged; earlier actions are not reconstructed. The actor is a shared
  local operator, not an individually identified account.
- An indexed geographic candidate query before exact location matching.
- Measured inference time, processed-frame rate, sampled-frame percentage and an
  optional JSON report. CPU thread count is configurable.
- The newly pulled command-center frontend uses actual backend totals and fleet
  heartbeats. All four models and both recordings have been preserved and checked.

## Add next, in this order

| Priority | Addition | Reviewer value | Suggested members |
| --- | --- | --- | --- |
| Done | Optional compact evidence crop per confirmed observation, with source filename and frame/time | Open an old alert and see what triggered it after the video has moved on | 1, 3, 4 |
| Done | A distinct false-detection action, reason and reopen flow | Separate a repaired/reviewed issue from an incorrect prediction; collect useful feedback | 2, 3, 4 |
| 3 | Label a small, independent set of varied clips and report misses/false alarms | Demonstrate measured limitations instead of treating confidence as accuracy | 1, 2, 6 |
| 4 | Route segments with last-inspected time and pass counts | Show the value of buses repeatedly inspecting their normal routes | 4, 5 |
| 5 | Link a later bus pass to a previously resolved issue for repair review | Show a before/after workflow; missing a detection on one pass is not proof of repair | 1, 3, 5 |

The first two additions are implemented. Evidence uses the durable outbox and is
visible in both interfaces. Two actual recorded-video crops measured 2,080 and 934
JPEG bytes in the latest check; HTTP/JSON overhead is additional. Next, prioritize
evaluation and route coverage. Dismissal currently applies to the grouped issue;
per-observation labeling remains a later improvement.
For evaluation, include negative examples, different lighting and unseen road
segments; keep near-duplicate frames out of the holdout. RDD2022 is a potential
road-damage dataset to assess for provenance, license and class mapping, including
its pothole class. [RDD2022 paper](https://arxiv.org/abs/2209.08538)

Emergency recognition needs a checkpoint with actual emergency-vehicle labels.
The supplied `emergency.pt` currently has general-object classes, so adding an
ambulance banner would not establish that capability. More event types, real GPS
and a live camera adapter are later extensions, not prerequisites for showing the
current recorded-video prototype.

## A credible project distinction

Road detection and fleet-based maps already exist: RoadBotics describes AI road
assessment from camera imagery, and NIRA describes connected-vehicle condition
monitoring and maintenance follow-up. These are vendor descriptions, not an
independent comparison of accuracy. [RoadBotics workflow](https://www.roadbotics.com/wp-content/uploads/2021/09/HowitWorkS2021.pdf),
[NIRA Road Health](https://www.niradynamics.com/products/road-health)

Position this student project around **repeat inspection using public-transport
routes, explainable confirmation across buses, delivery recovery during outages,
and a documented operator review cycle**. Route coverage and repair rechecks would
strengthen that combination. This is a proposed distinction for the demonstration,
not a claim of a world-first invention.

## Measurements on this laptop

Results are saved in `prototype-benchmark.json`; rerun with
`python tools/benchmark_prototype.py` in the project environment.

| CPU setting | Median inference | P95 inference |
| --- | --- | --- |
| Framework default, 3 threads observed | 398.16 ms | 1066.23 ms |
| 1 thread | 411.43 ms | 570.92 ms |
| 2 threads | 310.73 ms | 335.30 ms |
| 4 threads | 278.40 ms | 905.97 ms |

Eight identical recorded frames were processed twice per setting, with warm-up
excluded. Two threads gave the most consistent times in this small run and about
22% lower median time than the default. Four had a faster median but larger spikes.
Use `--cpu-threads 2` for a trial on this laptop; keep the universal default unchanged.
Prediction counts agreed across configurations, which does not establish accuracy.
Hardware, load, test order and the small sample limit these results.

In a separate sparse synthetic database of 10,000 issues, the geographic query
loaded one candidate instead of 10,000 and selected the same issue. Median query
plus matching time fell from 525.243 ms to 0.259 ms. Dense locations may still return
many candidates; this is not a production throughput claim.

Next, measure alert acceptance delay and bytes per event alongside detection speed.
Try smaller input sizes or alternate inference runtimes only with the same holdout
clips, checking for missed small potholes. The current player may run slower than
the recording; source FPS is not achieved inference speed. Confidence is not
physical severity, and simulated bus coordinates are not surveyed pothole positions.
