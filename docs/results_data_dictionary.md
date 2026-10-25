# Results Data Dictionary

All CSVs in `../results/` come from saved research artifacts or the latest supplied Colab output. They are not raw datasets.

| File | Contents |
|---|---|
| `presence_model_comparison_by_bandwidth.csv` | One row per bandwidth/model; includes validation protocol, window and capture metrics, confusion-matrix counts, status and caveat |
| `capture_level_model_predictions.csv` | Out-of-fold prediction, actual label, average positive-class probability and window count for each capture/model |
| `model_validation_fold_details.csv` | Held-out group, train/test windows, ANN balancing sizes, iterations and captured warnings |
| `csi_capture_quality_audit.csv` | Per-capture label source, modulation, dimensions, packet count, invalid columns, accepted/rejected windows |
| `csi_window_quality_audit.csv` | Per-window packet bounds, length, valid fraction, acceptance flag and rejection reason |
| `cross_domain_transfer_metrics.csv` | Selected LOS/NLOS, BQ/PIFA domain transfer results |
| `wifi_sensing_technology_comparison.csv` | High-level comparison of 802.11ax CSI, 802.11bf and proposed adaptive sensing |
| `sensing_mode_readiness.csv` | Evidence and readiness status of the three proposed application modes |
| `ax_bf_simulation_runs.csv` | Individual simulator runs and raw summary metrics |
| `ax_bf_simulation_summary.csv` | Five-run mean and standard deviation per simulator configuration |
| `figures/confusion_matrix_*.png` | Capture-level confusion matrix figures for each bandwidth/model |

Presence label definition: `0` = no person present; `1` = person present. See the model evaluation report for dataset-specific validation caveats.
