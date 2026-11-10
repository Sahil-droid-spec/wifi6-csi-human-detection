# ORBIT ULTIMATE — 3D SHARED COMMAND CENTRE V2
## Complete Premium Redesign, Multi-Person Simulation, Phone Control, Real Data Transfer and Synchronized Scientific Visualization

You are the lead 3D graphics engineer, animation engineer, React/Three.js developer, interaction designer, real-time systems engineer, FastAPI engineer, DSP engineer and QA engineer for my EXISTING ORBIT Ultimate application.

**This is a major upgrade request. I am dissatisfied with the current 3D animations, rendering quality and Command Centre usability.**

I want a dramatically better, more realistic, more interactive, scientifically meaningful 3D Command Centre.

The 3D experience should become one of ORBIT's main attractions, not a secondary animation.

My reference project is supplied as `WI-SENSE-X.zip`, and I previously provided its demonstration video.

**Inspect both resources carefully.**

Every feature demonstrated by the reference application is a MINIMUM functional requirement. Beyond that, create a significantly more advanced and original experience for ORBIT.

DO NOT simply copy the reference application's code, models, animation, UI layout, assets or branding.

Use its capabilities as a baseline, then engineer our own implementation.

All previous ORBIT requirements remain active.

---

# 1. NON-NEGOTIABLE REQUIREMENTS

1. Preserve my existing ORBIT application.
2. Preserve my datasets, trained models, research outputs, files and user preferences.
3. Keep the existing useful search, menu, navigation and theme functionality.
4. Improve the 3D scene substantially.
5. The 3D person must no longer look like a cartoon made from spheres, capsules or primitive blocks.
6. Support multiple people in the same scene.
7. Support different independent activities for each person.
8. Provide a configurable room with furniture.
9. Phone and laptop must connect to and control the SAME shared Command Centre session.
10. The phone must be able to act as the primary controller.
11. Both devices must reflect changes to the same scenario immediately.
12. Integrate real file transfer INSIDE the 3D Command Centre.
13. Display real transfer progress and communication graphs on both devices.
14. Allow changing simulation and processing parameters during a transfer.
15. Allow modifying the processing of received data after transmission without resending it.
16. Preserve original data and save derived versions separately.
17. Link 3D visualization, CSI analysis, DSP results and selected experiment state.
18. Build a scientifically honest simulation/replay/live-hardware separation.
19. Maintain excellent desktop and phone performance.
20. Use actual code and executable tests. No nonfunctional visual mockups.

---

# 2. FIRST: AUDIT THE REFERENCE AND EXISTING ORBIT

Read the reference ZIP as an external reference project.

Important files include:

- `frontend/src/components/three/Chamber.tsx`
- `frontend/src/components/Controls.tsx`
- `frontend/src/components/Pages.tsx`
- `frontend/src/types/index.ts`
- `backend/app/core/engine.py`
- `backend/app/simulation/channel.py`
- `backend/app/dsp/processing.py`
- `backend/app/detection/motion.py`

The reference uses React, React Three Fiber, Three.js, a Python backend, and simulated CSI.

Its README explicitly identifies all measurements as simulated and the 3D human as illustrative.

Inspect its pages and controls, including:
- Command Center
- Live Human Sensing
- 3D Hologram Studio
- CSI Explorer
- DSP Laboratory
- FFT Spectrum Analyzer
- Motion Analytics
- Experiment Studio
- Dataset Recordings
- System Diagnostics
- DSP Theory & Viva

Include its useful visualization, playback, recording, filtering and simulation capabilities in the ORBIT feature-parity audit.

Create a feature comparison matrix:

REFERENCE FEATURE
CURRENT ORBIT FEATURE
MISSING OR WEAKER BEHAVIOR
PROPOSED UPGRADE
IMPLEMENTATION STATUS
TEST EVIDENCE

Preserve existing ORBIT functionality before changing code.

Do not blindly import the reference implementation.

---

# 3. REBUILD THE 3D HUMAN WITH HIGH-QUALITY ANIMATION

The current primitive-looking person is not acceptable as the final experience.

Replace or substantially upgrade it with a realistic, properly rigged 3D human.

## Avatar quality

Use a suitable skinned human model with realistic body proportions and natural movement.

Prefer a locally bundled, properly licensed glTF/GLB asset with an animation skeleton, modern materials, and efficient rendering.

If using third-party 3D assets, check licensing and maintain required attribution.

