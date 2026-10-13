# Wi-Fi 6 CSI Human Presence Detection

Student project exploring human presence detection using Wi-Fi 6
(802.11ax) Channel State Information (CSI) and machine learning.

## Current progress

- Read the Wi-Fi sensing research paper.
- Found the SHARPax reference implementation.
- Downloaded and extracted the public 20 MHz CSI dataset from Zenodo.
- Inspected the configuration files and MATLAB v7.3 data format.
- Next step: build and evaluate a basic presence-detection model.

The baseline model has not yet been confirmed to run successfully.
Results will be added after the experiments are completed.

## Dataset

Source: https://zenodo.org/records/17225694

The current dataset file is `20MHz.zip`. Keep the raw dataset outside
this repository. Do not upload the ZIP or raw packet captures to GitHub.

The dataset differs from the one used by SHARPax. This project adapts
the general CSI-processing approach rather than reproducing the original
experiment exactly.

## Research paper

F. Meneghello, C. Chen, C. Cordeiro, and F. Restuccia,
"Toward Integrated Sensing and Communications in IEEE 802.11bf Wi-Fi
Networks," IEEE Communications Magazine, July 2023.

DOI: https://doi.org/10.1109/MCOM.001.2200806

Reference code: https://github.com/francescamen/SHARPax

## Project plan

1. Inspect CSI files and their configuration labels.
2. Convert complex CSI into amplitude features.
3. Train a basic presence/absence classifier.
4. Evaluate using capture-grouped validation.
5. Compare models and improve preprocessing/features.
6. Later, investigate through-wall sensing with separate data and
   clearly labelled simulation experiments.

## Tools

Python, Google Colab, NumPy, pandas, h5py, Matplotlib and scikit-learn.

## Progress notes

On 13 October 2026, the 20 MHz dataset ZIP was extracted in Colab.
The archive integrity check passed. Fifteen MATLAB files were found.
An inspected configuration was labelled `ax`, and an inspected
`capture` array had shape `(256, 18634)` with real and imaginary
components. The MATLAB v7.3 data was read with h5py.

This confirms that the data can be inspected. It does not yet mean
that a classifier has been trained or that through-wall detection works.

## Running in Colab

1. Put `20MHz.zip` in the root of Google Drive.
2. Upload or clone this repository in Colab.
3. Install libraries with `pip install -r requirements.txt`.
4. Run `python src/inspect_dataset.py`.
5. Run `python src/baseline_presence.py`.

The scripts expect the archive at `/content/drive/MyDrive/20MHz.zip`.

## Limitations

This is a software-first project. It has not yet demonstrated
through-wall human detection. Simulated channel attenuation/noise is
not the same as a real through-wall measurement.
