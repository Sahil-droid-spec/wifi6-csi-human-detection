import os
import json
import zipfile
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ZIP_PATH = "/content/drive/MyDrive/20MHz.zip"
EXTRACT_DIR = "/content/20MHz_data"
ROOT_DIR = os.path.join(EXTRACT_DIR, "20MHz")

try:
    from google.colab import drive
    if not os.path.isdir("/content/drive/MyDrive"):
        drive.mount("/content/drive")
except ImportError:
    pass

if not os.path.isdir(ROOT_DIR):
    if not os.path.isfile(ZIP_PATH):
        raise FileNotFoundError(f"Dataset ZIP not found: {ZIP_PATH}")

    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad_member = archive.testzip()
        print("ZIP integrity (None means OK):", bad_member)
        if bad_member:
            raise RuntimeError(f"Corrupt ZIP member: {bad_member}")
        archive.extractall(EXTRACT_DIR)

rows = []
sample_path = None
sample_config = None

for folder, subfolders, filenames in os.walk(ROOT_DIR):
    subfolders[:] = [d for d in subfolders if d != "__MACOSX"]

    if "config.json" not in filenames:
        continue

    with open(os.path.join(folder, "config.json"), encoding="utf-8") as f:
        config = json.load(f)

    people = config.get("people", {})

    for filename in sorted(filenames):
        if not filename.endswith(".mat") or filename.startswith("._"):
            continue

        path = os.path.join(folder, filename)

        with h5py.File(path, "r") as f:
            if "capture" not in f:
                print("Skipping file without capture:", path)
                continue
            shape = f["capture"].shape
            dtype = str(f["capture"].dtype)

        rows.append({
            "capture": os.path.relpath(path, ROOT_DIR),
            "modulation": config.get("modulation"),
            "bandwidth_MHz": config.get("bandwidth"),
            "present": people.get("present"),
            "people_count": people.get("num"),
            "moving": people.get("moving"),
            "shape": str(shape),
            "dtype": dtype
        })

        if sample_path is None:
            sample_path = path
            sample_config = config

df = pd.DataFrame(rows)

print("Capture files found:", len(df))
display(df)

if df.empty:
    raise RuntimeError("No usable capture files were found.")

print("\nModulation and label summary:")
display(df.groupby(
    ["modulation", "present", "people_count", "moving"],
    dropna=False
).size().rename("captures").reset_index())

print("\nSample capture:", sample_path)
print("Its own configuration:")
print(json.dumps(sample_config, indent=2))

with h5py.File(sample_path, "r") as f:
    raw = f["capture"][()]

if raw.dtype.fields and {"real", "imag"}.issubset(raw.dtype.fields):
    amplitude = np.hypot(raw["real"], raw["imag"]).astype(np.float32)
elif np.iscomplexobj(raw):
    amplitude = np.abs(raw).astype(np.float32)
else:
    raise TypeError(f"Unexpected CSI format: {raw.dtype}")

if amplitude.shape[0] > amplitude.shape[1]:
    amplitude = amplitude.T

trace = np.median(amplitude, axis=0)

plt.figure(figsize=(11, 4))
plt.plot(trace[:min(3000, len(trace))])
plt.title("CSI amplitude from one capture")
plt.xlabel("Packet index")
plt.ylabel("Median CSI amplitude")
plt.grid(True)
plt.tight_layout()
os.makedirs("results", exist_ok=True)
plt.savefig("results/csi_amplitude_example.png", dpi=150)
plt.show()

print("CSI amplitude shape:", amplitude.shape)
