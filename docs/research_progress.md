# Research Progress: Wi-Fi CSI Presence and Activity Sensing

## Current evidence

| Workstream | Status | Key limitation |
|---|---|---|
| 20 MHz CSI inspection | 15 captures over two dates inspected | Small number of dates |
| 40 MHz CSI inspection | 11 captures audited; 512 subcarriers | All no-person captures come from one date and all person-present captures from later dates |
| Baseline models | Logistic Regression and Random Forest evaluated | Scores depend on the validation protocol |
| ANN comparison | MLP evaluated alongside both baselines | ANN ties Random Forest on 20 MHz in the latest run; no demonstrated improvement |
| DSP | FIR filtering and DFT comparisons recorded | FIR did not consistently improve results |
| Soft computing | GA selection and fuzzy-rule experiments recorded | Preliminary small-data evidence |
| Cross-domain transfer | LOS/NLOS and BQ/PIFA evaluations recorded | Hybrid v1 is not a universal improvement |
| AX/BF simulator | 15 valid runs, five per configuration | Partial ns-3.40 implementation; simulator outputs are not human-detection accuracy |
| Local application | Requirements and modes proposed | Not yet implemented |

## Latest model comparison

See [the model comparison report](model_comparison_20mhz_40mhz.md) and [the metrics CSV](../results/presence_model_comparison_by_bandwidth.csv).

For 20 MHz, leave-one-recording-date-out capture accuracy was 0.4667 for Logistic Regression and 0.6667 for both Random Forest and ANN/MLP. Only two dates are available.

For 40 MHz, all three models reported 1.0000 capture accuracy with leave-one-capture-out evaluation. This is confounded: the three no-person captures are from 2024-07-30, and the eight person-present captures are from 2024-08-01/02. These scores must not be treated as evidence of date-independent generalization.

## Next engineering steps

1. Acquire 40 MHz captures with both presence classes represented across multiple dates/environments.
2. Keep evaluation protocols and model runs clearly labelled; do not merge historical results with the latest comparison.
3. Refactor the notebook into documented reusable scripts once the evaluation design is settled.
4. Design the responsive laptop-hosted local web application for recorded CSI import, signal visualizations, model selection, and results.
5. Keep recorded CSI prediction, AX/BF simulator results, proposed adaptive sensing, and unverified live sensing visibly separate in the app.
6. Verify hardware capture independently before claiming live operation or physical through-wall detection.
7. Prepare the final report and presentation from the recorded artifacts with the same limitations.

## Claims that remain unverified

- Live CSI capture on the intended hardware.
- Compatible physical IEEE 802.11bf hardware/software operation.
- Real-hardware through-wall human detection.
- A validated adaptive sensing algorithm.
