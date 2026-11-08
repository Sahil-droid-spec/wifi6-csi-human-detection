"""Bounded, reproducible DSP practicals. Generated signals are always simulations."""

import time

import numpy as np
from pydantic import BaseModel, Field
from scipy import signal


class Practical(BaseModel):
    kind: str = "sampling"
    frequency_hz: float = Field(default=30, gt=0, le=2000, allow_inf_nan=False)
    sample_rate_hz: float = Field(default=100, ge=10, le=16000, allow_inf_nan=False)
    duration_s: float = Field(default=1, ge=0.05, le=5, allow_inf_nan=False)
    bits: int = Field(default=4, ge=2, le=16)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    ebn0_db: float = Field(default=5, ge=-10, le=30, allow_inf_nan=False)
    modulation: str = "BPSK"
    samples: int = Field(default=4096, ge=256, le=32768)
    window: str = "hamming"
    filter_type: str = "lowpass"
    amplitude: float = Field(default=0.85, gt=0, le=2, allow_inf_nan=False)
    signal_shape: str = "sine"
    numerator: list[float] = Field(default=[1], min_length=1, max_length=5)
    denominator: list[float] = Field(default=[1, 2, 2], min_length=2, max_length=6)


def spectrum(x, rate):
    values = np.fft.rfft(x)
    magnitude = abs(values)
    valid = magnitude > max(float(magnitude.max()) * 1e-8, 1e-12)
    return {
        "frequency_hz": np.fft.rfftfreq(len(x), 1 / rate).tolist(),
        "magnitude": magnitude.tolist(),
        "phase_rad": [float(p) if v else None for p, v in zip(np.angle(values), valid)],
    }


