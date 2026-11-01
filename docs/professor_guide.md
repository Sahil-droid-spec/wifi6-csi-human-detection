# ORBIT: professor presentation and engineering guide

## What the files actually establish
Source inspected: latest Colab PDF, 410 pages, exported 1 November. SmartCSI summary and rule appear on pages 340–345. Smart-MAC matched-baseline negative result appears on pages 361–362. The PDF ends with SAGE V2 independent-validation CODE, not a V3 experiment output. V3 source, EWMA parameters, seed trials and the 51.86% record were NOT supplied. The master prompt contains V3 summary claims; these are not equivalent to verified experiment records.
The app separately stores older models with different parameters. Never describe their metrics as the newer Colab experiment. SmartCSI CSV replay recomputes supplied scores; original research RF, feature mask and fuzzy model artifacts are still required for fresh research-equivalent inference.

## Natural 5–7 minute talk: about 6 minutes at a relaxed pace

### 0:00–0:45 — Home, then Library (Recorded)
“Ma’am, my project is ORBIT. I am studying two related but different problems: how to use Wi-Fi channel measurements to detect presence, and how communication traffic behaves when sensing shares the network. Orbit puts my data, signal-processing tools, classifiers and research graphs in one local application. Today I will show saved measurements and clearly labelled simulations. I have not verified a live passive CSI system or native BF sensing hardware.”
Select a 20 MHz recorded capture. Open Saved graphs. “Each packet contains channel measurements across subcarriers. A person's effect on reflections can change these measurements, but other environmental changes can also affect them. A waveform alone does not prove presence.”

### 0:45–1:35 — SmartCSI → AX/BF network graphs (scroll below research summary)
“AX means the Wi-Fi 6 communication standard. BF here means the 802.11bf sensing work, not beamforming. In my network simulation, AX-only carries traffic and Mixed schedules sensing reports as well. Sensing consumes resources, so adding BF does not automatically increase throughput. These graphs show throughput and report latency, not classification accuracy.”
“The small throughput difference is real in the saved summary; I do not exaggerate the axis. In the later matched Smart-MAC validation, AX-only was 75.7338 Mbps and Smart-MAC+BF was 75.413 Mbps. That is about 0.424% worse. A faster tuned configuration must be compared against AX tuned the same way.”

### 1:35–2:20 — Signal Studio and Learning Lab
“Some optimization attempts failed. Earlier FIR smoothing did not improve the RF capture result, and some classifier or hybrid combinations performed worse. I kept those results. Cleaner-looking signals are not automatically better for classification.”
“In Learning Lab I compare methods only on the same recordings and outer validation split. The held-out date is excluded from scaling, feature selection and training. A combination does not always win. These app runs have their own saved settings; I keep them separate from newer Colab results.”

### 2:20–3:10 — SmartCSI → SAGE V3 verification-gap explanation
“My next direction was adaptation to channel conditions rather than claiming that sensing always helps. SAGE V3 is described in my supplied research brief as a packet-loss-driven optimization. A common mechanism is an exponentially weighted moving average: new smoothed loss equals alpha times recent loss plus one minus alpha times the old estimate. A larger alpha reacts faster; a smaller one smooths more.”
“However, the files currently available to this app do not contain the V3 implementation or trial records. Therefore I cannot state its exact alpha, thresholds or actions as verified. The brief gives 23.835 to 36.197 Mbps for severe-fading AX-only. Relative gain is the difference divided by baseline, times 100: approximately 51.865% from those rounded values. The stated 51.86% requires the original unrounded record. This is a scenario-specific claim awaiting verification, not a general Wi-Fi speed guarantee.”
If the professor requires verified results only: omit the numeric V3 claim and say it is pending source validation. Do not point at V2 code as evidence for V3.

