"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .plotting import animate_progressive_bits, save_summary_plot
from .simulation import run_simulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benign Phonon-Key fatigue telemetry lab")
    parser.add_argument(
        "--pattern",
        default="1011001110010110",
        help="public diagnostic bit pattern; never use a secret",
    )
    parser.add_argument("--bit-period", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("phonon_key_summary.png"))
    parser.add_argument("--live", action="store_true", help="show progressive window-by-window plot")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_simulation(args.pattern, args.bit_period)
    save_summary_plot(result, str(args.output))
    print(f"public pattern : {result.public_test_pattern}")
    print(f"decoded pattern: {result.decoded_bits}")
    print(f"plot saved     : {args.output.resolve()}")
    print(f"final damage   : {result.damage[-1]:.4f}")
    print(f"frequency start: {result.fatigue_frequency_hz[0]:.4f} Hz")
    print(f"frequency end  : {result.fatigue_frequency_hz[-1]:.4f} Hz")
    if args.live:
        animate_progressive_bits(result)


if __name__ == "__main__":
    main()