Do not use copyrighted or proprietary models without appropriate rights.

The person should have:
- Realistic anatomical proportions.
- A distinct head, torso, arms, hands and legs.
- Natural shoulder, hip and knee motion.
- Smooth joint articulation.
- Balanced posture.
- Realistic walking cycles.
- Natural turning.
- Subtle idle movement.
- Breathing and weight-shift animations.
- Optional subtle head and hand movement.
- Smooth transitions between activities.
- Ground contact and foot-placement correction where feasible.
- Correct shadows and lighting.

Avoid:
- Capsule-person appearance.
- Floating feet.
- Sliding while walking.
- Mechanical limb swings.
- Constant unnatural shaking.
- Teleporting between positions.
- Two avatars occupying the same location.
- Repeated identical animations without variation.

## Animation system

Implement a proper animation state machine.

Supported states:
- IDLE
- STANDING STILL
- WALKING
- RUNNING
- TURNING
- ENTERING ROOM
- LEAVING ROOM
- HAND MOVEMENT
- PAUSED
- CUSTOM PATH

Use smooth crossfades between animation clips.

A standing person should remain spatially stationary while subtle idle animations may continue.

Walking must include visible translation through the room, not merely legs moving in place.

Animate movement along paths and rotate the character toward its direction of travel.

Use configurable walking speed.

Support pause, resume, stop and reset.

The motion system must respect the shared scenario timeline.

---

# 4. CRITICAL: EXACT MULTI-PERSON SCENARIO CONTROL

I want to select a scenario on my PHONE and see EXACTLY that scenario on BOTH my phone and laptop.

This is mandatory.

## Required scenarios

SCENARIO A:
Empty room.
Exactly 0 people.

SCENARIO B:
1 person standing still.
Exactly 1 person, stationary.

SCENARIO C:
1 person walking.
Exactly 1 person, moving naturally.

SCENARIO D:
2 people standing still.
Exactly 2 people, both stationary.

SCENARIO E:
2 people walking.
Exactly 2 people, both walking independently.

SCENARIO F:
1 person standing and 1 person walking.
Exactly 2 people, one stationary and one moving.

SCENARIO G:
1 person entering the room.

SCENARIO H:
1 person leaving the room.

SCENARIO I:
2 people entering or leaving.

SCENARIO J:
Fast movement.

SCENARIO K:
Hand or arm movement.

SCENARIO L:
Custom scenario with independent states per person.

All existing reference-video scenarios must remain available, including noisy Wi-Fi and clearly labelled through-wall SIMULATION experiments.

## Important implementation details

Each virtual person must have:
- Stable unique ID.
- Activity state.
- Position.
- Rotation.
- Animation state.
- Animation speed.
- Movement path.
- Visibility.
- Optional color/appearance selection.

Allow custom scenarios containing multiple avatars, with a practical configurable upper limit and appropriate performance safeguards.

At minimum, support the exact 0-, 1- and 2-person combinations listed above.

When I select "Two people walking", do not reuse one avatar or show one walking and another standing.

When I select "Two people standing", both must remain in position.

When I change from two people to one, remove or transition out the extra avatar without leaving a ghost model.

Allow clicking individual avatars to inspect or modify their simulated state.

Provide natural independent movements, not identical synchronized walking loops.

Make the scenario and avatar count deterministic and testable.

---

# 5. CUSTOMIZABLE 3D ROOM AND FURNITURE

I want more than an empty grid with a person.

Create an original configurable wireless sensing environment.

## Room elements

Support:
- Floor.
- Walls.
- Door.
- Windows where appropriate.
- Tables.
- Chairs.
- Desk.
- Sofa or bench.
- Shelves.
- Router/access point.
- Laptop or receiver station.
- Wi-Fi transmitter marker.
- CSI receiver marker.
- Measurement equipment.
- Optional partitions and obstacles.

Allow choosing different room presets:
- Modern research laboratory.
- Classroom.
- Home room.
- Office.
- Minimal sensing chamber.
- Dark radar chamber.

## Room editor

Allow:
- Add object.
- Remove object.
- Select object.
- Move object.
- Rotate object.
- Change size within safe bounds.
- Reset scene.
- Save room preset.
- Reload saved preset.

Use intuitive gizmos or drag controls where suitable.

Provide placement snapping, bounds and collision avoidance.

Keep router, TX and RX positions visible and editable in simulation mode.