### 3:10–4:35 — SmartCSI top historical graph, then SC presentation → GA and Fuzzy
“SmartCSI addresses presence detection, a separate task. I extract CSI features. A genetic algorithm selects a subset, Random Forest produces a presence score, and a fuzzy stage is used when the score is uncertain. The prototype calls 0.35 through 0.65 uncertain. For those cases it averages RF and research fuzzy scores equally. Otherwise it keeps the RF score. At 0.5 or above the output is presence.”
“The PDF reports 73.33% for original RF, 86.67% for GA-RF and 93.33% for this prototype on 15 captures. Printed false alarms fall from four to two to one, with zero misses in these rows. The fuzzy stage was activated for three of fifteen captures. That is a 20 percentage-point accuracy difference, not 20% more throughput.”
“The individual base scores came from held-out dates, but I explored the fusion rule using the available results. This makes the final figure preliminary exploratory evidence. Independent recordings are still required. One capture changes accuracy by 6.67 percentage points. Here the app displays the PDF summary as historical output; the import section recalculates results only when the original prediction CSVs are provided.”
GA tab: show actual app run settings, explicitly a separate saved run. Fuzzy tab: “This interactive membership demo illustrates the concept; it is not silently substituted for my research fuzzy model.”

### 4:35–5:20 — Replay, then Connect
“Replay aligns a stored signal window with its saved held-out prediction. It is offline replay, not live CSI reception. Invalid packets are audited, and skipped windows are different from absence predictions.”
“Connect runs a local server. My phone can upload a stored file over the same Wi-Fi and the laptop processes it. The transfer is happening now; the channel recording was made earlier. The network interface is not automatically verified as Wi-Fi 6.”

### 5:20–6:15 — SDR & spectrum, then limitations
“Here is a separate hardware-free DSP extension. The simulator injects an AM tone and an FM tone. I tune −16 kHz and select AM to recover 440 Hz; I tune +16 kHz and select FM to recover 880 Hz. The spectrum and waterfall are calculated from samples, and the audio is actually demodulated. I can also import properly described complex IQ recordings. This does not turn the laptop Wi-Fi adapter into an arbitrary-band SDR.”
“BF sensing reliability needs more than a throughput number. We need report delivery, latency, scheduling overhead, a valid sensing algorithm and hardware verification. Future work includes fresh independent CSI recordings, the exact SAGE V3 artifacts, stronger cross-environment validation and receive-only SDR hardware tests. My contribution is an inspectable workflow that preserves both improvements and failures.”

## Exact screen checklist
1. Home → Library → Recorded → 20 MHz capture.
2. Saved graphs → median amplitude plot.
3. SmartCSI → historical classification graph and network plots.
4. Signal Studio → same recording, filter/spectrum.
5. Learning Lab → same cohort comparison and confusion matrix.
6. SmartCSI → SAGE verification-gap text (no fabricated V3 graph).
7. SC presentation → GA, then Fuzzy (compute window).
8. Replay → Held-out predictions → Run → Play, 0.5× or 1×.
9. Connect → fresh QR, same Wi-Fi, send demo ZIP → Inbox.
10. SDR & spectrum → AM/−16000 → Generate → play; FM/+16000 → Generate → play. Controls need user playback gestures; speakers/phone playback must be checked locally.

