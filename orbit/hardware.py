"""Explicit laptop-only adapter operations. No ordinary-NIC CSI claim."""

import importlib.util
import io
import ipaddress
import json
import os
import re
import socket
import subprocess
import time

import numpy as np
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field


def wifi_status():
    if os.name != "nt":
        return {
            "state": "HARDWARE UNVERIFIED",
            "next_step": "Use your OS Wi-Fi connection diagnostics.",
        }
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            timeout=6,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        output = result.stdout.decode(errors="replace")
        fields = {}
        for label, key in [
            ("Radio type", "radio_type"),
            ("Signal", "signal_percent"),
            ("Receive rate (Mbps)", "receive_link_mbps"),
            ("Transmit rate (Mbps)", "transmit_link_mbps"),
        ]:
            match = re.search(
                r"^\s*" + re.escape(label) + r"\s*:\s*([^\r\n]+)", output, re.M | re.I
            )
            fields[key] = match.group(1).strip() if match else None
        return {
            "state": "AVAILABLE" if fields["radio_type"] else "HARDWARE UNVERIFIED",
            **fields,
            "protocol": "Windows-reported laptop link snapshot, not phone RSSI or an independent RF measurement. Signal is an OS percentage, not dBm. Link rates are not application throughput. No SSID or MAC address is retained.",
            "next_step": "If fields are absent, check the laptop WLAN and Windows location/privacy permission yourself.",
        }
    except (OSError, subprocess.TimeoutExpired):
        return {
            "state": "ERROR",
            "next_step": "Open Windows Wi-Fi diagnostics; netsh was unavailable or timed out.",
        }


class SDR(BaseModel):
    device_index: int = Field(default=0, ge=0, le=15)
    sample_rate_hz: int = Field(default=48000, ge=16000, le=256000)
    frequency_hz: float = Field(default=100e6, ge=1e6, le=6e9, allow_inf_nan=False)
    frames: int = Field(default=48000, ge=4096, le=262144)
    consent: bool = False


class CSI(BaseModel):
    port: int = Field(default=5500, ge=1024, le=65535)
    source_ip: str
    duration_s: int = Field(default=10, ge=1, le=30)
    synthetic: bool = True
    source_description: str = Field(min_length=3, max_length=160)
    consent: bool = False


