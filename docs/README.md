# Project documentation

Start with the [project README](../README.md) for installation and the commands to
run the backend, dashboard and video player.

| Document | Purpose |
| --- | --- |
| [Demo walkthrough](demo-flow.md) | Show detection, location, saved images and issue resolution to a reviewer |
| [Architecture](architecture.md) | Edge, backend, dashboard and location module responsibilities |
| [API contract](api-contract.md) | Observations, grouped issues, evidence gallery, telemetry and review actions |
| [Implementation status](implementation-status.md) | What works and what remains pending |
| [Testing](testing.md) | Verified checks, measured runtime and verification limits |
| [Reviewer roadmap](reviewer-roadmap.md) | Prioritized improvements and their purpose |
| [Integration guide](integration.md) | Team handoffs, configuration and legacy data migration |
| [Model inventory](../01_ai_edge/models/README.md) | Preserved checkpoints, actual class labels and checksums |
| [Training guide](../02_dataset_model_training/README.md) | Dataset preparation, annotation, training and evaluation |

The [initial gap assessment](gap-assessment-and-task-plan.md), [cleanup record](cleanup.md)
and [September 15 pull record](pull-20260915.md) document earlier decisions. Their
dated test counts and local database examples are historical, not fixed demo totals.

Local recovery archives, credentials, installed dependencies, databases, detection
outputs and unreviewed training frames are excluded from Git. Startup creates the
required runtime directories; a fresh clone begins with an empty database.