## Important terms, equations and metrics
- AX / 802.11ax: Wi-Fi 6 communications technology. A saved AX-tagged dataset does not prove the current LAN link uses AX.
- BF / 802.11bf: WLAN sensing enhancements. Not a synonym for beamforming; hardware/standards implementation here is unverified.
- CSI: complex channel response per subcarrier/antenna/time. Amplitude and phase describe the channel; this app's presence pipeline primarily uses amplitude features.
- OFDM subcarrier: one frequency component of the multi-carrier signal. 20/40 MHz are channel bandwidths, not packet rates.
- Multipath, LOS/NLOS, fading: multiple reflected paths; direct-path present/blocked; changing channel strength/phase. Rayleigh is a statistical fading model, not a building-specific measurement.
- SNR: signal/noise power ratio, often 10 log10(Psignal/Pnoise) dB. The receiver's spectral peak contrast is NOT calibrated SNR.
- Throughput: delivered data per second. Goodput: useful payload delivered per second, excluding protocol overhead according to the experiment's definition. Do not equate simulator layers without checking counters.
- Mbps: million bits per second. Latency: elapsed delivery time. Jitter: delay variation. Neither is classifier accuracy.
- Packet loss: lost/attempted packets over a defined interval. PDR: delivered/attempted. Retries and application sequence gaps require explicit counting rules.
- EWMA: L_t = alpha*l_t + (1-alpha)*L_(t-1), 0<alpha<=1. Loss l_t may be a binary failure or a window loss fraction; those are different designs. Initial estimate, alpha, window and policy actions must be specified. Not a future-channel oracle.
- MCS: modulation and coding scheme. Higher rates can fail in poorer channels. ACK: delivery acknowledgement; an ACK-adaptive baseline matters for fairness. Airtime is the time spent using the radio resource.
- OBSS-PD: overlapping-BSS packet-detection threshold used for spatial reuse; more reuse can also cause interference. SARA/SAGE are project controller names, not standards. Exact policies must be read from their source. V3 policy is missing here.
- Relative gain: 100*(new-baseline)/baseline. Percentage points: new percentage minus old percentage. From the rounded V3 table: 51.865%, not independent verification.
- Feature vector: numeric representation. The app uses per-subcarrier mean, standard deviation, adjacent valid-sample change and percentile spread. 1024 can arise from 256 subcarriers × four features; verify each model contract.
- GA: binary feature-mask population, fitness, selection, crossover, mutation and elitism. RF fitness inside training groups is not outer test accuracy. A printed 13-feature claim requires its mask and fold provenance to reproduce.
- RF: ensemble of decision trees; votes/scores combine trees. Its probability output is not automatically calibrated confidence.
- Fuzzy: graded memberships and rules. The app's Mamdani demonstrator uses min AND/implication, max aggregation and centroid defuzzification: integral z*mu(z) dz / integral mu(z) dz. Research fuzzy scores have their own learned/fixed rule contract; do not conflate them.
- SmartCSI: if |p_RF-0.5|<=0.15 then s=(p_RF+fuzzy)/2, otherwise s=p_RF; predict presence for s>=0.5. Current import replay uses original per-capture scores, not newly fitted models.
- ANN: nonlinear weighted layers learned by backpropagation. Saved CSI app MLP uses 64 and 32 hidden ReLU units, Adam, maximum 300 iterations; not part of the specified GA-RF-fuzzy SmartCSI rule.
- Confusion matrix: actual-label rows, predicted-label columns. TN=no-person correct; FP=false alarm; FN=missed person; TP=person correct.
- Accuracy=(TP+TN)/N. Recall=TP/(TP+FN). Precision=TP/(TP+FP). F1=2PR/(P+R). Balanced accuracy averages class recalls; macro F1 averages class F1. Zero misses in a small sample does not establish perfect recall in deployment.
- Leave-one-date-out: train on other dates and test excluded date. Shared captures, scaling, feature selection and tuning must not leak into the held-out fold. Post-hoc rule selection still needs an independent validation set.
- Seed: pseudo-random initialization identifier. Multiple independent seeds measure simulation variability; they are not multiple real lab captures. Mean/SD/CI require actual trials. Bootstrap CI depends on resampling unit and assumptions.
- ns-3: discrete-event network simulator. The PDF's later SAGE link model explicitly says it is not ns-3. Physical measurement is another evidence category.
- SDR/IQ: software processing of digitized radio; I+jQ represents two quadrature components. Sample rate determines observable bandwidth. Frequency translation multiplies IQ by exp(-j*2*pi*offset*t).
- FFT/PSD/waterfall: frequency transform; power per frequency under a chosen normalization; spectrum versus time. Here PSD uses arbitrary amplitude reference, not calibrated dBm.
- AM demodulation: envelope magnitude followed by filtering/DC removal. FM demodulation: successive-sample phase difference scaled to frequency, then filtering/resampling. Receiver output normalizes amplitude and is not an RF strength measurement.
- Scanner: median PSD floor plus 12 dB and prominence/separation rules; detects peaks, not guaranteed stations. No AI modulation classifier or protocol decoder is implemented in this update.
- Resampling: changing sample rate with appropriate anti-alias filtering. Receiver uses polyphase resampling to 8 kHz audio. WAV is a saved audio file shared by HTTP, not continuous live streaming.