def install(app, ctx):
    def local(request, consent=True):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Start hardware capture from the laptop.")
        if not consent:
            raise ValueError("Confirm capture consent first.")

    @app.get("/api/hardware/wifi")
    def wifi():
        return wifi_status()

    @app.get("/api/hardware/sdr")
    def enumerate_sdr(request: Request):
        local(request)
        if not importlib.util.find_spec("SoapySDR"):
            return {
                "state": "NOT INSTALLED",
                "devices": [],
                "next_step": "Install SoapySDR and your receiver driver, connect the SDR, and scan again.",
            }
        import SoapySDR

        devices = [dict(d) for d in SoapySDR.Device.enumerate()]
        return {
            "state": "AVAILABLE" if devices else "HARDWARE UNVERIFIED",
            "devices": [
                {"index": i, "label": d.get("label", d.get("driver", "SDR"))}
                for i, d in enumerate(devices)
            ],
            "next_step": "Choose a device and run a short capture; enumeration does not verify RF reception.",
        }

    @app.post("/api/hardware/sdr/capture")
    def sdr(body: SDR, request: Request):
        local(request, body.consent)
        if not importlib.util.find_spec("SoapySDR"):
            raise HTTPException(
                503, "Install SoapySDR and a compatible receiver driver before capturing."
            )

        def work(jid, progress):
            import SoapySDR

            devices = SoapySDR.Device.enumerate()
            if body.device_index >= len(devices):
                raise ValueError("Connect the selected SDR and scan devices again.")
            device = SoapySDR.Device(devices[body.device_index])
            stream = None
            try:
                device.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, body.sample_rate_hz)
                device.setFrequency(SoapySDR.SOAPY_SDR_RX, 0, body.frequency_hz)
                actual_rate = float(device.getSampleRate(SoapySDR.SOAPY_SDR_RX, 0))
                actual_frequency = float(device.getFrequency(SoapySDR.SOAPY_SDR_RX, 0))
                stream = device.setupStream(SoapySDR.SOAPY_SDR_RX, SoapySDR.SOAPY_SDR_CF32)
                device.activateStream(stream)
                samples = np.empty(body.frames, dtype=np.complex64)
                offset = 0
                start = time.monotonic()
                while offset < len(samples):
                    progress("Reading SDR samples", 5 + int(80 * offset / len(samples)))
                    if time.monotonic() - start > 15:
                        raise ValueError("SDR timed out. Check device permissions and sample rate.")
                    result = device.readStream(
                        stream, [samples[offset:]], len(samples) - offset, timeoutUs=500000
                    )
                    if result.ret < 0:
                        raise ValueError(
                            "SDR driver reported a stream error or overflow. Reduce sample rate and retry."
                        )
                    offset += result.ret
                raw = io.BytesIO()
                np.save(raw, samples, allow_pickle=False)
                progress("Saving I/Q recording", 90)
                return ctx["save_asset"](
                    raw.getvalue(),
                    "SDR-capture.npy",
                    "LIVE SDR DRIVER OUTPUT",
                    sample_rate_hz=actual_rate,
                    center_frequency_hz=actual_frequency,
                    notes="Captured via SoapySDR; RF calibration and device acceptance require separate reference tests.",
                )
            finally:
                if stream is not None:
                    try:
                        device.deactivateStream(stream)
                    finally:
                        device.closeStream(stream)

        return ctx["job_start"]("sdr-capture", work)

    @app.post("/api/hardware/csi/receive")
    def csi(body: CSI, request: Request):
        local(request, body.consent)
        address = ipaddress.ip_address(body.source_ip)
        if not address.is_private or address.is_multicast:
            raise ValueError("Choose the specific private source IP of your compatible CSI sender.")

        def work(jid, progress):
            accepted = []
            times = []
            rejected = 0
            subcarriers = None
            began = time.monotonic()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
                receiver.bind(("0.0.0.0", body.port))
                receiver.settimeout(0.25)
                while time.monotonic() - began < body.duration_s:
                    progress(
                        "Waiting for compatible CSI UDP packets",
                        int(85 * (time.monotonic() - began) / body.duration_s),
                    )
                    try:
                        packet, sender = receiver.recvfrom(65507)
                    except socket.timeout:
                        continue
                    if sender[0] != body.source_ip:
                        continue
                    try:
                        p = json.loads(packet)
                        real = np.asarray(p["real"], float)
                        imag = np.asarray(p["imag"], float)
                        timestamp = float(p["timestamp"])
                        if (
                            real.ndim != 1
                            or len(real) not in (64, 128, 256, 512)
                            or real.shape != imag.shape
                            or not np.isfinite(real).all()
                            or not np.isfinite(imag).all()
                            or not np.isfinite(timestamp)
                        ):
                            raise ValueError()
                        if (
                            subcarriers is not None
                            and subcarriers != len(real)
                            or times
                            and timestamp <= times[-1]
                        ):
                            raise ValueError()
                        subcarriers = len(real)
                        accepted.append(real + 1j * imag)
                        times.append(timestamp)
                        if len(times) >= 10000:
                            break
                    except (ValueError, TypeError, KeyError):
                        rejected += 1
                    if rejected > 20000:
                        raise ValueError(
                            "Too many invalid packets. Check sender format before retrying."
                        )
            if len(times) < 32:
                raise ValueError(
                    "Fewer than 32 valid CSI packets. Start a compatible external sender; a phone file upload is not CSI capture."
                )
            raw = io.BytesIO()
            np.savez_compressed(raw, csi=np.asarray(accepted).T, timestamps=np.asarray(times))
            progress("Saving external CSI recording", 95)
            return ctx["save_asset"](
                raw.getvalue(),
                "external-CSI.npz",
                "EXTERNAL CSI UDP · USER-DECLARED SOURCE",
                synthetic=body.synthetic,
                packet_count=len(times),
                rejected_packets=rejected,
                notes=body.source_description
                + "; native 802.11bf and source hardware authenticity not independently verified.",
            )

        return ctx["job_start"]("csi-receive", work)
