# Tiny walking Simulation over encrypted sound

This is a generated, amplitude-only teaching session, not measured Wi-Fi CSI or
human activity inferred by a model. The supplied generated path drives the avatar.

## Prepare

Restart both Orbit and its laptop server after installing this update. Pair the
phone using Connect on the same reachable LAN. The existing APK can use these
server-provided screens; no new APK is required for this feature.

Download Simulation-Walking-Tiny.npz on the phone from AcousticLink → Walking
Simulation → Save tiny walking file. It is 1,698 bytes: 32 packets at nominal
20 packets/s (timestamps 0–1.55 s), one synthetic amplitude subcarrier and one
generated walking trajectory, quantized to float16. Phase is intentionally absent.
Its short, reduced data are not suitable for classifier evaluation, robust gait
frequency estimation or comparison with full research recordings.

## Generated-file test first

1. Open AcousticLink on the phone. Choose the tiny NPZ as the file payload.
2. Check Simulation/generated data and Encrypt the sound payload.
3. Enter orbit-demo-passphrase (public teaching key; use no private data).
4. In Reliability settings select 400 bit/s and turn SECDED/FEC OFF.
5. Create sound transmission. It should show 16 frames and 52.18 seconds.
6. Press Test generated WAV · codec only. On success the original file is in the
   Shared reconstructed inbox on both paired screens. This test uses a WAV file,
   not the room's speaker/microphone path.
7. On the laptop refresh AcousticLink if necessary; find the exact tiny filename
   and select Save & open Simulation in 3D. Press Play.

The original supplied path animates a walking person; the original 32 amplitude
samples produce the graphs. Try CSI explorer, DSP laboratory with FIR / Hamming
and 7 taps, and FFT & STFT with STFT size 32. With such a short record frequency
resolution is limited. No calibrated motion threshold or classifier result is
invented. Replay is short; press Restart replay to repeat it. Avoid regenerating
the scenario if demonstrating the exact received samples.

## Physical sound attempt

1. Keep the generated transmission ready on the phone.
2. On laptop AcousticLink enter the same passphrase; select Raw baseline.
3. Start recording the laptop microphone BEFORE playing the phone audio.
4. Play complete sound from the beginning on the phone. Capture the full 52.18 s;
   stop the laptop recording about one second after playback finishes. Keep the
   receiver recording below 60 s for the bounded clock-search fallback.
5. Only Hash-checked content recovered establishes success. Valid fragments alone
   do not establish complete-file recovery. On success use the inbox 3D button.
6. If recovery fails, save the receiver WAV for diagnosis. Do not pretend the
   generated-file test is physical delivery. Physical reception remains unverified.

The 200 bit/s + FEC room profile is deliberately NOT the profile for this example:
it makes this file much longer. A smaller payload does not repair the existing
microphone/decoder issue. No automatic Wi-Fi fallback is used for acoustic decode.

## Script to say

“This is a tiny generated walking session with channel-amplitude samples and an
explicitly supplied movement path. I encrypt its bytes and encode them into sound
tones. The receiver must recover every required frame, authenticate the encrypted
payload and verify the file hash. Orbit then replays that supplied path and shows
the received samples in the DSP tools. It is a communication-and-replay experiment,
not proof that Wi-Fi reconstructed a human. This first test decodes a generated
WAV; physical speaker-to-microphone delivery is a separate test.”

## Actual verification

Encrypted 16-bit PCM generated-WAV → exact recovered NPZ bytes → shared Library →
Sensing Studio import → 1×32×3 supplied trajectory and FIR analysis: PASS.
Command: python -m pytest tests/test_tiny_walking.py -q -s
Physical handset speaker-to-laptop-microphone delivery: NOT EXECUTED.
