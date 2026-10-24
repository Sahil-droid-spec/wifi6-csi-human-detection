<div align="center">

# Wi-Fi CSI Human Presence & Activity Sensing

**A research project combining Wi-Fi Channel State Information (CSI), digital signal processing, machine learning, and soft computing.**

<p>
  <a href="https://colab.research.google.com/drive/1iFoaTazemwuRKRnVC7APWzceNzxh0OiK?usp=sharing"><img alt="Open research notebook in Colab" src="https://img.shields.io/badge/Open%20Research%20Notebook-Colab-F9AB00?logo=googlecolab&logoColor=white"></a>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white"></a>
  <a href="https://colab.research.google.com/"><img alt="Google Colab" src="https://img.shields.io/badge/Workflow-Google%20Colab-F9AB00?logo=googlecolab&logoColor=white"></a>
  <a href="https://scikit-learn.org/"><img alt="scikit-learn" src="https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikitlearn&logoColor=white"></a>
  <a href="https://numpy.org/"><img alt="NumPy" src="https://img.shields.io/badge/Arrays-NumPy-013243?logo=numpy&logoColor=white"></a>
  <a href="https://standards.ieee.org/ieee/802.11bf/11574/"><img alt="802.11bf research" src="https://img.shields.io/badge/802.11bf-Simulator%20study-0891B2"></a>
</p>

<p><b>Recorded CSI experiments · DSP preprocessing · Cross-domain evaluation · AX/BF simulator study</b></p>

</div>

---

## At a glance

This project studies whether changes in Wi-Fi CSI can support human-presence and activity sensing. It combines recorded CSI datasets with DSP feature extraction, supervised learning, genetic-algorithm feature selection, fuzzy logic, and exploratory cross-domain evaluation. A separate ns-3 experiment compares selected AX-only, BF-only, and mixed AX+BF simulator configurations.

> **Research status:** These are exploratory software and simulator experiments. The project has not established real-hardware through-wall detection, verified live CSI capture on the author's device, or validated native IEEE 802.11bf operation on consumer hardware.

## Research notebook

