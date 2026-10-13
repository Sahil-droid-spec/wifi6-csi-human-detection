# Research Notes

## Main paper

Meneghello et al., "Toward Integrated Sensing and Communications in
IEEE 802.11bf Wi-Fi Networks," IEEE Communications Magazine, 2023.

The paper describes CSI/CFR as a source of information about wireless
multipath propagation. Its 802.11ax experiment uses channel measurements,
Doppler processing and a DNN for human activity recognition.

## Reference implementation

SHARPax: https://github.com/francescamen/SHARPax

This code is a reference for the processing pipeline. The current
project uses a different public dataset, so the loader and baseline
classification method need to be adapted.

## Dataset

Zenodo: https://zenodo.org/records/17225694

Checks performed in Colab:
- ZIP integrity check passed.
- Fifteen MATLAB files were found in the 20 MHz subset.
- Configuration files contain modulation, bandwidth and people labels.
- MATLAB v7.3 files were inspected using h5py.
- One inspected capture array had shape (256, 18634).

## Planned work

1. Confirm labels and 802.11ax modulation for each capture.
2. Plot CSI amplitude and extract simple features.
3. Train and evaluate a baseline classifier.
4. Compare models using held-out captures.
5. Later, investigate through-wall data separately.

## Reporting

Do not state accuracy before running the model. Do not claim that the
current dataset is the original SHARPax dataset. Do not present a
simulated wall effect as real through-wall hardware evidence.
