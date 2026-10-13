import os
import json
import zipfile
import gc
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)

ZIP_PATH = "/content/drive/MyDrive/20MHz.zip"
EXTRACT_DIR = "/content/20MHz_data"
ROOT_DIR = os.path.join(EXTRACT_DIR, "20MHz")
WINDOW = 256
HOP = 128

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
        if bad_member:
            raise RuntimeError(f"Corrupt ZIP member: {bad_member}")
        archive.extractall(EXTRACT_DIR)

features = []
labels = []
groups = []
capture_rows = []
subcarrier_count = None
preview_trace = None

for folder, subfolders, filenames in os.walk(ROOT_DIR):
    subfolders[:] = [d for d in subfolders if d != "__MACOSX"]

    if "config.json" not in filenames:
        continue

    with open(os.path.join(folder, "config.json"), encoding="utf-8") as f:
        config = json.load(f)

    # Keep only captures marked as 802.11ax.
    if str(config.get("modulation", "")).lower() != "ax":
        continue

    people = config.get("people", {})
    present = people.get("present")

    if not isinstance(present, bool):
        print("Skipping capture with missing presence label:", folder)
        continue

    label = int(present)

    for filename in sorted(filenames):
        if not filename.endswith(".mat") or filename.startswith("._"):
            continue

        path = os.path.join(folder, filename)

        try:
            with h5py.File(path, "r") as f:
                if "capture" not in f:
                    continue
                raw = f["capture"][()]

            if raw.dtype.fields and {"real", "imag"}.issubset(raw.dtype.fields):
                amplitude = np.hypot(raw["real"], raw["imag"]).astype(np.float32)
            elif np.iscomplexobj(raw):
                amplitude = np.abs(raw).astype(np.float32)
            else:
                print("Skipping unsupported CSI data type:", path, raw.dtype)
                continue

            del raw
            gc.collect()

            if amplitude.ndim != 2:
                print("Skipping unexpected array shape:", path, amplitude.shape)
                continue

            # The inspected files use subcarriers x packets.
            if amplitude.shape[0] > amplitude.shape[1]:
                amplitude = amplitude.T

            if subcarrier_count is None:
                subcarrier_count = amplitude.shape[0]

            if amplitude.shape[0] != subcarrier_count:
                print("Skipping capture with different subcarrier count:", path)
                continue

            amplitude = np.nan_to_num(
                amplitude, nan=0.0, posinf=0.0, neginf=0.0
            )

            n_subcarriers, n_packets = amplitude.shape

            if n_packets < WINDOW:
                print("Skipping short capture:", path)
                continue

            if preview_trace is None:
                preview_trace = np.median(
                    amplitude, axis=0
                )[:min(3000, n_packets)]

            count = 0

            for start in range(0, n_packets - WINDOW + 1, HOP):
                segment = amplitude[:, start:start + WINDOW]

                # Simple amplitude features for every subcarrier.
                feature_vector = np.concatenate([
                    np.mean(segment, axis=1),
                    np.std(segment, axis=1),
                    np.mean(np.abs(np.diff(segment, axis=1)), axis=1),
                    np.percentile(segment, 90, axis=1)
                    - np.percentile(segment, 10, axis=1)
                ])

                features.append(feature_vector.astype(np.float32))
                labels.append(label)
                groups.append(os.path.relpath(path, ROOT_DIR))
                count += 1

            capture_rows.append({
                "capture": os.path.relpath(path, ROOT_DIR),
                "modulation": config.get("modulation"),
                "people_count": people.get("num"),
                "present": present,
                "moving": people.get("moving"),
                "packets": n_packets,
                "windows": count
            })

            print(
                "Loaded:", os.path.relpath(path, ROOT_DIR),
                "| presence:", label,
                "| windows:", count
            )

            del amplitude
            gc.collect()

        except Exception as error:
            print("Error reading", path, repr(error))

