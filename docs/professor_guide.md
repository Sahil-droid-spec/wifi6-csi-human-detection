# Final ORBIT demonstration - updated 3 November

This guide supersedes the earlier V3 source-gap note. Latest source has 313 pages, archived 12-seed ns-3 output and 19 original graphs. No new experiment was run for the application update. GA-Fuzzy output remains supplied in the brief, pending original experiment export.

## A natural six-minute presentation
0:00 Home / Library: Ma'am, Orbit studies two different tasks: network communication performance when sensing shares resources, and human presence classification from saved CSI. The app preserves data, algorithms, successes and failures. Today I am showing archived simulations and recorded-data analysis, not verified live Wi-Fi sensing.

0:45 Research Journey - stages 1 and 2 - figures 1 to 5: Adding BF scheduling costs airtime. Changing sensing intervals, MCS, payload, guard interval and contention windows helps performance, but AX+BF must be compared against equally configured AX. The early matched experiments did not demonstrate a win over AX-only. BF here means IEEE 802.11bf sensing, not beamforming.

1:35 stages 3 and 4 - figures 6 to 10: Standard OBSS-PD spatial reuse produced layout-dependent gains up to about 84.29%. This is an existing Wi-Fi 6 feature, not my invention. SARA V1 and V2 did not add throughput over the standard/best tested settings. Simplified SAGE V1/V2 models also had mixed outcomes. Keeping negative results makes the baseline comparison honest.

2:20 stage 5 - figures 11 to 13: SAGE V3 adapts rate selection using packet feedback, loss history and an SNR safety margin. The PDF patch uses an EWMA: failure updates L to 0.75L+0.25; success multiplies L by 0.75; aggregate feedback uses failed/total with weight 0.25. The safety margin influences the MCS chosen for the next transmission. These code excerpts describe the displayed patch; I do not claim to have rerun its archived binary here.
The archived 12-seed ns-3 results, against IdealWifiManager, show Rayleigh gains of about 25.77% for AX and 22.23% for AX+BF. Severe fading gives about 51.86% for AX and 42.66% for AX+BF. The strongest is a relative throughput gain from about 23.835 to 36.197 Mbps, not percentage points. Stable-channel throughput is essentially unchanged. Source notes warn that channel-event traces may differ.

3:25 stage 6 - figures 14 and 15: Communication improvements did not improve every outcome. Severe-fading successful BF reports declined from 2.492 to 1.933 per second; mean failed reports per ten-second run increased from 5.5 to 10.833. Thus the overall sensing-and-communication system is not fully optimized.

4:05 stage 7 - figures 16 to 18: SmartCSI is separate. CSI features go through GA selection, RF and an optional fuzzy stage. RF scores between 0.35 and 0.65 trigger equal averaging with a research fuzzy score, then threshold 0.5. The preliminary offline 15-capture summary is 73.33%, 86.67% and 93.33%. False alarms fall from four to one; feature count falls from 1024 to 13, a 98.73% reduction. Base scores were date-held-out, but the fusion rule was explored on available results, so independent validation is still needed. The original per-capture CSVs are needed for app recomputation; a summary does not reconstruct predictions.

5:00 stage 8: The latest proposed GA-Fuzzy controller uses Sugeno memberships to adjust the SNR margin and GA to search parameters. The supplied brief reports about +0.698% in a simplified model on 50 held-out traces. The original result export is not attached; the app labels this pending source verification. It is not the ns-3 result, cannot be added to 51.86%, and is not hardware validation.

5:40 figure 19 / final slide: Orbit makes the research inspectable through original graphs, labelled evidence, replay, DSP tools and report export. Next steps are reproduction from raw archives, independent CSI recordings and physical hardware validation. The phone transfers files to the laptop server; it does not measure CSI itself.

## Exact clicks
Sidebar Research Journey -> stages. Graph buttons open Graphs & Evidence. Select a thumbnail, use Previous/Next and Zoom. Professor Presentation opens ten slides with notes. Print Research Report -> Export full report PDF or Print / Save as PDF. Print Only Graphs is separate. The report has 30 A4 pages; graphs-only has 19. No twentieth original graph was supplied.

## Quick questions
Why not combine 51.86% and 0.698%? Different baselines, model types and experiments.
Is BF reliability solved? No; report reliability declined under the tested SAGE runs.
Is spatial reuse new? No; OBSS-PD is an existing Wi-Fi 6 capability.
Did SARA win? Not beyond the standard/best tested settings in the displayed experiments.
Is 93.33% live accuracy? No; preliminary offline 15-capture result with exploratory fusion.
Was ns-3 rerun by this app update? No; archived output was integrated and labelled.
Why do saved app models differ? Distinct settings/runs; retain their own cohort and protocol.
What does EWMA do? Smooth recent losses against past history. Weight 0.25 reacts faster than a smaller weight but remains imperfect under changing channels.
What is Sugeno? Weighted singleton rule outputs; here an SNR margin, not a presence probability. Different from the app's Mamdani teaching demo.

Accuracy=(TP+TN)/N; false alarms=FP; misses=FN. Relative gain=100*(new/baseline-1). Feature reduction=100*(1-13/1024). A confidence interval is tied to its resampling assumptions and experimental units, not proof of general reliability.