## Likely professor questions — short answers
Q: Is 93.33% real-time accuracy? A: No. It is the printed offline result for 15 captures. Current app can recompute from imported scores; independent validation remains necessary.
Q: Why only 15? A: That is the available cohort for this experiment. It limits statistical strength and cross-environment claims.
Q: Did you tune on test results? A: The fusion rule was explored on available held-out base scores. That final prototype result is exploratory, not an untouched final test.
Q: Why do app RF results differ from Colab? A: They are distinct runs with distinct settings and provenance, not interchangeable evidence.
Q: Does BF mean beamforming? A: No, here BF refers to IEEE 802.11bf sensing. Beamforming is a separate technique.
Q: Does adding BF improve throughput? A: Not inherently; sensing uses resources. Matched Smart-MAC validation here remained below AX-only.
Q: What exactly improves by 51.86%? A: The brief claims relative severe-fading AX-only goodput/throughput gain from 23.835 to 36.197 Mbps. The exact V3 metric definition and trial records are missing, so I cannot certify it.
Q: Is V3 the same as the PDF's V2? A: No. The available PDF ends at V2 code; I do not use it to verify V3.
Q: What alpha did V3 use? A: I need the actual V3 source. I can explain EWMA but will not invent its parameter.
Q: Why EWMA? A: It balances recent evidence against history. It can react late to abrupt fading; smoothing is a tradeoff, not a guarantee.
Q: Why not compare only with fixed MCS? A: A fixed baseline may be artificially weak. An equally configured ACK-adaptive baseline is needed.
Q: Is the 13-feature selection leakage-safe? A: It must be selected inside each training fold; the final deployment mask cannot establish that by itself. The original masks and folds are needed to verify the claim.
Q: Why GA plus RF? A: GA searches feature subsets and RF classifies. Feature reduction can reduce cost but can overfit; outer validation tests the combined procedure.
Q: Why fuzzy only sometimes? A: It adds an alternate score around the RF uncertainty region. The rule needs separate evaluation to establish utility.
Q: Are these probabilities confidence? A: No, they are uncalibrated model/decision scores unless calibration is separately validated.
Q: Can you detect walking versus standing? A: Current classifiers predict presence. Simulation condition names do not establish real activity recognition.
Q: Is the phone sensing CSI? A: No. It transfers files and displays the laptop interface.
Q: Why show failed experiments? A: They reveal overhead and baseline fairness, and prevent cherry-picking improvements.
Q: Are SDR and Wi-Fi CSI interchangeable? A: No. A Wi-Fi adapter is not a universal-band SDR, and IQ modulation analysis is a different task from CSI presence classification.
Q: Can the SDR classify any signal? A: No. This update implements AM/FM demodulation and peak scanning; AI recognition, live hardware and arbitrary protocol decoding remain incomplete.
Q: Does BF report delivery prove sensing reliability? A: No. Report timeliness, coverage, sensing accuracy, channel conditions and hardware implementation all matter.
Q: Is the audio live streamed with measured latency? A: No. This is computed WAV playback over authenticated HTTP. Continuous transport, jitter and end-to-end measurements are future work.

## Practice method
Answer in your own words in 2–4 sentences. Start with the distinction between communication performance and presence classification. Then give one measured/source-labelled finding and one limitation. Do not memorize the exact script. The chat will ask one question at a time and correct your answer.
