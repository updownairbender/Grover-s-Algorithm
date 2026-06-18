# Grover's Search Algorithm

Scalable, Noise-Aware Implementation

[![Tests](https://github.com/updownairbender/grover-s-algorithm/actions/workflows/pytest.yml/badge.svg)](https://github.com/updownairbender/grover-s-algorithm/actions/workflows/pytest.yml)

A **production-grade**, scalable implementation of Grover's quantum search algorithm with dynamic oracle synthesis, noise simulation, and amplitude amplification visualization.

```cmd
> python main.py --qubits 4 --search 1101 --noise --save-plot outputs/histogram.png
```

## Overview

Grover's algorithm searches an unsorted database of $N = 2^n$ items in $O(\sqrt{N})$ quantum queries - a **quadratic speedup** over the classical $O(N)$.

### Properties

- **Dynamic oracle** - specify *any* binary marked state; the circuit adapts
- **Scalable diffuser** - generalized inversion-about-the-mean for $n$ qubits
- **Optimal iteration calculator** - automatically computes $R \approx \frac{\pi}{4}\sqrt{\frac{2^n}{M}}$
- **Noise simulation** - depolarizing gate errors + readout errors on a realistic backend
- **Multi-state search** - search for $M$ marked states simultaneously via `--search "001,110"`
- **Circuit visualization** - text diagrams, probability histograms, scalability benchmarks

## Quick Start

```bash
git clone https://github.com/updownairbender/Grover-s-Algorithm.git
cd Grover-s-Algorithm
pip install -r requirements.txt
```

### CLI Usage

```bash
# 4-qubit search for |1101> on ideal simulator
python main.py --qubits 4 --search 1101

# Same search with noise simulation
python main.py --qubits 4 --search 1101 --noise

# Save the histogram plot and circuit diagram (PNG via matplotlib)
python main.py --qubits 5 --search 10101 --save-plot outputs/histogram.png --save-circuit outputs/circuit.png

# Multi-state search: find |000> and |111> simultaneously
python main.py --qubits 3 --search "000,111"
```

### Run the Notebook

```bash
jupyter notebook notebooks/demonstration.ipynb
```

### Run Tests

```bash
pytest tests/ -v
```

### Benchmark

```bash
python scripts/benchmark.py
```

</br>

## Architecture

```python
grovers-search-scaled/
│
├── src/                       # Core implementation
│   ├── oracle.py              # Dynamic phase oracle (any n, any marked state)
│   ├── diffuser.py            # Generalized diffusion operator (n qubits)
│   └── pipeline.py            # Build circuit, compute iterations, run sims
│
├── tests/
│   └── test_circuits.py       # pytest: oracle, diffuser, full pipeline
│
├── scripts/
│   └── benchmark.py           # Scalability analysis (depth, gates, time vs n)
│
├── notebooks/
│   └── demonstration.ipynb    # Interactive walkthrough
│
├── .github/workflows/
│   └── pytest.yml             # CI/CD: lint + test on every push
│
├── main.py                    # CLI entry point
├── requirements.txt           # Single-command install
├── pyproject.toml             # Package metadata & build config
├── .gitignore                 # venv, cache, outputs, IDE
└── README.md
```

</br>

## Mathematical Background

### Oracle ($U_f$)

The oracle marks the target state $|\omega\rangle$ by flipping its phase:

$$U_f|x\rangle = \begin{cases} -|x\rangle & \text{if } x = \omega \\ |x\rangle & \text{otherwise} \end{cases}$$

Implementation: for each qubit where $\omega_i = 0$, apply X gates before/after a multi-controlled Z gate, so only the $|1\dots1\rangle$ state acquires a phase - which maps to $|\omega\rangle$ after inversion.

### Diffuser ($D$)

The diffusion operator inverts amplitudes about their mean:

$$D = 2|\psi\rangle\langle\psi| - I = H^{\otimes n}\left(2|0\rangle\langle 0| - I\right)H^{\otimes n}$$

After each oracle-diffuser pair, the amplitude of $|\omega\rangle$ grows by approximately $2/\sqrt{N}$, while others shrink.

### Optimal Iterations

Let $\theta = \arcsin(\sqrt{M/N})$. The code computes the exact number of iterations:

$$R = \left\lfloor\frac{\pi/2 - \theta}{2\theta}\right\rceil$$

For $M \ll N$, this reduces to the familiar approximation:

$$R \approx \frac{\pi}{4}\sqrt{\frac{N}{M}}$$

Where $N = 2^n$ and $M$ is the number of marked states.

The code uses the exact formula because the approximation can be off by 1 for small systems. For example, $n=2$, $M=1$ ($N=4$): the exact formula gives $R=1$, while the approximation yields $\pi/4 \cdot \sqrt{4} \approx 1.57 \to 2$ — that extra iteration overshoots the optimum and lowers success probability. The exact formula guarantees correctness for any $n$ and $M$.

### Geometric Interpretation

The algorithm iterates the state vector through a 2D subspace spanned by $|\omega\rangle$ (marked) and $|\omega^\perp\rangle$ (unmarked). Each Grover iteration rotates the vector by $2\theta$, where $\sin\theta = \sqrt{M/N}$.

## Results

### 3-Qubit Search for |101> (Ideal)

```txt
  Measurement Results (Ideal Simulator):
    State     Probability
  --------   ------------
       101       94.75%   <- marked
       100        0.81%
       110        0.79%
       001        0.74%
       010        0.74%
```

### Amplitude Amplification

```txt
  n=3, searching |101>
  Iters=0  ->  p=13.2%   (expected 12.5%, uniform)
  Iters=1  ->  p=77.6%   (expected 78.1%)
  Iters=2  ->  p=94.8%   <- optimal (expected 94.5%)
  Iters=3  ->  p=33.0%   (expected 33.0%, overshoot)
  Iters=4  ->  p=1.3%    (expected 1.2%)
```

### Noise Degradation

| Metric | Ideal | Noisy (1% 1q, 1% 2q, 2% readout) |
|----|----|----|
| Marked state prob | 94.5% | 71.2% |
| Correct ranking | ✅ | ✅ |
| Circuit depth | 14 | 14 |

</br>

## Project Status

| Component | Status |
|---|---|
| Dynamic Oracle | ✅ |
| Scalable Diffuser | ✅ |
| Multi-State Search (M marked states) | ✅ |
| Optimal Iteration Calculator | ✅ |
| Ideal Simulation | ✅ |
| Noise Simulation (depolarizing + readout) | ✅ |
| CLI with argparse | ✅ |
| Probability Histograms | ✅ |
| Circuit Diagram Export (PNG + text) | ✅ |
| Unit Tests (pytest) | ✅ |
| CI/CD (GitHub Actions) | ✅ |
| Scalability Benchmark | ✅ |
| Jupyter Notebook | ✅ |

## License

MIT

---

*Built with [Qiskit](https://qiskit.org/) . Simulation by [Aer](https://qiskit.github.io/qiskit-aer/)*