The 3D environment must be significantly more attractive than the original reference while remaining scientifically understandable.

Do not imply that arbitrary virtual furniture geometries exactly model real RF propagation unless the simulator actually computes their effect.

---

# 6. PREMIUM 3D RENDERING AND VISUAL EFFECTS

Build a genuinely high-quality visual presentation.

Include:
- Physically based materials.
- Professional scene lighting.
- Soft shadows.
- Ambient occlusion where performance permits.
- Ground contact shadows.
- Balanced exposure.
- Smooth camera movements.
- Environment presets.
- Useful depth cues.
- Subtle volumetric atmosphere where efficient.
- Optional scanning sweeps.
- Wireless wave visualizations.
- Receiver/transmitter markers.
- Motion trails.
- Signal strength overlays.
- Spatial grid.
- Coordinate axes.
- Measurement labels.

Provide visualization modes:
1. Realistic human.
2. Hologram human.
3. Wireframe.
4. Skeleton.
5. RF/sensing overlay.

All modes must remain functional, but the realistic mode should be the premium default.

Avoid excessive neon glow, visual noise and distracting animations.

Do not copy the reference's exact rendering composition or color treatments.

## Camera controls

Support:
- Orbit rotation.
- Pan.
- Zoom.
- Reset.
- Front view.
- Back view.
- Side view.
- Top view.
- Isometric view.
- Follow selected person.
- Focus on transmitter.
- Focus on receiver.
- Fit whole room.
- Full-screen mode.
- Screenshot export.

Provide smooth interpolation between camera presets.

A camera that is locally controlled should not unexpectedly jump when another device changes its own viewing angle.

Offer an optional "Follow Presenter's Camera" mode to synchronize camera position when explicitly enabled.

---

# 7. MOST IMPORTANT: PHONE AND LAPTOP SHARE ONE COMMAND CENTRE

Implement a proper shared-session architecture.

When the phone connects to the laptop/server:

BOTH devices must display the same underlying live ORBIT Command Centre state.

The phone must not launch a separate, independent simulation that merely looks similar.

## Primary control

My preferred demonstration:

PHONE = PRIMARY CONTROLLER

LAPTOP = SYNCHRONIZED DISPLAY AND RECEIVER

I should be able to:

1. Open the Command Centre on my laptop.
2. Pair my phone using QR.
3. Open the same Command Centre on my phone.
4. Select "2 PEOPLE WALKING" on my phone.
5. Watch the laptop immediately change to two walking people.
6. Change the noise/filter/motion settings on my phone.
7. Watch the related laptop graphs and scenario update.
8. Start, pause or reset the experiment from my phone.
9. Continue using the laptop to inspect results.

This must work over the actual local network.

## Shared-session backend

Use the existing FastAPI backend and extend it with authenticated real-time synchronization, preferably WebSocket-based.

Create one server-authoritative experiment session.

Synchronize:
- Session ID.
- Experiment mode.
- Selected scenario.
- Avatar count.
- Individual avatar states.
- Room configuration.
- Simulation parameters.
- Playback state.
- Current experiment time.
- Active dataset ID.
- Selected DSP processing parameters.
- Experiment revision.
- Recording status.
- Transfer events.
- Shared chart data.
- Current prediction and source provenance.

Use versioned state snapshots, server revisions, command acknowledgements and reconnection recovery.

Reject stale updates safely.

Avoid duplicate actions after reconnection.

Protect the session with authenticated pairing and permissions.

## Control ownership

Default to the paired phone as the primary controller for the faculty demonstration.

Allow the laptop to request or regain control through an explicit authorized action.

Show which device currently controls the session.

Allow other connected devices to act as viewers when authorized.

Do not allow unpaired devices to control experiments.

## Rendering

The phone and laptop must share the SAME scenario, timestamps, data and experiment state.

They may render the 3D environment at different graphical quality levels according to device capability.

Each device may retain its own camera angle unless Follow Presenter is enabled.

The phone UI must be responsive and useful, not a broken miniature version of the desktop.

---

# 8. FILE TRANSFER INSIDE THE 3D COMMAND CENTRE

This is extremely important.

I want to transfer real data directly from the Command Centre without leaving the 3D workspace.

Do not make me navigate to a completely different application to send data.

Keep the existing Connect/Library functionality accessible, but integrate it into the Command Centre.

## Transfer panel

