# Orbit 4.4 — Command center and acoustic receiver update

## Install / open

The existing Downloads/ORBIT installation has the matching updated application source and UI. Close Orbit completely, reopen Orbit.exe or Start-Orbit-Server.cmd, then reopen the phone APK page. Refresh alone cannot reload Python receiver code. The server health version is 4.4.0. Keep orbit-data.

For another existing Orbit 4.3 installation, extract Orbit-4.4-Quick-Update.zip into the folder containing Orbit.exe, replacing matching app-source files. Your existing runtime, speech model, datasets and trained models are reused. The current Android companion 4.3 remains compatible; its workspace is loaded from the laptop. No native APK code changed in this release.

## What was found in the supplied video

The supplied file is an 8.6-second screen recording of laptop playback, not an independently identified microphone WAV. Its AAC audio begins inside the first packet's training preamble. Previously, packet 2 of 2 passed CRC and the whole message remained incomplete. The corrected synchronization search recovered both frames and exactly the same 223 encrypted-envelope bytes as the matching original generated WAV. The private message was not decrypted. This establishes repair of that recorded clip's framing; it does not prove physical phone-to-laptop reception or identify the cause of a separate microphone failure.

The receiver now accepts the complete final sync marker when earlier training bytes are clipped. CRC, sequence/length checks, AES-GCM authentication and payload SHA-256 remain required. It does not fabricate missing data. New transmissions have one second of opening silence and a Play complete sound from the beginning button. Receiver output lists received/missing packet positions.

## Retry real phone sound

1. Restart the laptop server, then reopen the APK page.
2. On phone open AcousticLink, type Hello, choose Reliability settings → Use room-test profile (200 bit/s + SECDED), enter a shared passphrase and CREATE A NEW sound. Old saved WAVs do not gain the opening pause.
3. On laptop enter the same passphrase, select Raw baseline, refresh microphone choices and choose the intended input.
4. Start laptop recording. On phone press Play complete sound from the beginning. Let the entire sound finish, including the opening pause. Watch that the laptop's measured input level responds.
5. Stop and inspect the exact recovered message. A generated-WAV test is separate and is not a physical result.
6. If it fails, Save recording to Library for diagnosis → Download saved receiver WAV and provide that actual receiver file. Replay it to check whether it contains the whole modem sound. Fireworks may interfere; no cause is asserted without the relevant recording.

## Demonstrate Command center

1. Open Command center from Home or Signal lab in the sidebar. On phone use More / navigation to find it.
2. Use the top Recorded / Simulation switch and choose a saved CSI recording. Source labels remain visible.
3. The spatial explainer has Hologram, Wireframe and Solid views; empty, still, walking and two-person scenarios; pause, rotation and reset. These are procedural 3D illustrations, not pose estimates. Changing the illustrated scenario does not relabel or change the selected data.
4. Original/filtered graphs and the subcarrier map use the actual selected recording. Move the window slider; change filter, window, taps or cutoff. The spectrum axis is cycles per packet unless a separate measured rate is available. Charts support zoom and PNG export.
5. Filtering resets at each packet gap; invalid positions stay gaps, and runs shorter than 32 samples are withheld. The paired spectra use the longest contiguous usable run, whose exact packet range is displayed. No packet-gap zero filling or spectral stitching occurs. Startup transients are shown, not hidden.
6. Open Inspect filter response and computation for the calculated frequency response and measured DSP computation time. This time excludes disk/network and is not phone latency.
7. Save this DSP experiment, then inspect its source, settings and spectral window in run history/export. Model evidence displays existing matched-cohort results and protocols; no new accuracy is manufactured by the dashboard. Open Replay for actual held-out predictions.
8. Devices & transfer links to QR connection, ordinary file transfer, AcousticLink and diagnostics. Existing audio, retinal, MATLAB, learning and research pages remain available.

The layout was checked at desktop and phone widths in an isolated browser workspace using explicitly generated CSI. A real handset graphics/media acceptance check remains required. Reduce motion pauses the illustration; ordinary app themes remain available. The scene uses bundled browser/canvas code, without external 3D assets or cloud services.

## Validation limits

See the canonical checklist and test log. Camera-based clinical diagnosis, native 802.11bf, actual CSI/SDR hardware acceptance and recovery of original SmartCSI artifacts are not established by this update. Archived MATLAB/Simulink and research records remain their original dated experiments. This release does not claim rerunning those scientific studies or general room-acoustic reliability.
