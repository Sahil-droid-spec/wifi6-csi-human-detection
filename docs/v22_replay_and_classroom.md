# Orbit 2.2 final classroom changes

Replay now requests bounded batches of 16 exact contract windows, prefetches the next batch, retains one mounted chart, uses a recording-wide y range and window-relative packet axis, and advances only after the displayed window is ready. In-flight prediction results are discarded on selection changes; single-model inference forwards the selected validation mode. Packet loss remains gaps. Frame and probability are aligned to the same displayed index.

Adds SC presentation (exact ANN/GA parameters, original training/fitness curves and illustrative Mamdani rule firing on a selected CSI window) and Saved graphs (current CSI traces, SVG export and separate historical notebook PNG figures). The original PDF is retained unchanged; 18 notebook figures and 45 distinct relevant code cells remain historical, outside Evidence.

Three new classroom ZIPs contain empty/still/moving generated channels, three neutral sessions each, with synthetic provenance retained. Complete nine-recording source cohort and seven evaluated classifiers are stored. Isolated API rehearsal passed all 3 hash-checked ZIP imports, 9 recording validations and 63 saved held-out classifier replays. Copies are a workflow demonstration, not new independent evidence. No hardware live CSI or native 802.11bf claims are added.

Executed verification: 85 pytest tests passed (122.37 seconds, one upstream deprecation warning), frontend TypeScript/Vite passed, scoped Ruff passed. Browser Replay ran from window 0 to 35 at 4× with a single unchanged ECharts canvas, then stopped at end. ANN presentation, actual Mamdani rule computation and a historical PNG rendering were checked in the browser. Physical phone operation and independent clean-machine testing remain NOT EXECUTED.
