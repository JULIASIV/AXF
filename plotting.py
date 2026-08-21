"""Visualization for the fatigue and DSP telemetry demonstration."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .simulation import SimulationResult


def save_summary_plot(result: SimulationResult, output_path: str) -> None:
    """Save a four-panel summary, including progressive bit appearance."""
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), constrained_layout=True)

    axes[0].plot(result.time_s, result.damage, color="#9b2226", lw=1.8)
    axes[0].set_ylabel("Damage")
    axes[0].set_title("Phonon-Key Lab: fatigue-driven resonance telemetry")
    axes[0].grid(alpha=0.25)

    axes[1].plot(result.time_s, result.temperature_c, color="#ca6702", lw=1.3, label="temperature")
    axes[1].set_ylabel("Temp. (°C)")
    axes[1].twinx().plot(
        result.time_s,
        result.fatigue_frequency_hz,
        color="#005f73",
        lw=1.3,
        label="resonance",
    )
    axes[1].grid(alpha=0.25)

    axes[2].plot(result.time_s, result.stream, color="#3a0ca3", lw=0.55)
    axes[2].set_ylabel("Synthetic sensor")
    axes[2].set_xlim(result.time_s[0], result.time_s[-1])
    axes[2].grid(alpha=0.25)

    axes[3].set_xlim(0, len(result.public_test_pattern))
    axes[3].set_ylim(-0.5, 0.5)
    axes[3].set_yticks([])
    axes[3].set_xlabel("Fatigue progression / bit window")
    for idx, expected in enumerate(result.public_test_pattern):
        decoded = result.decoded_bits[idx] if idx < len(result.decoded_bits) else "·"
        color = "#2a9d8f" if decoded == expected else "#e76f51"
        axes[3].text(idx + 0.5, 0.08, decoded, ha="center", va="center", fontsize=16, color=color)
        axes[3].text(idx + 0.5, -0.18, expected, ha="center", va="center", fontsize=9, color="#555555")
        axes[3].axvline(idx, color="#cccccc", lw=0.6)
    axes[3].text(0.0, 0.42, "decoded", color="#2a9d8f", fontsize=9)
    axes[3].text(0.8, 0.42, "expected", color="#555555", fontsize=9)
    axes[3].set_title("Progressive public diagnostic-bit readout")
    axes[3].grid(axis="x", alpha=0.25)

    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def animate_progressive_bits(result: SimulationResult, interval_ms: int = 500) -> None:
    """Show decoded bits appearing window-by-window in a live-style plot."""
    if interval_ms <= 0:
        raise ValueError("interval_ms must be positive")
    plt.ion()
    fig, (ax_signal, ax_bits) = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    ax_signal.plot(result.time_s, result.stream, color="#3a0ca3", lw=0.55)
    marker = ax_signal.axvline(0.0, color="#e76f51", lw=1.2)
    ax_signal.set_title("Synthetic vibration stream")
    ax_signal.set_xlabel("Time (s)")
    ax_signal.set_ylabel("Amplitude")
    ax_signal.grid(alpha=0.25)
    ax_bits.set_xlim(0, len(result.public_test_pattern))
    ax_bits.set_ylim(-0.5, 0.5)
    ax_bits.set_yticks([])
    ax_bits.set_title("Decoded diagnostic bits appearing as fatigue progresses")

    for idx in range(len(result.decoded_bits)):
        marker.set_xdata([min((idx + 1) * result.bit_period_s, result.time_s[-1])])
        ax_bits.text(idx + 0.5, 0.0, result.decoded_bits[idx], ha="center", va="center", fontsize=20)
        ax_bits.axvline(idx, color="#cccccc", lw=0.6)
        fig.canvas.draw_idle()
        plt.pause(interval_ms / 1000.0)
    plt.ioff()
    plt.show()
