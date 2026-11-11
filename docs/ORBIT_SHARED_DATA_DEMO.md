# Phone-controlled ORBIT: send, receive and process

## Install this update

Close Orbit and its server. Extract Orbit-Shared-Data-Update.zip. Copy its contents
into the EXISTING folder containing Orbit.exe, merging app-source and replacing
files. Keep _internal and orbit-data. Run Start-Orbit-Server.cmd. Fully close and
reopen the phone APK/browser and scan a fresh QR in Connect. Existing APK 5.1 works;
this update is served by the laptop, so no new APK is necessary.

## Connect the equipment

Connect the laptop and phone to the same router or hotspot. The laptop can use
Ethernet or Wi-Fi if both interfaces reach the same LAN. The laptop runs ORBIT's
server; the phone opens that server's LAN address, never its own localhost.

An ESP32-S3 is separate sensing hardware. Power/USB connection alone does not
produce CSI or prove human detection. It needs compatible firmware and a receiver
protocol. Current Command Centre samples do not come from the ESP. Its connection
map explicitly says live ESP capture is not verified. Do not tell your professor
that the supplied paths are reconstructed from live ESP measurements.

## Phone to laptop: no separate file download needed

1. Open Command center on BOTH screens. On the phone press Take control.
2. In Send. Receive. Explore together, check This screen = Phone on the phone and
   Laptop on the laptop. The default follows the browser device; manual choices
   are for demonstration and are not hardware detection.
3. Set Send direction = Phone to Laptop. Choose One walking as the demonstration
   dataset. Press Send selected Simulation data on the PHONE.
4. This creates an explicit Simulation NPZ with 8 seconds, 160 packets, 16 complex
   subcarriers and supplied paths. The phone actually uploads those bytes to the
   laptop server; server-side SHA-256 verifies them. Both screens see the incoming
   filename. Expand Transfer graph to see actual server-accepted byte counts.
5. On the LAPTOP press Receive & open shared data. It downloads and hashes the
   actual bytes, records the receipt, saves the original to Library, explicitly
   takes control and starts shared replay. Both rooms show the same supplied walker.
   A tiny upload may finish before the next graph refresh; no animation invents
   extra transfer time. Resending identical data is a duplicate with no new upload
   timing. The server is on the laptop; laptop receipt can be a loopback download,
   not a second radio transfer.
6. On the phone press Take control again. Select One standing, Two walking or
   Standing + walking in Scenario controller. The laptop follows. These buttons
   generate a NEW Simulation; they do not edit or infer labels in your original file.
7. In Signals & DSP choose fir, hamming and 7 taps. Raw/processed waveform, FFT,
   phase, PSD, amplitude heatmap, spectrogram and motion proxy use the same current
   input. Filter settings/results synchronize; camera angles remain local.
8. Save input & derived analysis separately if you want to keep that scenario and
   analysis. The received original already remains in Library unchanged.

## Laptop to phone

Take control, change direction to Laptop to Phone, choose a sample and press Send
on the laptop. On the phone press Receive & open shared data. This time the phone
downloads the dataset over the LAN and verifies its hash. Both screens still share
one room and DSP experiment. Use Send my data file for your compatible NPZ/JSON,
numeric single-column CSV/NPY or PCM WAV. Files without supplied Simulation paths
do not acquire an invented human avatar. General images/video use Transfer and
their compatible studios; sending a photograph does not reconstruct a room.

## What to say

"My laptop hosts one shared experiment. My phone is a remote control and file
sender/receiver. Here I send an explicitly simulated walking dataset; the receiver
checks the original file hash and opens it on both screens. I can change the
scenario or DSP settings from either device. The animation uses supplied paths,
while the waveforms and spectra are calculated from the selected data. This
demonstrates the communication, replay and DSP parts supporting our Wi-Fi human
detection research. Live ESP CSI and through-wall position reconstruction are
separate hardware-validation tasks; this demonstration does not establish them."

## Acceptance and limits

Automated two-client tests cover both directions, verified file bytes, shared
dataset/people, playback, phone-role FIR processing, retained original hash,
authentication and all five sample classes. Browser checks exercise the actual
buttons using two desktop browser sessions with explicit roles. These are software
tests; physical phone/ESP acceptance is NOT EXECUTED by the agent. Active session
badges use server-observed browser/WebSocket heartbeats (20-second expiry), not
Wi-Fi association, router wiring or USB telemetry. No radio-standard, RF signal
strength, live CSI, inferred pose or medical measurement is claimed.
