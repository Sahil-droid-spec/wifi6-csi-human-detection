# ORBIT 5.0 — simple demo

1. Close Orbit and its server, apply the update to the existing folder containing Orbit.exe, keep orbit-data, and restart Start-Orbit-Server.cmd for phone access. The server is still necessary and retained. In-app updates require a server restart, not just a page refresh.
2. Open **Signal lab → 3D Sensing Studio** (or Ctrl+K → 3D Sensing Studio). Select **Simulation library → One person walking → Apply & restart simulation**.
3. Say: “This is a generated complex-channel experiment. The 3D person explains the scenario; this is not a body or position reconstructed from Wi-Fi.”
4. Press **Play**. The packet counter, scene label, generated movement, graph cursor and motion card use one timeline. Pause, Step packet or scrub to inspect the same sample. Low-quality windows show a gap, not an invented result.
5. Drag the room to orbit; use Zoom+/−, Pan arrows, Top/Front/Side, Human focus and Reset. Try solid, wireframe and hologram. Expand Scene controls to toggle room/grid/signals/person. Change the global theme: the room, cards and text should follow it.
6. Open **CSI explorer**: amplitude heatmap and phase when the input actually contains complex values. Amplitude-only recordings correctly say phase unavailable.
7. Open **DSP laboratory**. Compare raw and filtered data; select FIR/Hamming or Butterworth. Cutoff is cycles per packet; LP/HP/band and notch have different purposes. Say: “A smoother graph does not prove better detection.” Coefficients and response are calculated by real code.
8. Open **FFT & STFT**. Explain frequency content and time-varying spectrum. Spectrum uses one stated contiguous valid segment. Hz needs a known sample rate; recorded untimed data use cycles per packet.
9. Open **Motion analytics**. Show threshold crossings and Jump here. This is a motion proxy, not a trained human-presence probability. Still people may not trigger motion, and gain/noise changes can trigger false events.
10. Open **Experiments**. Change seed/noise/loss/speed and Apply; same seed+settings reproduce the same channel. Save comparison summaries; do not describe them as an accuracy leaderboard. Empty baseline calibration is synthetic, separate from recorded validation.
11. Open **Record & export → Save NPZ to Library**. Download NPZ/JSON/CSV. Reopen the exported JSON/NPZ using the file control above. NPZ preserves complex channel and generated ground-truth positions where present; JSON is the median-trace summary. Saved synthetic calibration is explicitly labelled and is not independent validation. Files retain Simulation metadata. Shared file management is **Connected workbench → Library** (rename/export/trash/restore).
12. To show your own CSI, use the saved-input selector above, choose **Selected saved CSI recording**, then Load. The avatar is an illustration and recording remains unchanged. If an evaluated model has held-out windows for that capture, load it explicitly: its actual saved decision appears only within those windows. Use existing Replay/Evidence for the full validation report. No compatible model means no invented prediction.
13. Diagnostics checks the actual server and displays the real configuration; Theory & viva gives searchable formulas and explanations.

## Connect your phone

Keep laptop and phone on the same reachable Wi-Fi or laptop hotspot. Start-Orbit-Server.cmd, open Connect, create a fresh QR and scan it. localhost/127.0.0.1 on a phone points to the phone, not the laptop. Use the laptop's current LAN address. Use Connection Doctor if client isolation/firewall blocks it; do not disable authentication or expose the server publicly.

Install the new signed companion APK5.0 (versionCode10). Native Java features remain, with hardware acceleration and refreshed exact LAN allowances. The current laptop Wi-Fi address changed to10.179.100.79; APK4.3 did not allow that address. The hotspot address192.168.137.1 is also allowed. A physical handset's pairing, upload, GPU performance and microphone transfer still need acceptance. Phone camera/microphone commonly need trusted HTTPS; normal file transfer does not prove live CSI.

## The Wi-Fi6 engineering story

“Our original experiment studies how human presence changes recorded Wi-Fi channel measurements. Orbit lets us inspect those measurements, process them and evaluate models with recording/date separation. The 3D simulator explains the signal path; the DSP lab shows what filters do to the same samples. Phone uploads connect our devices, but uploaded application bytes are different from radio CSI. AcousticLink is a separate sound-modem experiment. We compare measured results only under their stated protocol, including negative findings.”

Existing SAGE/SmartCSI research results, MATLAB/Simulink, audio/mixer/speech, SDR and consented camera/retinal pages remain in their previous menus. Imported scores are not equivalent to rerunning original trained SmartCSI artifacts. No promise of medical diagnosis, webcam blood pressure, verified native802.11bf or through-wall localization.

## Three files to try from your phone

Use Connect → downloadable examples, or copy the three direct NPZ downloads from this release to your phone. They are labelled Simulation-Empty, Simulation-Still and Simulation-Walking; each contains8seconds of generated complexCSI at100nominal packets/s and52synthetic subcarriers, seed42,1%configured loss. No real room or Wi-Fi6 radio measurement is implied.

1. On the phone, download one NPZ. Upload it using Transfer & chat or Connected workbench → Shared files. Keep the Simulation flag on.
2. On the laptop, open Connected workbench → Shared files. Find that exact file and press **3D sensing replay**. The laptop reads the original saved bytes and embedded source metadata; it does not classify the file merely because it arrived over Wi-Fi.
3. Alternatively download the received original on the laptop, open3DSensingStudio and choose it with Reopen exported session. Press Play and inspect CSI/DSP/FFT views.
4. For a new experiment, change Source back to Simulation library, set parameters and Apply. Save its selected segment to Library, reopen it and confirm source/calibration and generated movement are retained.

The52-subcarrier educational generator is a channel experiment, not a replacement for the256/512-subcarrier verified research model inputs. A new synthetic52-subcarrier file does not receive a fabricated trained RF/ANN prediction.

For untimed recorded input, replay advances packet indices at a display speed of100packets/s at1×. This is a UI playback convention, not a measured packet rate. Only known generated timestamps are displayed in seconds.

Historical4.4demo guide is retained in archive/orbit_demo_guide_4_4.md.

Expanded view includes Play scene/Pause scene and Restart replay, controlling the same packet cursor. On narrow screens the default camera fits the room; use Human focus to inspect the avatar closely. Recorded/simulated source stays visible. If native fullscreen is blocked, Orbit expands the scene inside the app; use Exit expanded view to return.