Add a compact expandable transfer panel beside or below the 3D scene.

Support:
- Send text.
- Send CSV.
- Send WAV/audio.
- Send images.
- Send videos.
- Send documents.
- Send ZIP files.
- Send compatible CSI recordings.
- Send other permitted files.

Allow both directions:
- Phone → Laptop.
- Laptop → Phone.

Use real device transport, not a simulated transfer animation.

## Required transfer UI on BOTH devices

Display:
- Sender.
- Receiver.
- Filename.
- File size.
- Transfer direction.
- Elapsed time.
- Bytes transferred.
- Percentage complete.
- Actual measured throughput.
- Transfer progress graph.
- Retries/errors where measurable.
- Upload/download status.
- Integrity verification.
- Completion status.
- Preview/Analyze action.

Show real transfer events on both the sender and receiver.

Avoid generating random numbers to make graphs look active.

## During transfer

I must be able to:
- Watch the 3D scene.
- Change simulated human scenarios.
- Rotate/zoom the camera.
- Inspect graphs.
- Change allowed processing parameters.
- Pause/resume/cancel the transfer when supported.
- See real-time updates on both devices.

File transfer should not freeze the 3D animation.

Do not stop the entire experiment merely because a file transfer starts.

Use independent processing and transfer jobs.

Prioritize responsive rendering and bounded memory usage.

---

# 9. POST-TRANSFER DATA MODIFICATION AND SECONDARY PROCESSING

This is another major requirement.

Suppose I send a dataset from my phone to the laptop.

The laptop receives and stores the original file.

After that, I want to change how the dataset is processed WITHOUT needing to send it again.

Example:

PHONE SENDS CSV OR CSI DATA
→ LAPTOP RECEIVES IT
→ BOTH SHOW TRANSFER COMPLETED
→ I SELECT HAMMING FIR ON MY PHONE
→ LAPTOP REPROCESSES THE RECEIVED DATA
→ BOTH DISPLAYS UPDATE
→ I CHANGE THE FILTER AGAIN
→ RESULTS UPDATE AGAIN.

The same should work with compatible audio and image processing.

## Required controls

Allow changing:
- Input dataset.
- Filter type.
- Filter order.
- Window function.
- Cutoff frequency.
- FFT size.
- Selected subcarrier.
- Time window.
- Smoothing settings.
- Model/algorithm where appropriate.
- Simulation parameters.

All values must be validated against the actual selected data.

If an operation requires retraining, a long computation or a recording restart, show that accurately.

Do not silently retrain or restart expensive processes.

## Data versioning

Never modify the uploaded original unexpectedly.

Maintain:
- Original data.
- Processed version A.
- Processed version B.
- Experiment parameters.
- Result graphs.
- Source provenance.

Allow Save, Export, Compare, Revert, Trash and Delete.

If a user edits a file while it is being transmitted, keep the in-flight transfer bound to a consistent snapshot and offer to send a new version afterward.

Do not corrupt an in-progress file to simulate live editing.

## Shared results

When processing completes, both laptop and phone must show the same result revision.

Show processing progress and errors.

If a new parameter change supersedes an older computation, prevent the older result from overwriting the newer one.

---

# 10. LIVE SCIENTIFIC GRAPHS — A COMPLETE COMMAND CENTRE

The 3D Command Centre should have significantly richer scientific visualization.

Do not crowd everything permanently onto one screen.

Use resizable, selectable chart panels and useful tabs.

## Communication charts

- Bytes transferred versus time.
- Transfer throughput versus time.
- Latency versus time where measured.
- Transfer completion.
- Retry counts.
- Transfer-event timeline.
- Integrity verification.

## CSI charts

- Raw CSI amplitude.
- Filtered CSI amplitude.
- CSI amplitude heatmap: subcarrier versus time.
- CSI phase where available.
- Subcarrier selection.
- Temporal FFT.
- Power spectral density.
- Motion score.
- Adaptive detection threshold.
- Packet-quality or validity indicators.
- Selected signal-window details.

## DSP charts

- Raw versus processed waveform.
- FIR/IIR response.
- FFT magnitude and phase.
- Spectrogram.
- Time-frequency comparison.
- Noise reduction comparison.
- Signal quality.

## Model results

- Presence prediction.
- Prediction confidence when supported.
- Model provenance.
- Feature values.
- False alarms/misses on labelled datasets.
- Saved results and comparison tables.

