"""Synthetic vibration stream and receiver DSP."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks

from .beam import Beam


@dataclass(frozen=True)
class DSPParameters:
    sample_rate_hz: float = 2_000.0
    fft_window_s: float = 0.50
    frequency_deviation_hz: float = 0.75
    noise_std: float = 0.002
    random_seed: int = 7


def bit_at_time(t: float, bits: str, bit_period_s: float) -> str:
    index = min(int(np.floor(t / bit_period_s)), len(bits) - 1)
    return bits[index]


def synthesize_stream(
    t: np.ndarray,
    base_frequency_hz: np.ndarray,
    bits: str,
    bit_period_s: float,
    params: DSPParameters,
) -> np.ndarray:
    """Synthesize a sensor-like vibration/audio stream.

    A public diagnostic bit changes the instantaneous carrier frequency by a
    small signed deviation.  The stream is intentionally synthetic and does
    not interact with acoustic hardware.
    """
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("bits must be a non-empty binary string")
    t = np.asarray(t, dtype=float)
    bits_array = np.fromiter(
        (1.0 if bit_at_time(x, bits, bit_period_s) == "1" else -1.0 for x in t),
        dtype=float,
        count=len(t),
    )
    instantaneous_frequency = base_frequency_hz + params.frequency_deviation_hz * bits_array
    phase = 2.0 * np.pi * np.cumsum(instantaneous_frequency) / params.sample_rate_hz
    envelope = 0.55 + 0.20 * np.sin(2.0 * np.pi * 0.7 * t)
    rng = np.random.default_rng(params.random_seed)
    return envelope * np.sin(phase) + rng.normal(0.0, params.noise_std, size=len(t))


def dominant_frequency(signal: np.ndarray, sample_rate_hz: float) -> float:
    """Estimate the dominant positive FFT frequency with a Hann window."""
    signal = np.asarray(signal, dtype=float)
    if len(signal) < 8:
        raise ValueError("signal is too short for FFT estimation")
    centered = signal - np.mean(signal)
    window = np.hanning(len(centered))
    spectrum = np.abs(np.fft.rfft(centered * window))
    frequencies = np.fft.rfftfreq(len(centered), 1.0 / sample_rate_hz)
    spectrum[0] = 0.0
    return float(frequencies[np.argmax(spectrum)])


def decode_bits_from_fft(
    t: np.ndarray,
    stream: np.ndarray,
    fatigue_frequency_hz: np.ndarray,
    bits: str,
    bit_period_s: float,
    params: DSPParameters,
) -> tuple[str, np.ndarray, np.ndarray]:
    """Decode the public diagnostic pattern from windowed peak shifts.

    Returns decoded bits, per-window estimated frequencies, and threshold.
    Thresholding is relative to each window's fatigue-only carrier estimate.
    """
    window_samples = max(8, int(round(params.fft_window_s * params.sample_rate_hz)))
    samples_per_bit = max(1, int(round(bit_period_s * params.sample_rate_hz)))
    decoded = []
    estimates = []
    threshold = params.frequency_deviation_hz * 0.0

    for bit_index in range(len(bits)):
        start = bit_index * samples_per_bit
        stop = min(start + samples_per_bit, len(stream))
        if stop - start < 8:
            break
        chunk = stream[start:stop]
        if len(chunk) < window_samples:
            local = chunk
        else:
            local = chunk[-window_samples:]
        measured = dominant_frequency(local, params.sample_rate_hz)
        carrier = float(np.mean(fatigue_frequency_hz[start:stop]))
        delta = measured - carrier
        estimates.append(measured)
        threshold = max(threshold, abs(params.frequency_deviation_hz) * 0.45)
        decoded.append("1" if delta >= threshold else "0")

    return "".join(decoded), np.asarray(estimates), np.asarray(threshold)


def peak_candidates(signal: np.ndarray, sample_rate_hz: float) -> tuple[np.ndarray, np.ndarray]:
    """Return FFT bins that are plausible resonance peaks for inspection."""
    spectrum = np.abs(np.fft.rfft(np.asarray(signal) * np.hanning(len(signal))))
    frequencies = np.fft.rfftfreq(len(signal), 1.0 / sample_rate_hz)
    peaks, _ = find_peaks(spectrum)
    return frequencies[peaks], spectrum[peaks]