def modulation(body: Practical):
    """Known bit reference, Es normalized, Eb/N0 includes OFDM CP overhead."""
    rng = np.random.default_rng(body.seed)
    mode = body.modulation
    if mode not in ("ASK", "BPSK", "DPSK", "QPSK", "16QAM", "OFDM"):
        raise ValueError("Choose ASK, BPSK, DPSK, QPSK, 16QAM or OFDM.")
    k = 4 if mode == "16QAM" else 2 if mode in ("QPSK", "OFDM") else 1
    count = body.samples // (k * 64) * (k * 64)
    bits = rng.integers(0, 2, count).astype(np.uint8)
    ebn0 = 10 ** (body.ebn0_db / 10)
    if mode in ("BPSK", "ASK", "DPSK"):
        symbols = 2 * bits.astype(float) - 1
        if mode == "ASK":
            symbols = np.sqrt(2) * bits.astype(float)
        if mode == "DPSK":
            symbols = np.r_[1, np.cumprod(symbols)]
        # Unit-energy rectangular pulse; matched filter sums its 8 samples.
        wave = np.repeat(symbols, 8) / np.sqrt(8)
        noisy = wave + rng.normal(0, np.sqrt(1 / (2 * ebn0)), len(wave))
        matched = noisy.reshape(-1, 8).sum(axis=1) / np.sqrt(8)
        recovered = matched > (np.sqrt(2) / 2 if mode == "ASK" else 0)
        if mode == "DPSK":
            recovered = matched[1:] * matched[:-1] > 0
    else:
        grouped = bits.reshape(-1, k)
        if k == 2:
            symbols = (
                (2 * grouped[:, 0].astype(float) - 1) + 1j * (2 * grouped[:, 1].astype(float) - 1)
            ) / np.sqrt(2)
        else:
            levels = np.array([-3, -1, 3, 1]) / np.sqrt(10)
            symbols = (
                levels[2 * grouped[:, 0] + grouped[:, 1]]
                + 1j * levels[2 * grouped[:, 2] + grouped[:, 3]]
            )
        wave = symbols.copy()
        if mode == "OFDM":
            blocks = np.fft.ifft(symbols.reshape(-1, 64), norm="ortho")
            wave = np.concatenate([blocks[:, -16:], blocks], axis=1).reshape(-1)
        energy_per_bit = float(np.sum(abs(wave) ** 2) / count)
        sigma = np.sqrt(energy_per_bit / (2 * ebn0))
        noisy = wave + sigma * (rng.normal(size=len(wave)) + 1j * rng.normal(size=len(wave)))
        matched = (
            np.fft.fft(noisy.reshape(-1, 80)[:, 16:], norm="ortho").reshape(-1)
            if mode == "OFDM"
            else noisy
        )
        if k == 2:
            recovered = np.column_stack([matched.real > 0, matched.imag > 0]).reshape(-1)
        else:
            indices = np.arange(4)
            i = np.argmin(abs(matched.real[:, None] - levels), axis=1)
            q = np.argmin(abs(matched.imag[:, None] - levels), axis=1)
            recovered = np.column_stack(
                [indices[i] // 2, indices[i] % 2, indices[q] // 2, indices[q] % 2]
            ).reshape(-1)
    errors = int(np.count_nonzero(recovered != bits))
    return {
        "bit_errors": errors,
        "bit_count": count,
        "ber": errors / count,
        "transmitted_bits": bits[:256].tolist(),
        "recovered_bits": recovered[:256].astype(int).tolist(),
        "input": np.real(wave[:512]).tolist(),
        "output": np.real(noisy[:512]).tolist(),
        "constellation": [
            [float(v.real), float(v.imag)] for v in np.asarray(matched, dtype=complex)[:512]
        ],
        "ebn0_db": body.ebn0_db,
        "protocol": f"Generated {mode}; seed {body.seed}; {count} known bits, AWGN at specified Eb/N0. BER includes every recovered payload bit. OFDM uses 64 carriers + 16-sample CP, no pilots/coding/synchronization; not IEEE Wi-Fi implementation.",
    }


def run(body: Practical):
    began = time.perf_counter()
    fs = body.sample_rate_hz
    n = int(fs * body.duration_s)
    if not 8 <= n <= 32768:
        raise ValueError("Choose sample rate and duration giving 8–32768 samples.")
    t = np.arange(n) / fs
    x = body.amplitude * np.sin(2 * np.pi * body.frequency_hz * t)
    result = {"source": "SIMULATION", "synthetic": True, "settings": body.model_dump()}
    if body.kind == "signals":
        if body.signal_shape == "cosine":
            x = body.amplitude * np.cos(2 * np.pi * body.frequency_hz * t)
        elif body.signal_shape == "step":
            x = body.amplitude * (t >= body.duration_s / 2)
        elif body.signal_shape == "ramp":
            x = body.amplitude * np.maximum(0, t - body.duration_s / 2)
        elif body.signal_shape == "exponential":
            x = body.amplitude * np.exp(-2 * t)
        elif body.signal_shape != "sine":
            raise ValueError("Choose sine, cosine, step, ramp or exponential.")
        result.update(
            times=t[:2048].tolist(),
            input=x[:2048].tolist(),
            spectrum=spectrum(x, fs),
            protocol="Generated mathematical signal evaluated on a finite sample grid. Step/ramp begin halfway through the record; exponential is A exp(-2t). This is a sampled representation, not a physical continuous-time measurement.",
        )
    elif body.kind == "modulation":
        result.update(modulation(body))
        result["ber_curve"] = [
            {
                "ebn0_db": db,
                **{
                    k: v
                    for k, v in modulation(body.model_copy(update={"ebn0_db": db})).items()
                    if k in ("bit_errors", "bit_count", "ber")
                },
            }
            for db in (-2, 0, 2, 5, 8, 12)
        ]
    elif body.kind == "laplace":
        b, a = np.asarray(body.numerator, float), np.asarray(body.denominator, float)
        if not np.isfinite(b).all() or not np.isfinite(a).all() or a[0] == 0 or len(b) > len(a):
            raise ValueError(
                "Use finite proper continuous-time coefficients and a nonzero leading denominator."
            )
        system = signal.TransferFunction(b, a)
        times = np.linspace(0, body.duration_s, 512)
        _, impulse = signal.impulse(system, T=times)
        _, step = signal.step(system, T=times)
        if not np.isfinite(impulse).all() or not np.isfinite(step).all():
            raise ValueError("Reduce duration or use a stable bounded system.")
        result.update(
            times=times.tolist(),
            input=impulse.tolist(),
            output=step.tolist(),
            poles=[[float(v.real), float(v.imag)] for v in system.poles],
            zeros=[[float(v.real), float(v.imag)] for v in system.zeros],
            stable=bool(np.all(system.poles.real < 0)),
            protocol="Continuous-time Laplace H(s)=B(s)/A(s), SciPy impulse and unit-step response; poles in s-plane (1/s). Stability refers to proper rational LTI system, not a measured device.",
        )
    elif body.kind == "quantisation":
        step = 2 / (2**body.bits)
        q = np.clip(np.floor((x + 1) / step), 0, 2**body.bits - 1) * step - 1 + step / 2
        error = x - q
        mse = float(np.mean(error**2))
        result.update(
            times=t[:2048].tolist(),
            input=x[:2048].tolist(),
            output=q[:2048].tolist(),
            error=error[:2048].tolist(),
            mse=mse,
            snr_db=float(10 * np.log10(np.mean(x * x) / mse)) if mse > 0 else None,
            clipping_samples=int(np.count_nonzero(abs(x) >= 1)),
            step=step,
            protocol=f"Uniform mid-rise quantizer, range [-1,1), {body.bits} bits; MSE and reference/error power SNR computed over all {n} generated samples.",
        )
    elif body.kind == "sampling":
        dense_t = np.linspace(0, body.duration_s, 2048, endpoint=False)
        dense = body.amplitude * np.sin(2 * np.pi * body.frequency_hz * dense_t)
        # Bound finite sinc synthesis matrix rather than allocating O(n²).
        reconstruction = np.zeros(len(dense_t))
        for offset in range(0, n, 256):
            reconstruction += (
                np.sinc(fs * (dense_t[:, None] - t[None, offset : offset + 256]))
                @ x[offset : offset + 256]
            )
        result.update(
            times=t[:2048].tolist(),
            input=x[:2048].tolist(),
            dense_times=dense_t.tolist(),
            dense=dense.tolist(),
            output=reconstruction.tolist(),
            aliased_frequency_hz=abs((body.frequency_hz + fs / 2) % fs - fs / 2),
            protocol=f"Generated sine {body.frequency_hz} Hz sampled at {fs} Hz. Finite sinc reconstruction uses all {n} samples; boundary error is expected. Alias formula maps frequency to [-fs/2,fs/2).",
        )
    elif body.kind in ("fourier", "hilbert", "fir"):
        if body.kind == "hilbert":
            analytic = signal.hilbert(x)
            result.update(
                output=abs(analytic)[:2048].tolist(),
                quadrature=analytic.imag[:2048].tolist(),
                protocol="SciPy discrete analytic signal; magnitude is Hilbert envelope. Finite-record edge effects apply.",
            )
        elif body.kind == "fir":
            if (
                body.window not in ("hann", "hamming", "blackman", "kaiser")
                or body.filter_type not in ("lowpass", "highpass")
                or body.frequency_hz >= fs / 2
            ):
                raise ValueError("Choose a supported window, LP/HP, and cutoff below Nyquist.")
            window = ("kaiser", 8) if body.window == "kaiser" else body.window
            taps = signal.firwin(
                63, body.frequency_hz, fs=fs, window=window, pass_zero=body.filter_type == "lowpass"
            )
            out = signal.lfilter(taps, [1], x)
            f, h = signal.freqz(taps, fs=fs, worN=512)
            result.update(
                output=out[:2048].tolist(),
                taps=taps.tolist(),
                response_hz=f.tolist(),
                response_db=(20 * np.log10(abs(h).clip(1e-12))).tolist(),
                protocol="63-tap SciPy windowed FIR. Causal zero-state filtering, nominal 31-sample delay. Response is computed from actual coefficients.",
            )
        else:
            result.update(
                output=np.fft.irfft(np.fft.rfft(x), n=n)[:2048].tolist(),
                reconstruction_max_error=float(np.max(abs(np.fft.irfft(np.fft.rfft(x), n=n) - x))),
                protocol=f"NumPy {n}-point DFT and inverse, same generated samples. Phase withheld below relative magnitude 1e-8.",
            )
        result.update(times=t[:2048].tolist(), input=x[:2048].tolist(), spectrum=spectrum(x, fs))
    else:
        raise ValueError(
            "Choose sampling, quantisation, Fourier, Hilbert, FIR, Laplace or modulation."
        )
    return {**result, "elapsed_ms": (time.perf_counter() - began) * 1000}