## AcousticLink charts

When using acoustic transfer:
- Encoded-bit view.
- Modulated waveform.
- Received microphone waveform.
- FFT.
- Spectrogram.
- Detected symbols.
- Frame errors.
- Encryption/decryption status.
- Successfully recovered payload.

## Graph interaction

Allow:
- Zoom.
- Pan.
- Cursor inspection.
- Hover values.
- Select time range.
- Select subcarrier.
- Synchronize cursors between related plots.
- Compare original and processed.
- Export PNG/CSV.
- Save graph configuration.
- Open fullscreen.
- Restore default view.

Always show units, source, timestamp and experiment type.

Use real chart samples from actual sources.

---

# 11. LINK 3D ACTIVITY AND SIGNAL VISUALIZATIONS

Make 3D and graph displays operate on one coordinated experiment timeline.

For simulation mode:

Changing from an empty room to a walking-person scenario should affect:
- Virtual avatar activity.
- Generated synthetic channel measurements.
- Corresponding DSP graphs.
- Motion score.
- Detection state.
- Event timeline.

For recorded CSI replay:

The selected recording and replay time should control signal graphs and classifier output.

3D animation may illustrate the recording's labelled scenario, but must not pretend that the original binary model recovered exact limb motion or multiple-person positions.

For live CSI mode:

Only display hardware-derived CSI and verified algorithm outputs as live measurements.

Do not generate fictional measured pose coordinates from an ordinary presence classifier.

Clearly label all source modes:

SIMULATION
RECORDED REPLAY
LIVE HARDWARE
ARCHIVED EXPERIMENT

These labels should be easy to see without looking intrusive.

---

# 12. SIMULATION CONTROL PARITY AND IMPROVEMENTS

Preserve every meaningful reference-video simulation function.

Include:
- Packet rate.
- OFDM subcarrier count.
- Noise amplitude.
- Motion intensity.
- Virtual movement speed.
- Multipath components.
- Channel attenuation/gain.
- Packet-loss probability in simulation.
- Detection sensitivity.
- Simulation speed.
- Sampling jitter.
- Baseline drift.
- Seed.
- DSP filter type.
- Filter order.
- Filter cutoffs.
- Scenario presets.

Support:
- Start.
- Pause.
- Resume.
- Stop.
- Reset.
- Previous scenario.
- Next scenario.
- Automatic scenario playback.
- Recording.
- Replay.
- Save experiment.
- Export results.

Parameter changes must have meaningful, testable effects.

Use a deterministic simulation seed so the same configuration can be reproduced.

Distinguish simulation packet loss from measured over-the-air Wi-Fi packet loss.

Provide classroom-friendly parameter presets.

---

# 13. COMMAND CENTRE INTERFACE DESIGN

I want premium professional software quality.

Keep the current ORBIT branding and existing useful navigation/search functionality.

Do not copy WI-SENSE X's exact interface.

## Suggested desktop composition

TOP:
ORBIT identity, active experiment, devices, connection health, recording, source mode.

CENTER:
Large high-quality interactive 3D room and humans.

RIGHT:
Scenario selection, selected-person controls, live state, processing controls.

BOTTOM:
Resizable scientific chart panels.

SIDE:
Navigation, saved experiments, datasets, tools.

FLOATING / COLLAPSIBLE:
File transfer, device pairing, activity log and quick actions.

Allow:
- Expand 3D viewer.
- Expand graph.
- Switch 3D-only/graph-only/split view.
- Collapse secondary controls.
- Full-screen presentation.

## Phone layout

The phone should use the same underlying session with a mobile-friendly interface.

Top:
Shared session and connection state.

Main:
Responsive 3D view.

Below:
Large touch-friendly scenario selector and controls.

Tabs:
DATA
GRAPHS
TRANSFER
PROCESSING
DEVICES.

Prioritize being able to select scenarios and control the laptop without tiny buttons.

## Design quality

Use:
- Clean hierarchy.
- Professional typography.
- Proper whitespace.
- Thoughtful panels.
- Smooth transitions.
- Clear control grouping.
- Excellent mobile responsiveness.
- Consistent icons.
- Subtle motion.
- Scientific chart legibility.

Avoid:
- Clutter.
- Cartoonish 3D.
- Excessive glowing borders.
- Tiny labels.
- Huge amounts of decorative text.
- Fake animations.
- Broken mobile layouts.

