# Original ORBIT 3D design & provenance

Implementation: `frontend/src/SpatialScene.tsx`, shared by Command center and 3D Sensing Studio. Actual WebGL2 via Three.js0.187.0 and React Three Fiber9.8.2, pinned in package-lock; MIT licenses. Runtime: modern WebGL2 browser / current Android System WebView. No network fonts, textures, models or external rendering service are needed.

All avatar geometry is procedural: capsules, spheres, articulated groups, a pelvis/neck, eye markers and optional hologram rings. Floor, walls, beacons and wireless rings are generated code. No reference video image, logo, room asset, human mesh, shader, stylesheet or exact layout is used. Orbit's own existing navigation and 18-theme token system are retained. The reference establishes functional requirements, not reusable artwork.

Camera supports genuine perspective orbit, pan and zoom. Presets move the actual camera; render styles change mesh materials. Reset moves the same camera without destroying the GPU context. Damping and resource disposal use OrbitControls lifecycle. Low/balanced/high DPR caps reduce device load; actual FPS is averaged over frames/time and may be throttled by hidden browser tabs. No universal60FPS promise.

Source contract: generated positions drive generated avatar translation. Recorded amplitude never reconstructs position, skeleton or identity; it shows an explicit illustration. Motion proxy is separate from trained inference. Held-out model results use existing backend prediction checks, only inside their saved window bounds; no training-seen substitution. A scene mesh is not evidence of through-wall detection.

The simulator approximates a complex multipath channel: static seeded paths plus moving path-length reflections, breathing-like phase, complex Gaussian noise, slow drift, an AGC-like midpoint step, jittered timestamps and missing packets. It is not a full standards-compliant Wi-Fi6 PHY. Static channel/noise are paired with same-seed empty calibration, not independent validation. Changing scene room/node sliders changes illustration only, clearly disclosed; channel controls are applied separately.

Exports: NPZ includes numeric arrays, generated ground-truth trajectories where available, saved synthetic calibration and JSON metadata with synthetic flag; JSON and CSV include source flags; PNG/WebM have a burned-in source header and illustration note. Import has compressed/expanded size, supported array names, duplicate names, dtype, shape and header limits and never enables pickle. Input files do not execute code.

Safety: manual 2D mode and context-loss fallback retain data/graphs, with return-to3D action. Scene video records only the visualization after explicit button press, no camera/microphone, maximum60s; tracks/timers stop on exit. Camera/medical functions remain separate consented experiments. Shared Library saves originals as new assets; no source datasets/models/keys are overwritten.

A phone-uploaded Orbit sensing NPZ can route from the shared Library to3Dreplay. File metadata and existing Library Simulation flags cannot be downgraded on this route. Derived saves link back to their Library parent. Arbitrary NPZ/image/audio files are not automatically treated as CSI or retinal evidence.

Animation transforms ease between displayed simulation samples using per-render-frame interpolation. Pause/scrub and reduced motion snap to the selected illustrative pose. This affects neither the original samples nor metrics/inference. Default camera fits portrait aspect/room size; Human focus intentionally crops closer. Expanded view includes shared transport and a host-compatible fallback.

Recorded data with no valid held-out decision withhold the avatar. A valid binary prediction controls an illustrative presence cue only; it never estimates count, pose or location. Simulation uses its explicit generated ground truth instead. This final visibility gate is covered by the fifth automated cursor/state test.
