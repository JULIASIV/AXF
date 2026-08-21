# Phonon-Key Lab

**Phonon-Key Lab** is a hardware-free cyber-physical-systems research demonstrator that couples a vibrating metallic cantilever, a bounded Paris-law fatigue surrogate, an abstract thermal-load trace, and FFT-based telemetry decoding. It is deliberately designed for **non-secret laboratory payloads only**.

The original concept of embedding an AES key in an acoustic covert channel is not implemented. Transmitting or recovering a cryptographic key through a covert physical channel would directly enable secret exfiltration. Instead, the framework uses a fixed public diagnostic pattern such as `1011001110010110`, which is useful for validating resonance tracking, signal robustness, fatigue progression, and receiver error rates without handling secrets.

## Physical model

For a uniform clamped-free Euler–Bernoulli beam, the first-mode resonance is modeled as

$$
f_1 = \frac{\beta_1^2}{2\pi L^2}\sqrt{\frac{EI}{\rho A}}, \qquad \beta_1 \approx 1.875104,
$$

where \(L\) is beam length, \(E\) is Young’s modulus, \(I\) is the second moment of area, \(\rho\) is density, and \(A\) is cross-sectional area. The relationship between cantilever resonance, Fourier analysis, and modulus identification is established in the laboratory reference by Digilov [1].

Fatigue is represented with the Paris relation

$$
\frac{da}{dN} = C(\Delta K)^m, \qquad
\Delta K = Y\Delta\sigma\sqrt{\pi a},
$$

where \(a\) is crack length, \(N\) is cycle count, \(C\) and \(m\) are illustrative material parameters, \(Y\) is a geometry factor, and \(\Delta\sigma\) is the stress range. The Engineering Library reference describes this as an empirical stable-growth relation whose parameters depend on material, environment, and temperature [2].

The simulator maps normalized crack-growth damage \(d \in [0,1]\) to an effective modulus with a bounded surrogate:

\[
E_{fatigue}(t) = E_0[1 - \lambda d(t)].
\]

A first-order thermal model converts an abstract load waveform into temperature, then applies a small linearized temperature coefficient to obtain \(E_{eff}(t)\). The abstract load waveform is mathematical only: the code does **not** busy-loop, change host CPU utilization, access microphones, or control actuators.

## Repository structure

```text
phonon-key-lab/
├── pyproject.toml
├── README.md
├── phonon_key/
│   ├── __init__.py       # Public package exports
│   ├── beam.py           # Beam geometry, natural frequency, and ODE solver
│   ├── fatigue.py        # Paris-law crack trajectory and normalized damage
│   ├── thermal.py        # Abstract load pulses and first-order thermal response
│   ├── signal.py         # Synthetic sensor stream and FFT receiver DSP
│   ├── simulation.py     # End-to-end orchestration and result container
│   ├── plotting.py       # Static summary plot and progressive live-style plot
│   └── cli.py            # Command-line entry point
└── tests/
    └── test_phonon_key.py
```

## Installation and execution

From the project directory:

```bash
python3 -m pip install -e .
phonon-key-lab --pattern 1011001110010110 --output phonon_key_summary.png
```

The command prints the public test pattern, the decoded result, the final normalized fatigue damage, and the resonance at the beginning and end of the run. To see the progressive readout window-by-window, run:

```bash
phonon-key-lab --pattern 1011001110010110 --live
```

The end-to-end test suite can be run with:

```bash
python3 -m pytest -q
```

## Pipeline

The simulation proceeds in six stages. First, `Beam.natural_frequency_hz()` computes the resonance from density, modulus, and geometry. Second, `paris_crack_trajectory()` integrates the crack-length ODE driven by the Paris relation and returns a normalized damage curve. Third, `cpu_load_modulation()` converts the public diagnostic bits into an abstract low/high load trace. Fourth, `thermal_response()` applies a first-order thermal model, and `temperature_modulus_factor()` produces a small temperature-dependent modulus factor. Fifth, `synthesize_stream()` generates a synthetic sensor stream whose carrier follows the fatigue- and temperature-dependent resonance. Finally, `decode_bits_from_fft()` estimates each window’s dominant FFT frequency and thresholds the shift relative to the fatigue-only carrier estimate.

The final plot contains the damage curve, temperature and resonance drift, synthetic sensor signal, and a bottom panel where decoded public bits appear progressively. Green text indicates a match with the expected diagnostic pattern; red text indicates a mismatch.

## Five-day implementation roadmap

| Day | Engineering objective | Concrete deliverable | Verification |
|---|---|---|---|
| 1 | Establish the physical baseline | Implement beam geometry, mass properties, first-mode frequency, damping, and `solve_ivp` modal ODE integration | Compare the computed frequency against a hand-calculated reference case and verify finite, stable ODE output |
| 2 | Add bounded fatigue mechanics | Implement Paris-law crack growth with explicit MPa√m units, event clipping, normalized damage, and modulus degradation | Confirm monotonically increasing crack length and decreasing effective modulus; document that parameters are illustrative |
| 3 | Add abstract thermal telemetry | Implement public-pattern load modulation, first-order thermal response, and temperature-dependent modulus factor | Verify no system-load side effects, bounded temperatures, and expected direction of frequency shifts |
| 4 | Implement receiver DSP | Generate the synthetic stream, apply Hann-windowed FFT peak estimation, perform per-window threshold decoding, and compute mismatch rate | Run deterministic tests with fixed random seed; test noise and frequency-deviation sweeps |
| 5 | Integrate visualization and research packaging | Add progressive plotting, CLI, README, tests, experiment configuration, and result export | Run the full test suite, save a reproducible summary plot, and archive configuration plus output metrics |

## Safe extension points

A legitimate laboratory extension could replace `synthesize_stream()` with a file-based sensor replay, add calibration data for a real beam, or evaluate receiver performance under controlled noise. Any hardware integration should remain opt-in, bounded, and restricted to non-sensitive telemetry. The framework should not be modified to carry credentials, cryptographic keys, authentication tokens, private messages, or other secrets.

## References

[1]: https://iopscience.iop.org/article/10.1088/0143-0807/29/3/018/meta "Rafael M. Digilov, Flexural vibration test of a cantilever beam with a force sensor: fast determination of Young's modulus, European Journal of Physics 29(3), 2008"

[2]: https://engineeringlibrary.org/reference/fatigue-crack-growth "Engineering Library, Fatigue Crack Growth"