Preserve existing themes.

---

# 14. PERFORMANCE AND RESOURCE MANAGEMENT

The 3D scene must not freeze while uploading files or running DSP.

Use suitable rendering optimizations:
- Efficient glTF loading.
- Skeletal-animation reuse.
- Appropriate instancing.
- Level of detail.
- Shadow-quality controls.
- Adaptive device pixel ratio.
- Efficient particle systems.
- Chart downsampling.
- Throttled updates.
- Incremental processing.
- Background jobs.
- Memory cleanup.
- GPU resource disposal.
- Lazy loading.

Aim for responsive performance on common laptops and supported phones.

Measure actual frame rate and rendering performance rather than claiming a fixed FPS.

Provide performance presets:
- Performance.
- Balanced.
- High Quality.
- Ultra, where supported.

Gracefully fall back if WebGL or a particular effect is unavailable.

Respect reduced-motion accessibility settings.

---

# 15. REQUIRED BACKEND ARCHITECTURE

Reuse the existing Python/FastAPI infrastructure wherever possible.

Implement cohesive services for:

SharedSessionManager
ScenarioController
AvatarStateManager
RoomConfigurationManager
SimulationEngine
DataTransferManager
DatasetVersionManager
ProcessingJobManager
ChartStreamManager
RecordingManager
DevicePermissionManager

These are architectural responsibilities, not a requirement to create unnecessary duplicate classes.

Use appropriate REST endpoints for resource operations and authenticated WebSocket events for real-time state changes.

Each event should carry enough information to correlate it with:
- Session ID.
- Experiment ID.
- Revision.
- Event ID.
- Source.
- Event timestamp.
- Initiating device.
- Related transfer or processing job where relevant.

Keep file transfer metrics, simulation events and real CSI measurements in separate typed data streams.

Do not confuse network traffic with CSI.

Avoid stale updates, duplicate events and client-state divergence.

Implement recovery after disconnection.

---

# 16. IMPORTANT DEMONSTRATION SCENARIO

This is the exact demonstration I want to show my professor.

STEP 1:
Open ORBIT Command Centre on my laptop.

STEP 2:
Connect my phone via QR.

STEP 3:
Both screens show the same experiment.

STEP 4:
On my phone select "ONE PERSON STANDING."

Laptop shows exactly one stationary, realistic human.

STEP 5:
On my phone select "TWO PEOPLE WALKING."

Laptop shows exactly two different people moving naturally.

STEP 6:
Select "TWO PEOPLE STANDING."

Both stop walking and transition smoothly to standing.

STEP 7:
Change a synthetic noise or speed parameter on the phone.

Laptop graphs and animation reflect the updated simulation state.

STEP 8:
Select a CSV/CSI/audio file on the phone.

Send it to the laptop from INSIDE the Command Centre.

STEP 9:
Both phone and laptop show actual transmission progress and live graphs.

STEP 10:
Laptop receives the file and verifies integrity.

STEP 11:
Click "Analyze received data."

STEP 12:
Apply a DSP filter from the phone.

The laptop reprocesses the saved file.

STEP 13:
Both devices show updated processing graphs.

STEP 14:
Change filter or selected subcarrier again.

Both update without sending the file again.

STEP 15:
Save the processed version and open it in MATLAB or another compatible ORBIT studio.

STEP 16:
Show original versus processed results, the signal timeline, saved data and evidence.

STEP 17:
Switch to a verified recorded CSI experiment and demonstrate actual held-out presence-detection results.

STEP 18:
Explain which visualizations were simulated, which data were recorded and which metrics were actually measured.

The experience should be fluid, compelling and technically credible.

---

# 17. HARDWARE AND SCIENTIFIC LIMITATIONS

Do not make false sensing claims.

A physically transferred file does not automatically provide CSI.

The transfer graph measures network application behavior.

The CSI graph measures the wireless channel and requires recorded CSI data or supported capture hardware.

A binary human-presence model cannot automatically count people, recover exact skeletal pose or track limbs.

Simulation scenarios are allowed to explicitly contain multiple animated people.

These scenarios must be labelled as simulations.

Do not claim real multi-person detection unless an appropriate model has been trained and independently validated on suitable data.

Do not claim live Wi-Fi 6 CSI without actual compatible hardware, drivers and measurements.

Keep archived SAGE V3 and SmartCSI results scientifically separate from new experiments.

---

