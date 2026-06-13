import time
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit_aer import AerSimulator

from src.pipeline import build_grover_circuit, optimal_iterations


SWEEP_QUBITS = range(2, 11)
SHOTS_PER_POINT = 2048


def measure_circuit_stats(num_qubits: int, marked_state: str) -> dict:
    circuit = build_grover_circuit(num_qubits, marked_state)
    ops = circuit.count_ops()

    return {
        "depth": circuit.depth(),
        "num_qubits": num_qubits,
        "total_gates": sum(ops.values()),
        "cx_gates": ops.get("cx", 0) + ops.get("mcx", 0) + ops.get("ccx", 0),
        "iterations": optimal_iterations(num_qubits, 1),
    }


def measure_execution_time(circuit) -> float:
    backend = AerSimulator()
    start = time.perf_counter()
    backend.run(circuit, shots=SHOTS_PER_POINT).result()
    return time.perf_counter() - start


def plot_benchmark(results: list[dict], title: str, ylabel: str, filepath: str) -> None:
    xs = [r["num_qubits"] for r in results]
    ys = [r["value"] for r in results]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs, ys, "o-", color="#3498db", linewidth=2, markersize=6)
    ax.set_xlabel("Number of Qubits (n)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(filepath, dpi=150)
    print(f"  Plot saved: {filepath}")
    plt.close(fig)


def main() -> None:
    print()
    print("=" * 60)
    print("  Grover's Algorithm - Scalability Benchmark")
    print("=" * 60)
    print()

    depth_results = []
    time_results = []

    for n in SWEEP_QUBITS:
        marked = "1" * n
        info = measure_circuit_stats(n, marked)
        circuit = build_grover_circuit(n, marked)
        elapsed = measure_execution_time(circuit)

        depth_results.append({"num_qubits": n, "value": info["depth"]})
        time_results.append({"num_qubits": n, "value": elapsed})

        print(
            f"  n={n:2d}  |  depth={info['depth']:5d}  "
            f"gates={info['total_gates']:6d}  "
            f"cx={info['cx_gates']:5d}  "
            f"iters={info['iterations']:2d}  "
            f"time={elapsed:.3f}s"
        )

    plot_benchmark(
        depth_results,
        "Grover's Algorithm - Circuit Depth vs. Qubits",
        "Circuit Depth",
        "outputs/benchmark_depth.png",
    )
    plot_benchmark(
        time_results,
        "Grover's Algorithm - Execution Time vs. Qubits",
        f"Execution Time (s) - {SHOTS_PER_POINT} shots",
        "outputs/benchmark_time.png",
    )

    print()
    print("  Done. Plots saved to outputs/.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
