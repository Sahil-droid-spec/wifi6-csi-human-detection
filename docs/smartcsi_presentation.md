# Orbit presentation script

## Before opening
Extract the SmartCSI update into your Orbit folder (the folder containing Orbit.exe). Keep orbit-data. Close and reopen Orbit.exe. The laptop server is still available through Connect or Start-Orbit-Server.cmd. The phone companion displays the updated laptop interface when paired.

## 1. Introduce the problem — Home
Say: “Ma’am, Orbit analyses saved Wi-Fi channel measurements to explore human presence detection. It combines signal processing, machine learning and soft-computing experiments.”
Say: “Today I am showing offline recordings and clearly labelled simulation examples. This is not verified live Wi-Fi sensing.”

## 2. Show the input — Library and Saved graphs
Select Recorded, a 20 MHz recording, then Saved graphs.
Say: “These are numeric CSI amplitudes across subcarriers and packets. The presence label belongs to the recording. A graph alone is not a prediction.”
Show the original notebook/PDF reference separately. The PDF is a reference, not an executable model or dataset.

## 3. DSP — Signal Studio
Open the selected recording; show one filter and its spectrum.
Say: “DSP prepares and inspects the signal. Smoothing is not automatically an accuracy improvement. Invalid packets are audited rather than treated as real flat signals.”

## 4. Soft computing — SC presentation
ANN tab: “The CSI classifier uses a 64-then-32-neuron ReLU MLP trained with Adam. Training loss and test accuracy are different.”
GA tab: “A chromosome selects features. Fitness is evaluated inside training groups, excluding the outer test date. GA is a selector, not a standalone presence classifier.”
Fuzzy tab: compute the first window. “Memberships and rules produce a graded response. This illustrative app demo is separate from my exported research fuzzy model.”

## 5. Compare models — Learning Lab
Show the saved cohort, graph/table and confusion matrix.
Say: “All rows must use the same captures and split for a fair comparison. Ensembles can improve, tie or worsen. These saved app experiments may use different settings from my newer Colab experiments.”

## 6. Explain SmartCSI — SmartCSI page
Point to pipeline and rule.
Say: “GA-RF supplies a presence score. If it is between 0.35 and 0.65 inclusive, the prototype averages it with a research fuzzy score. Otherwise it keeps the RF score. The final threshold is 0.5.”
If no imported CSV: “The rule is implemented and tested. The original exported capture scores are required before I can display the new accuracy. The app deliberately does not substitute the old fuzzy demo or invent missing predictions.”
If imported CSV: choose a capture, show RF score, activation, fuzzy score and final score. Show aggregate accuracy and confusion matrix. Say: “This recomputes the prototype from saved capture-level scores. The rule was explored on existing research results, so this is preliminary exploratory analysis, not independent validation.”
Do not claim 93.33% unless the imported rows reproduce it. Do not replace older 86.67% Phase 4C results with newer percentages from a prompt.

## 7. Network experiments — same page
Show AX throughput and BF latency graphs.
Say: “These are historical network simulator results, separate from classifier accuracy. AX is communication traffic; BF is sensing reports; Mixed schedules both. Switching modes does not change the same saved CSI waveform.”
Say: “Mixed need not beat AX-only. Optimized configurations must be compared with equally optimized AX settings.”
The newly requested optimized network summaries are import-required; these charts currently show the original installed simulator summary, not the claimed newer values.

## 8. Phone — Connect
Keep Orbit running on the laptop. Enable trusted LAN sharing, same Wi-Fi, fresh QR. On phone download one demo ZIP then import it. On laptop show Inbox and Replay.
Say: “The file transfer happens now. The stored signal was recorded or generated earlier. The phone is not capturing CSI.”
If phone networking fails, use laptop upload of the same ZIP; do not describe it as a successful phone transfer.

## 9. Finish
Say: “The contribution is a reproducible local workflow: import, inspect, process, compare, explain decisions and preserve evidence. Next work is independent recordings, exporting the exact research model and fuzzy artifacts, and hardware validation.”

## Required SmartCSI import
Export per-capture rows from Colab using the schema downloaded on SmartCSI. Required columns:
sha256, actual_presence, rf_probability, fuzzy_score, original_prediction, ga_prediction, validation_protocol.
One row per unique recorded capture; SHA-256 must match Library. Actual labels must match. Binary GA prediction must match the RF score threshold. Uncertain rows need fuzzy scores. Do not infer missing scores from predictions. Do not average window scores unless that is the original declared capture aggregation. Existing exports with different columns need explicit mapping in Colab; preserve the original files.
The importer does not certify the original training protocol; it retains the declared protocol and labels SmartCSI exploratory. No feature-reduction claim is calculated without an actual mask. No model file is executed from uploads.