# 18. TESTS AND ACCEPTANCE CRITERIA

Implement real tests for:

## Multi-person scenes

- Empty = 0 avatars.
- One standing = 1 stationary avatar.
- One walking = 1 walking avatar.
- Two standing = 2 stationary avatars.
- Two walking = 2 moving avatars.
- Mixed = 1 walking + 1 stationary.
- Scenario changes do not leave ghost avatars.
- Avatars do not overlap improperly.
- Animations crossfade correctly.
- Room controls do not break the scene.

## Shared Command Centre

- Two connected clients see the same session.
- Phone changes scenario; laptop updates.
- Laptop reconnects; it recovers current state.
- Stale command is rejected or reconciled.
- Primary-controller permissions work.
- Unauthorized clients cannot control the session.
- Mobile layout is functional.

## Data transfer

- Phone sends file.
- Laptop receives exact bytes.
- Both show measured progress.
- Actual SHA-256 values match.
- Transfer continues during 3D animation.
- Scenario changes during transfer do not corrupt the file.
- Failed transfers recover appropriately.
- Save/Trash/Delete work.

## Reprocessing

- Original input is preserved.
- New filter produces a derived result.
- Changing a parameter produces a new result revision.
- Both clients display the same committed result.
- Older job results cannot overwrite newer processing results.
- Saved results reopen correctly.

## Visual quality

Capture screenshots and short demonstration recordings from:
- Desktop Command Centre.
- Phone Command Centre.
- One standing person.
- One walking person.
- Two standing people.
- Two walking people.
- Mixed activity.
- Room editor.
- Transfer in progress.
- Processing graphs.
- Replay.

Visually inspect:
- Human proportions.
- Walking quality.
- Lighting.
- Materials.
- Animation smoothness.
- Camera controls.
- Text readability.
- Mobile usability.
- Graph quality.
- Rendering glitches.

Run the existing automated frontend/backend tests and add new relevant coverage.

Never claim physical-device testing without actually performing it.

---

# 19. IMPLEMENTATION ORDER

MILESTONE A:
Audit existing ORBIT, WI-SENSE X reference and current UI. Produce the feature-parity matrix.

MILESTONE B:
Implement realistic rigged human and professional 3D room.

MILESTONE C:
Implement correct multi-person animations and scenario switching.

MILESTONE D:
Implement server-authoritative shared sessions with phone as primary controller.

MILESTONE E:
Integrate real data transfer into the Command Centre and show transfer events on both devices.

MILESTONE F:
Integrate post-transfer data processing, shared experiment state and data versioning.

MILESTONE G:
Integrate scientific graphs, linked timelines, CSI viewer and replay.

MILESTONE H:
Complete room editing, camera controls, animations and UI polish.

MILESTONE I:
Test desktop, Android, performance, security and recovery.

MILESTONE J:
Create a faculty demonstration and record actual test evidence.

Finish coherent, verifiable milestones.

Do not attempt one massive untested rewrite.

---

# 20. FINAL INSTRUCTIONS

This project is called ORBIT Ultimate.

The 3D Command Centre must be a flagship experience.

I want it to be substantially more realistic, visually polished, interactive and useful than the supplied reference.

**The minimum baseline is every demonstrated reference feature, including its 3D viewer, DSP laboratory, spectrum, motion analysis, experiments, recordings, diagnostics and theory.**

Above that, add:
- Realistic multi-person animation.
- Customizable 3D room.
- Shared phone/laptop controls.
- Real data transfer directly inside the Command Centre.
- Real transfer statistics displayed on both devices.
- Post-transfer reprocessing controlled from either authorized device.
- Shared scientific charts.
- CSI Window Microscope.
- Full data versioning.
- Integrated ORBIT experiments.
- Premium desktop/mobile usability.

Do not remove existing AcousticLink, encrypted sound communication, MATLAB, SDR, SAGE V3, SmartCSI, Soft Computing, camera or other ORBIT modules.

Preserve existing research results, datasets, user files, settings and functionality.

Update my canonical ORBIT project checklist after every milestone.

Report:
1. What was actually implemented.
2. Source files changed.
3. Tests run.
4. Screenshots and visual proof.
5. Physical hardware features still unverified.
6. Next incomplete milestone.

START NOW.

Inspect the current project and reference ZIP.

Then build the realistic 3D human, multi-person scene and shared Command Centre architecture.

Do not stop at documentation or mockups.
