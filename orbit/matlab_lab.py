"""Bounded MATLAB batch experiments using only Orbit-owned scripts."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from threading import Lock
from typing import Literal

import numpy as np
from fastapi import HTTPException, Request
from scipy import ndimage, signal

_active = Lock()

SCRIPT = r"""
load('input.mat','x','b');
switch 'ORBIT_MODE'
case 'fir'
    values = filter(b,1,x);
case 'image'
    kernel = [1 2 1;2 4 2;1 2 1]/16;
    smooth = imfilter(x,kernel,'replicate','same');
    edges = imfilter(smooth,[-1 0 1;-2 0 2;-1 0 1],'replicate','same');
    values = cat(3,smooth,abs(edges),double(abs(edges)>0.5));
case 'simulink'
    name = 'orbit_gain_comparison';
    new_system(name);
    cleanup = onCleanup(@()close_system(name,0));
    add_block('simulink/Sources/Digital Clock',[name '/Input'],'SampleTime','1');
    add_block('simulink/Math Operations/Gain',[name '/Gain'],'Gain','2.5');
    add_block('simulink/Sinks/To Workspace',[name '/Output'],'VariableName','y','SaveFormat','Array');
    add_line(name,'Input/1','Gain/1');
    add_line(name,'Gain/1','Output/1');
    in = Simulink.SimulationInput(name);
    in = in.setModelParameter('SolverType','Fixed-step','Solver','FixedStepDiscrete',...
        'FixedStep','1','StartTime','0','StopTime',num2str(numel(x)-1));
    out = sim(in);
    values = out.get('y');
    values = values(:).';
end
fid = fopen('result.json','w');
fprintf(fid,'%s',jsonencode(struct('values',values,'version',version)));
fclose(fid);
"""


def matlab_executable() -> str | None:
    if path := shutil.which("matlab"):
        return path
    if os.name == "nt":
        root = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "MATLAB"
        for release in sorted(root.glob("R20*"), reverse=True):
            path = release / "bin" / "matlab.exe"
            if path.is_file():
                return str(path)
    return None


def compare(executable: str, workspace: Path, mode: str, audio: tuple | None = None) -> dict:
    from scipy.io import savemat

    b = np.array([0.25, 0.5, 0.25])
    t = np.arange(64)
    x = np.sin(2 * np.pi * t / 16) + 0.24 * np.cos(2 * np.pi * t / 4)
    if audio is not None:
        x, b = audio
    if mode == "fir":
        expected = signal.lfilter(b, [1], x)
    elif mode == "simulink":
        x = t.astype(float)
        expected = 2.5 * x
    elif mode == "image":
        rows, cols = np.mgrid[:32, :32]
        x = (cols / 100) + ((rows > 7) & (rows < 24) & (cols > 8) & (cols < 24)) * 0.55
        smooth = ndimage.correlate(
            x, np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]]) / 16, mode="nearest"
        )
        edges = np.abs(
            ndimage.correlate(smooth, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], mode="nearest")
        )
        expected = np.dstack((smooth, edges, edges > 0.5))
    else:
        raise ValueError("Choose a listed MATLAB experiment.")
    prefs = workspace / "matlab-prefs"
    prefs.mkdir(exist_ok=True)
    env = {**os.environ, "MATLAB_PREFDIR": str(prefs)}
    with tempfile.TemporaryDirectory(prefix="orbit-matlab-", dir=workspace) as directory:
        folder = Path(directory)
        savemat(folder / "input.mat", {"x": x, "b": b})
        (folder / "orbit_run.m").write_text(SCRIPT.replace("ORBIT_MODE", mode), encoding="utf-8")
        command = [
            executable,
            *(["-wait"] if os.name == "nt" else []),
            "-batch",
            "run('orbit_run.m')",
        ]
        proc = subprocess.run(
            command,
            cwd=folder,
            env=env,
            capture_output=True,
            timeout=150,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if proc.returncode or not (folder / "result.json").is_file():
            raise RuntimeError("MATLAB batch or toolbox initialization failed.")
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    actual = np.asarray(result["values"], dtype=float)
    if actual.shape != expected.shape or not np.isfinite(actual).all():
        raise RuntimeError("MATLAB returned an unexpected sample layout.")
    delta = np.abs(actual - expected)
    return {
        "mode": mode,
        "source": "Library WAV · channel 1" if audio is not None else "Generated comparison input",
        "synthetic": None if audio is not None else True,
        "matlab_version": result["version"],
        "input": x.tolist(),
        "python": expected.tolist(),
        "matlab": actual.tolist(),
        "shape": list(actual.shape),
        "max_abs_difference": float(delta.max()),
        "protocol": "Same input and coefficients or gain; all returned values compared against NumPy/SciPy.",
    }


def install(app, ctx):
    @app.get("/api/matlab/status")
    def status(request: Request):
        return {"available": bool(matlab_executable()), "can_run": ctx["local_request"](request)}

    def run_batch(request, mode, audio=None):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Run MATLAB Studio from the laptop.")
        exe = matlab_executable()
        if not exe:
            raise HTTPException(
                503, "Install a licensed MATLAB on this laptop to run this experiment."
            )
        if not _active.acquire(blocking=False):
            raise HTTPException(409, "Wait for the current MATLAB run to finish.")
        try:
            return compare(exe, ctx["data"], mode, audio)
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(
                504, "MATLAB did not finish. Check its license and try again."
            ) from exc
        except (OSError, RuntimeError) as exc:
            raise HTTPException(
                503, "Open MATLAB on the laptop and check its license and toolbox."
            ) from exc
        finally:
            _active.release()

    @app.post("/api/matlab/{mode}")
    def run(mode: Literal["fir", "image", "simulink"], request: Request):
        return run_batch(request, mode)

    @app.post("/api/matlab/audio/{ident}")
    def run_wav(ident: str, request: Request):
        from .audio_studio import MAX_WAV, read_wav

        if not ctx["local_request"](request):
            raise HTTPException(403, "Run MATLAB Studio from the laptop.")
        row = ctx["get"]("media", ident)
        if row.get("trashed") or row["type"] != "audio/wav":
            raise HTTPException(404, "Choose a saved WAV from the Library.")
        path = ctx["data"] / row["path"]
        try:
            with path.open("rb") as file:
                raw = file.read(MAX_WAV + 1)
        except FileNotFoundError as exc:
            raise HTTPException(404, "The saved audio file is unavailable.") from exc
        if len(raw) > MAX_WAV:
            raise HTTPException(413, "Choose a WAV smaller than 12 MiB.")
        rate, x = read_wav(raw)
        coefficients = signal.firwin(63, 1200, window="hamming", fs=rate)
        result = run_batch(request, "fir", (x[:2048, 0], coefficients))
        return {
            **result,
            "sample_rate": rate,
            "library_id": ident,
            "sha256": row["sha256"],
            "protocol": "Channel 1, first 2048 samples or fewer; same 63-tap, 1200 Hz Hamming FIR and zero initial state in Python and MATLAB.",
        }