if not features:
    raise RuntimeError(
        "No CSI windows were created. Check file paths, configuration "
        "labels, modulation values and CSI shapes."
    )

X = np.vstack(features)
y = np.asarray(labels, dtype=np.int32)
groups = np.asarray(groups)
metadata = pd.DataFrame(capture_rows)

print("\nFeature matrix:", X.shape)
print("Independent capture files:", len(np.unique(groups)))
print("\nCapture metadata:")
display(metadata)

print("\nWindow counts by class:")
print(pd.Series(y).map({
    0: "No people",
    1: "People present"
}).value_counts())

os.makedirs("results", exist_ok=True)
metadata.to_csv("results/capture_metadata.csv", index=False)

plt.figure(figsize=(11, 4))
plt.plot(preview_trace)
plt.title("CSI amplitude example")
plt.xlabel("Packet index")
plt.ylabel("Median CSI amplitude")
plt.grid(True)
plt.tight_layout()
plt.savefig("results/csi_amplitude_example.png", dpi=150)
plt.show()

# Keep all windows from a capture file in the same train/test fold.
capture_labels = pd.DataFrame({
    "capture": groups,
    "label": y
}).drop_duplicates("capture")

class_counts = capture_labels.groupby("label")["capture"].nunique()
print("\nDistinct captures per class:")
print(class_counts)

if len(class_counts) < 2 or int(class_counts.min()) < 2:
    raise ValueError(
        "There are not enough independent capture files in both classes "
        "for grouped cross-validation. Inspect the metadata before training."
    )

n_splits = min(5, int(class_counts.min()))
cv = StratifiedGroupKFold(
    n_splits=n_splits, shuffle=True, random_state=42
)
splits = list(cv.split(X, y, groups=groups))

models = {
    "Logistic Regression": make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            random_state=42
        )
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=150,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    )
}

summary = []

for name, model in models.items():
    window_predictions = np.full(len(y), -1, dtype=np.int32)

    for fold, (train_idx, test_idx) in enumerate(splits, start=1):
        model.fit(X[train_idx], y[train_idx])
        window_predictions[test_idx] = model.predict(X[test_idx])
        print(f"{name}: completed fold {fold}/{n_splits}")

    true_capture = []
    predicted_capture = []

    for capture in np.unique(groups):
        indices = np.where(groups == capture)[0]
        values, votes = np.unique(
            window_predictions[indices], return_counts=True
        )
        true_capture.append(int(y[indices][0]))
        predicted_capture.append(int(values[np.argmax(votes)]))

    accuracy = accuracy_score(true_capture, predicted_capture)
    f1 = f1_score(true_capture, predicted_capture, zero_division=0)

    print("\nModel:", name)
    print("Capture-level accuracy:", round(accuracy, 4))
    print("Capture-level F1-score:", round(f1, 4))
    print(classification_report(
        true_capture,
        predicted_capture,
        labels=[0, 1],
        target_names=["No people", "People present"],
        zero_division=0
    ))

    matrix = confusion_matrix(
        true_capture, predicted_capture, labels=[0, 1]
    )
    ConfusionMatrixDisplay(
        matrix, display_labels=["No people", "People present"]
    ).plot()
    plt.title(name + " - capture-level confusion matrix")
    plt.tight_layout()

    safe_name = name.lower().replace(" ", "_")
    plt.savefig(f"results/confusion_matrix_{safe_name}.png", dpi=150)
    plt.show()

    summary.append({
        "model": name,
        "capture_level_accuracy": accuracy,
        "capture_level_f1": f1,
        "capture_files": len(true_capture)
    })

summary_df = pd.DataFrame(summary).sort_values(
    "capture_level_f1", ascending=False
)
display(summary_df)
summary_df.to_csv("results/model_comparison.csv", index=False)

print("\nSaved plots and tables in the results/ folder.")
print("This is normal presence detection, not through-wall detection.")
