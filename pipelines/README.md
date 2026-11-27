# pipelines: Doorstep batch data scripts

Python scripts that run outside the API. Status: **not started**.

| Script area | What it does | Owner | Plan |
|---|---|---|---|
| Bootstrap import | Loads Google Open Buildings v3 footprints inside the zone as `candidate` structures with confidence scores, so mappers confirm rather than start from nothing | Person B | B4 |
| Ground truth | Hand-corrected OSM footpaths for the campus (`ground_truth/`), used to evaluate the path graph and to generate synthetic GPS traces | Person A | A2 |
| Synthetic traces and graph evaluation | Noisy GPS walks generated from the ground truth; edge precision/recall, spurious edges, usable-route rate | Person B | B5 |
| Dedup and bootstrap metrics | Precision/recall of duplicate candidates; share of candidates confirmed / adjusted / rejected / missed | Person B | B3, B4 |
| Imagery change detection | Zone-cell change candidates from Open Buildings 2.5D Temporal and Sentinel-2 via Earth Engine (noncommercial tier), imported as re-survey tasks | Person B (movable to A) | B9 |

Rules: pipelines only **raise candidates or tasks**; they never assign codes, resolve duplicates or change
verified records. Imports go through the API so they stay atomic and idempotent.

Plans: [Person B](../docs/plans/person-b-services.md), [Person A](../docs/plans/person-a-clients.md) (A2).
