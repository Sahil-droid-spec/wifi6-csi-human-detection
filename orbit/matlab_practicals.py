"""Fixed, auditable same-input MATLAB/NumPy/SciPy DSP cross-check."""

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from fastapi import HTTPException, Request
from scipy import signal
from scipy.io import savemat

from .matlab_lab import _active, matlab_executable

SCRIPT = """load('input.mat');
F=fft(x);H=fft(x);m=zeros(size(x));m(1)=1;m(2:numel(x)/2)=2;m(numel(x)/2+1)=1;
analytic=ifft(H.*m);
A=[0 1;-2 -2];B=[0;1];C=[1 0];imp=zeros(size(t));step=zeros(size(t));
for k=1:numel(t),E=expm(A*t(k));imp(k)=C*E*B;step(k)=C*(A\\(E-eye(2)))*B;end
r=struct('fourier_real',real(F),'fourier_imag',imag(F),'fir',filter(b,1,x),...
'butterworth',filter(bi,ai,x),'hilbert_imag',imag(analytic),...
'linear',conv(x(1:8),h),'circular',real(ifft(fft(x(1:8),16).*fft(h,16))),...
'quantized',min(15,max(0,floor((x+1)/.125)))*.125-1+.0625,...
'laplace_impulse',imp,'laplace_step',step,'version',version);
fid=fopen('result.json','w');fprintf(fid,'%s',jsonencode(r));fclose(fid);
"""


def compare(workspace: Path):
    exe = matlab_executable()
    if not exe:
        raise HTTPException(
            503, "Install licensed MATLAB or use the Python practicals and exported scripts."
        )
    if not _active.acquire(blocking=False):
        raise HTTPException(409, "Wait for the current MATLAB operation to finish.")
    try:
        x = 0.8 * np.sin(2 * np.pi * 7 * np.arange(128) / 100)
        h = np.array([0.25, 0.5, 0.25])
        b = signal.firwin(63, 20, fs=100, window="hamming")
        bi, ai = signal.butter(4, 20, fs=100)
        t = np.linspace(0, 2, 201)
        _, imp = signal.impulse(([1], [1, 2, 2]), T=t)
        _, step = signal.step(([1], [1, 2, 2]), T=t)
        expected = {
            "fourier_real": np.fft.fft(x).real,
            "fourier_imag": np.fft.fft(x).imag,
            "fir": signal.lfilter(b, [1], x),
            "butterworth": signal.lfilter(bi, ai, x),
            "hilbert_imag": signal.hilbert(x).imag,
            "linear": np.convolve(x[:8], h),
            "circular": np.fft.ifft(np.fft.fft(x[:8], 16) * np.fft.fft(h, 16)).real,
            "quantized": np.clip(np.floor((x + 1) / 0.125), 0, 15) * 0.125 - 1 + 0.0625,
            "laplace_impulse": imp,
            "laplace_step": step,
        }
        with tempfile.TemporaryDirectory(prefix="matlab-practical-", dir=workspace) as tmp:
            folder = Path(tmp)
            savemat(folder / "input.mat", {"x": x, "h": h, "b": b, "bi": bi, "ai": ai, "t": t})
            (folder / "orbit_check.m").write_text(SCRIPT, encoding="utf-8")
            result = subprocess.run(
                [exe, "-batch", "orbit_check"], cwd=folder, capture_output=True, timeout=180
            )
            if result.returncode != 0 or not (folder / "result.json").is_file():
                raise ValueError(
                    "MATLAB did not complete. Check its license/startup on the laptop and retry; Python results remain available."
                )
            actual = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        outputs = []
        for name, ref in expected.items():
            values = np.asarray(actual[name], float).reshape(-1)
            if values.shape != ref.shape or not np.isfinite(values).all():
                raise ValueError("MATLAB returned incompatible output dimensions.")
            outputs.append(
                {
                    "operation": name,
                    "samples": len(ref),
                    "max_abs_difference": float(np.max(abs(ref - values))),
                }
            )
        return {
            "matlab_version": actual["version"],
            "comparisons": outputs,
            "protocol": "One fixed generated 128-sample sine, identical coefficients and inputs in MATLAB and NumPy/SciPy. FIR/Butterworth compare filtering with the same Python-designed coefficients; they do not benchmark independent filter design. Laplace uses equivalent state-space exponential response. Not hardware validation.",
        }
    except subprocess.TimeoutExpired as exc:
        raise ValueError("MATLAB exceeded 180 seconds. Close other jobs and retry.") from exc
    finally:
        _active.release()


def install(app, ctx):
    @app.post("/api/matlab/practicals")
    def run(request: Request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Run licensed MATLAB on the laptop.")
        return compare(ctx["data"])