The complete analysis notebook, including saved code outputs and plots, is available here: [Open WIFI6RECONSTRUCTION in Google Colab](https://colab.research.google.com/drive/1iFoaTazemwuRKRnVC7APWzceNzxh0OiK?usp=sharing). Access depends on the notebook share settings. The repository is intended to hold the curated scripts, results, figures and documentation rather than raw datasets or large runtime backups.

## Workflow

<p align="center">
  <img src="assets/project_pipeline.svg" alt="Project workflow from recorded CSI data through DSP, models, evaluation and reporting" width="100%">
</p>

1. **Inspect data:** audit dataset labels, CSI arrays, configuration files and PCAP/CSI alignment where available.
2. **Process signals:** convert complex CSI to amplitude, create windows, extract subcarrier statistics, and compare FIR filtering and DFT summaries.
3. **Evaluate models:** compare Logistic Regression, Random Forest, genetic-algorithm feature selection, fuzzy rules and a scale-invariant hybrid approach.
4. **Test transfer:** evaluate LOS/NLOS and antenna/configuration domain shifts, keeping source-domain training and target-domain testing distinct.
5. **Compare simulator modes:** measure selected MAC-level outputs for AX-only, BF-only and mixed AX+BF in a partial ns-3.40 research implementation.

## Selected signal visualizations

### 20 MHz CSI traces

These are saved traces from three recorded captures labelled no person, one person, and four people. The traces illustrate differences in the recorded signal; they are not standalone proof of presence-detection accuracy.

<p align="center">
  <img src="assets/csi_20mhz_examples.webp" alt="CSI amplitude traces from 20 MHz captures with no person, one person, and four people" width="92%">
</p>

### FIR filtering and DFT comparison

The recorded analysis applied a 15-tap moving-average FIR filter to median CSI amplitude over packets and compared raw and filtered traces and their DFT magnitudes.

<p align="center">
  <img src="assets/fir_filter_comparison.webp" alt="Raw and FIR-filtered CSI amplitude traces" width="92%">
</p>

<p align="center">
  <img src="assets/dft_spectrum_comparison.webp" alt="DFT magnitude comparison for raw and FIR-filtered CSI amplitude" width="92%">
</p>

### 40 MHz CSI examples

<p align="center">
  <img src="assets/csi_40mhz_examples.webp" alt="40 MHz CSI amplitude examples for no person, one person, and five people" width="92%">
</p>

These plots come from embedded outputs in the research notebook. More detailed figures and confusion matrices remain in the notebook and archived experiment artifacts.

## Model results: the validation split matters

<p align="center">
  <img src="assets/validation_protocol_comparison.png"
       alt="Comparison of capture accuracy under two validation protocols"
       width="92%">
</p>

### 20 MHz presence baseline

The dataset inspection found **15 captures** across **two recording dates**: eight no-person captures and seven person-present captures. Window features use 256-packet windows with a 128-packet hop and 1,024 amplitude-derived features per window in the saved baseline workflow.

The recorded results differ substantially depending on the validation protocol:

| Evaluation | Model | Window accuracy | Capture accuracy | Capture F1 |
|---|---|---:|---:|---:|
| Stratified capture-grouped 5-fold | Logistic Regression | 0.9802 | 1.0000 | 1.0000 |
| Stratified capture-grouped 5-fold | Random Forest | 0.9771 | 1.0000 | 1.0000 |
| Leave-one-recording-date-out (2 dates) | Logistic Regression | — | 0.4667 | 0.6000 |
| Leave-one-recording-date-out (2 dates) | Random Forest | — | 0.7333 | 0.7778 |

**Interpretation:** the 100% capture scores came from grouped folds that kept windows from the same capture together, but did not hold out an entire date. The leave-one-date-out results are lower. Only two dates and 15 captures are available, so both evaluations are exploratory and do not establish broad generalization to new rooms, hardware, dates, or people.

### Raw features versus FIR-filtered features

| Features | Model | Capture accuracy | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|
| Raw | Logistic Regression | 0.6667 | 0.6000 | 0.8571 | 0.7059 |
| Raw | Random Forest | 0.7333 | 0.6364 | 1.0000 | 0.7778 |
| FIR filtered | Logistic Regression | 0.6000 | 0.5556 | 0.7143 | 0.6250 |
| FIR filtered | Random Forest | 0.7333 | 0.6364 | 1.0000 | 0.7778 |

In this date-held-out comparison, FIR filtering did not improve Random Forest capture metrics and reduced Logistic Regression metrics. The DSP preprocessing is therefore an experiment to assess, not an assumed improvement.

### Genetic algorithm and fuzzy-logic experiments

The recorded GA feature-selection run selected **8 features** in one outer fold and **12 features** in the other.

| Method | Capture accuracy | Macro-F1 | Presence F1 | Balanced accuracy |
|---|---:|---:|---:|---:|
| Raw Random Forest | 0.7333 | 0.7222 | 0.7778 | 0.7500 |
| GA + Random Forest | 0.8000 | 0.7964 | 0.8235 | 0.8125 |

The recorded fuzzy-rule experiment had capture accuracy 0.8000 and balanced accuracy 0.7857. These are preliminary results from the same small two-date dataset and should not be interpreted as a dependable estimate of out-of-domain performance.

## 40 MHz CSI: a useful caution

The notebook records **11 MATLAB captures** with 512 subcarriers, plus a PCAP/CSI reconciliation and window-quality audit. The saved capture-grouped model table reported 100% scores across threshold variants, but it explicitly cautions that presence is confounded with recording date/class distribution and only 11 captures were evaluated. An always-predict-presence reference reached 72.73% accuracy on a separate 33-capture table, with 0.50 balanced accuracy and 9 false alarms. We therefore retain the 40 MHz 100% result as **exploratory and potentially confounded**, not as a headline claim of generalization.

## LOS/NLOS and cross-domain evaluation

Four recorded domains were evaluated:

| Domain | Feature matrix shape |
|---|---:|
| NLOS / BQ | 452 × 208 |
| NLOS / PIFA | 440 × 208 |
| LOS / BQ | 460 × 208 |
| LOS / PIFA | 465 × 208 |

The workflow tested 12 directional transfers for presence and three-class activity. The scale-invariant hybrid v1 beat both comparison baselines in only **1 of 12 presence-transfer directions** and **4 of 12 activity-transfer directions**. Examples:

| Transfer task | Method | Accuracy | Balanced accuracy | Macro-F1 |
|---|---|---:|---:|---:|
| NLOS/BQ → LOS/BQ, presence | Raw Logistic Regression | 0.9935 | 0.9952 | 0.9926 |
| NLOS/BQ → LOS/BQ, presence | Hybrid v1 | 0.9109 | 0.9323 | 0.9040 |
| NLOS/PIFA → NLOS/BQ, presence | Raw Random Forest | 0.8628 | 0.7923 | 0.8222 |
| NLOS/PIFA → NLOS/BQ, presence | Hybrid v1 | 0.6726 | 0.5000 | 0.4021 |

**Takeaway:** performance is domain-dependent, and the hybrid is not a universal improvement. A high score in one room/configuration should not be generalized to other environments without controlled testing.

## AX / BF simulator study

The project separately compared three simulator configurations using a partial ns-3.40 research implementation, with five runs per configuration (15 valid runs in total):

| Configuration | Valid runs | Mean BF sensing latency | Mean AX throughput |
|---|---:|---:|---:|
| AX-only | 5/5 | Not applicable (BF disabled) | 57.1744 Mbps |
| BF-only | 5/5 | 0.8540 ms | Not applicable |
| Mixed AX+BF | 5/5 | 8.0313 ms | 56.5456 Mbps |

<p align="center">
  <img src="assets/phase7_simulator_results.png" alt="Recorded AX throughput and BF sensing latency means for three simulator configurations" width="92%">
</p>

In this tested setup, mixed AX+BF had a mean reported BF sensing latency about 9.4× the BF-only value, and mean AX throughput about **1.10% lower** than AX-only. Throughput and latency are different metrics and should not be treated as a single score.

**Simulator limitations**

- “100 successful sensing reports” is not 100% human-presence or activity-recognition accuracy.
- BF sensing latency is not ML inference latency or end-to-end latency from a person's movement to an app prediction.
- BF-only and AX-only do not use identical offered user-data loads.
- The simulator is a partial research implementation, not proof of IEEE standards conformance or physical 802.11bf operation.
- The random seed did not guarantee identical topology positions; five runs per configuration are exploratory, not perfectly paired.
- These results do not establish through-wall detection on real hardware.

## Sensing modes planned for the application

| Mode | Current evidence | Status |
|---|---|---|
| **Wi-Fi 6 / 802.11ax CSI** | Recorded CSI data, DSP pipeline, and presence-model experiments | Offline analysis available; live CSI capture unverified |
| **802.11bf WLAN sensing** | Standards/architecture comparison and ns-3 simulation | Compatible physical hardware/firmware not verified |
| **Proposed Adaptive Wi-Fi Sensing** | Proposed application architecture | Adapters and mode-selection logic not implemented/validated |

The proposed application is intended to run on a laptop and be accessible from a phone on the same trusted local network. **Phase 8 UI/UX design and implementation are pending; the app is not finished.**

## Repository and reproducibility

The repository includes starter dataset-inspection and baseline scripts. The larger research workflow still relies on notebook cells, datasets, intermediate feature artifacts, and an ns-3 build; it is not yet one-click reproducible from a clean checkout. No raw CSI archives, PCAPs, large datasets or simulator build tree should be committed.

Planned engineering tasks:

- Refactor notebook phases into standalone, documented scripts.
- Add deterministic split manifests and consolidated evaluation tables.
- Preserve model outputs, confusion matrices and experiment metadata.
- Design the application's requirements, navigation and responsive screens before implementation.
- Integrate only tested data/model/simulator functionality and display source/status clearly.

## Data, code and research sources

- **CSI dataset:** [Zenodo — 20 MHz dataset](https://zenodo.org/records/17225694)
- **Reference implementation:** [SHARPax on GitHub](https://github.com/francescamen/SHARPax)
- **Background paper:** Meneghello, Chen, Cordeiro & Restuccia, “Toward Integrated Sensing and Communications in IEEE 802.11bf Wi-Fi Networks,” *IEEE Communications Magazine* (July 2023). [DOI: 10.1109/MCOM.001.2200806](https://doi.org/10.1109/MCOM.001.2200806)
- **IEEE 802.11ax:** [IEEE Standards Association](https://standards.ieee.org/ieee/802.11ax/7180/)
- **IEEE 802.11bf:** [IEEE Standards Association](https://standards.ieee.org/ieee/802.11bf/11574/)
- **Simulator used:** [IEEE 802.11bf ns-3 research implementation](https://github.com/idolumbantobing/IEEE_802.11bf)

This project uses a dataset different from the SHARPax experimental dataset. It adapts general CSI-processing ideas rather than claiming an exact reproduction of the paper's experiments.

---

<div align="center">
<sub>Research-first project · Results are reported with their validation limits · No claim of verified live sensing or real-hardware through-wall detection</sub>
</div>
