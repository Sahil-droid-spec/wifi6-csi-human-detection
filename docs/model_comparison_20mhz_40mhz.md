# CSI Presence Model Evaluation at 20 MHz and 40 MHz

## Scope

This report records the results from the combined Colab workflow that evaluates Logistic Regression, Random Forest, and an artificial neural network implemented as an MLP (`MLPClassifier`). Metrics below are copied from the completed run's `results/presence_model_comparison_by_bandwidth.csv` and are not independently rerun in this package.

## Dataset and validation summary

| Bandwidth | MATLAB captures | No-person captures | Person-present captures | Accepted windows | Recording dates | Evaluation protocol |
|---|---:|---:|---:|---:|---:|---|
| 20 MHz | 15 | 8 | 7 | 1,920 | 2 | Leave-one-recording-date-out; capture prediction by majority vote over out-of-fold windows |
| 40 MHz | 11 | 3 | 8 | 382 | 3 | Leave-one-MAT-capture-out; capture prediction from mean out-of-fold window probability, exploratory |

Feature generation used overlapping CSI amplitude windows. The 20 MHz data has 256 subcarriers and a 256-packet window with a 128-packet hop. The 40 MHz data has 512 subcarriers and uses the dataset-specific windowing/validity rules in the notebook. Only accepted windows are included in modelling; detailed decisions are recorded in the capture and window quality audits.

## Results from this combined run

| Bandwidth | Model | Validation protocol | Captures | Window accuracy | Capture accuracy | Balanced accuracy | Presence precision | Presence recall | Presence F1 | Status |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 20 MHz | Logistic Regression | leave-one-recording-date-out; majority vote over windows | 15 | 0.3703 | 0.4667 | 0.4911 | 0.4615 | 0.8571 | 0.6000 | COMPLETED |
| 20 MHz | Random Forest | leave-one-recording-date-out; majority vote over windows | 15 | 0.5906 | 0.6667 | 0.6786 | 0.6000 | 0.8571 | 0.7059 | COMPLETED |
| 20 MHz | ANN (MLP) | leave-one-recording-date-out; majority vote over windows | 15 | 0.5661 | 0.6667 | 0.6786 | 0.6000 | 0.8571 | 0.7059 | COMPLETED |
| 40 MHz | Logistic Regression | leave-one-MAT-capture-out; mean window probability per capture; exploratory | 11 | 0.9607 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | COMPLETED |
| 40 MHz | Random Forest | leave-one-MAT-capture-out; mean window probability per capture; exploratory | 11 | 0.9764 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | COMPLETED |
| 40 MHz | ANN (MLP) | leave-one-MAT-capture-out; mean window probability per capture; exploratory | 11 | 0.9398 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | COMPLETED |

Capture accuracy and balanced accuracy should be the main focus because multiple windows from one capture are correlated. Window accuracy is a secondary diagnostic, not an independent sample-level performance estimate.

## Interpretation

### 20 MHz

- Logistic Regression: capture accuracy **0.4667**, balanced accuracy **0.4911**, presence F1 **0.6000**.
- Random Forest: capture accuracy **0.6667**, balanced accuracy **0.6786**, presence F1 **0.7059**.
- ANN/MLP: capture accuracy **0.6667**, balanced accuracy **0.6786**, presence F1 **0.7059**.

In this run, ANN matches Random Forest on the reported capture-level metrics; it does not demonstrate an improvement over Random Forest. The test holds out each of only two recording dates, so the estimate is highly uncertain.

These numbers differ from earlier, separately recorded baseline runs in the research log. They come from the newly assembled bandwidth-comparison pipeline and should be cited with this evaluation protocol and its implementation, not silently substituted for earlier historical results.

### 40 MHz — critical limitation

All three models produced 1.0000 capture accuracy in this run, with 3/3 no-person captures and 8/8 person-present captures classified correctly. **Do not present this as evidence of reliable 40 MHz generalization.** The audit shows the class label is perfectly associated with recording date in the 11-capture dataset:

| Recording date | No-person captures | Person-present captures |
|---|---:|---:|
| 2024-07-30 | 3 | 0 |
| 2024-08-01 | 0 | 7 |
| 2024-08-02 | 0 | 1 |

Every capture from 2024-07-30 is labelled no-person, while captures from 2024-08-01 and 2024-08-02 are labelled person-present. A model can exploit date-, environment-, or recording-specific differences rather than learn person presence. Leave-one-capture-out evaluation does not remove this confound because other captures from the same date remain in training. More balanced recordings with both labels on each date/environment are needed for a meaningful date-held-out test.

Therefore, the 40 MHz 100% capture scores are **exploratory and confounded**, not a headline performance claim. The differing 20 MHz and 40 MHz split protocols also mean scores should not be compared as a fair bandwidth-vs-bandwidth ranking.

## Quality-control counts

- Total unique capture rows in the audit: 26 (20 MHz: 15; 40 MHz: 11).
- Total windows recorded in the audit: 2322.
- For 20 MHz, all 1,920 feature windows were accepted by the recorded audit.
- For 40 MHz, 382 windows were accepted and 20 rejected by the saved validity checks.

The detailed audit CSVs preserve label sources, date, packet count, accepted/rejected windows, valid fraction, and rejection reason.

## Artifacts

- `../results/presence_model_comparison_by_bandwidth.csv` — summary metrics.
- `../results/capture_level_model_predictions.csv` — one prediction per capture/model.
- `../results/model_validation_fold_details.csv` — split groups, fold sizes and fit warnings.
- `../results/csi_capture_quality_audit.csv` and `../results/csi_window_quality_audit.csv` — data-quality audits.
- `../results/figures/` — confusion matrices per bandwidth and model.
- `../notebooks/wifi_csi_bandwidth_model_comparison.ipynb` — notebook used for the combined evaluation.

## Claims that are not supported

This experiment does not establish real-time sensing, live hardware capture, activity classification, physical through-wall detection, or standards-conforming IEEE 802.11bf operation. It is an offline binary presence experiment over a small, fixed research dataset.
