# Source notes for safe Phonon-Key alternative

## Beam vibration reference
IOPscience article: Rafael M. Digilov, “Flexural vibration test of a cantilever beam with a force sensor: fast determination of Young's modulus,” European Journal of Physics 29(3), 2008. URL: https://iopscience.iop.org/article/10.1088/0143-0807/29/3/018/meta

The abstract states that a clamped-free strip is modeled with the Euler–Bernoulli beam model, and that free-bending vibrations followed by FFT identify the resonant frequency; Young’s modulus is calculated from the model. It also reports that the method was used across several industrial materials and examined temperature dependence of stainless-steel modulus.

## Paris-law reference
Engineering Library, “Fatigue Crack Growth,” URL: https://engineeringlibrary.org/reference/fatigue-crack-growth

The page gives Paris law as da/dN = C (Delta K)^m and explains that crack-growth rate depends primarily on the stress-intensity-factor range Delta K = K_max - K_min. It notes that C and m depend on material, environment, and temperature, and that the relationship is empirical and applies to the stable-growth region. It also discusses effective Delta K and crack closure effects.

## Design implication
The safe simulator will use these equations only for a bounded, synthetic lab model. It will not encode, transmit, or recover secrets. The payload will be a fixed public test pattern or a user-supplied non-sensitive diagnostic bit string, and the output will be framed as telemetry robustness testing rather than covert exfiltration.
