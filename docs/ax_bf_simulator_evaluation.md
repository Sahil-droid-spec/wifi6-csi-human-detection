# Wi-Fi AX/BF Simulator Evaluation

## Purpose

A separate experiment compared AX-only, BF-only, and mixed AX+BF configurations in a partial ns-3.40 research implementation: [IEEE 802.11bf simulator](https://github.com/idolumbantobing/IEEE_802.11bf), cloned at commit `ea60e43c1cb191e6b0afc545660fab77f5813580`.

## Mean results across five runs per configuration

| Configuration | Valid runs | Mean BF sensing latency | Latency SD | Mean successful MAC sensing reports | Mean failed reports | Mean AX throughput | Throughput SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| AX-only | 5/5 | N/A (BF disabled) | N/A | 0 | 0 | 57.1744 Mbps | 0.0069 Mbps |
| BF-only | 5/5 | 0.8540 ms | 0.0003 ms | 100 | 0 | N/A | N/A |
| Mixed AX+BF | 5/5 | 8.0313 ms | 0.6289 ms | 100 | 0 | 56.5456 Mbps | 0.1053 Mbps |

For this tested setup, mixed AX+BF throughput was about 0.6288 Mbps (1.10%) below AX-only, while mixed-mode reported BF sensing latency was about 9.4 times the BF-only value.

## Configuration arguments

- BF-only: `--nBss=1 --nBfBss=1 --nAxBss=0`
- AX-only: `--nBss=1 --nBfBss=0 --nAxBss=1`
- Mixed AX+BF: `--nBss=2 --nBfBss=1 --nAxBss=1`

An early mixed setup omitted the AX BSS argument. A shared/cumulative `rxBytes` counter was later corrected; the repeated-run table included here supersedes earlier mixed throughput estimates. Seeds were 347, 722, 876, 59, and 463; five runs per configuration were marked valid.

## Limitations

- Successful MAC-level sensing report counts are not human-presence detection accuracy.
- BF sensing-report latency is not AI inference latency or end-to-end app latency.
- The AX-only and BF-only configurations did not have identical offered user-data workloads.
- The seed did not guarantee identical topology positions; the runs are not perfectly paired.
- Five runs per configuration are exploratory.
- The repository is a partial research implementation, not proof of IEEE standards conformance or physical 802.11bf operation.
- These results do not demonstrate real-hardware through-wall detection.

## Source files

- `../results/ax_bf_simulation_runs.csv`
- `../results/ax_bf_simulation_summary.csv`
- `../results/wifi_sensing_technology_comparison.csv`
- `../results/sensing_mode_readiness.csv`
