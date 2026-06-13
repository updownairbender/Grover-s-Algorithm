import argparse
import os
import re

import matplotlib.pyplot as plt

from src.pipeline import (
    build_grover_circuit,
    optimal_iterations,
    run_ideal,
    run_noisy,
    extract_marked_probability,
    expected_success_probability,
    compute_probabilities,
    save_circuit_diagram,
    NOISE_MODEL,
)


def _parse_search(value: str) -> list[str]:
    parts = [s.strip() for s in value.split(",")]
    for p in parts:
        if not re.fullmatch(r"[01]+", p):
            raise ValueError(
                f"Invalid search state '{p}'. Must be a binary string."
            )
    return parts


def _validate_args(args: argparse.Namespace) -> None:
    if args.qubits < 1:
        raise ValueError("--qubits must be >= 1")
    for s in args.search:
        if len(s) != args.qubits:
            raise ValueError(
                f"State '{s}' length {len(s)} does not match --qubits {args.qubits}"
            )


def _plot_histogram(
    probs: dict,
    marked_states: list[str],
    title: str,
    filepath: str | None,
) -> None:
    states = sorted(probs.keys())
    values = [probs[s] for s in states]

    colors = [
        "#2ecc71" if s in marked_states else "#3498db" for s in states
    ]

    fig, ax = plt.subplots(figsize=(max(10, len(states) * 0.4), 5))
    ax.bar(states, values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Computational Basis State")
    ax.set_ylabel("Probability")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)

    for i, v in enumerate(values):
        if v > 0.02:
            ax.text(i, v + 0.005, f"{v:.1%}", ha="center", fontsize=7)

    plt.tight_layout()
    if filepath:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath, dpi=150)
        print(f"  Plot saved to {filepath}")
    try:
        plt.show(block=True)
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grover's Search Algorithm - scalable, noise-aware implementation",
    )
    parser.add_argument(
        "--qubits",
        type=int,
        default=4,
        help="Number of qubits (default: 4)",
    )
    parser.add_argument(
        "--search",
        type=str,
        required=True,
        help="Marked state(s) as binary string(s), comma-separated for multi-state, e.g. 1101 or 001,110",
    )
    parser.add_argument(
        "--noise",
        action="store_true",
        help="Run on a noisy simulated backend",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=8192,
        help="Number of measurement shots (default: 8192)",
    )
    parser.add_argument(
        "--save-plot",
        type=str,
        default=None,
        help="File path to save the probability histogram (e.g. outputs/histogram.png)",
    )
    parser.add_argument(
        "--save-circuit",
        type=str,
        default=None,
        help="File path to save the circuit diagram (e.g. outputs/circuit.txt)",
    )

    args = parser.parse_args()
    args.search = _parse_search(args.search)
    _validate_args(args)

    num_marked = len(args.search)
    label = ",".join(args.search) if num_marked > 1 else args.search[0]
    iters = optimal_iterations(args.qubits, num_marked)

    print()
    print("=" * 60)
    print(f"  Grover's Search Algorithm")
    print("=" * 60)
    print(f"  Qubits:          {args.qubits}")
    print(f"  Search state(s): |{label}>")
    if num_marked > 1:
        print(f"  Marked count:    {num_marked}")
    print(f"  Optimal iters:   {iters}")
    print(f"  Shots:           {args.shots}")
    print(f"  Noise model:     {'Enabled' if args.noise else 'Disabled'}")
    print("=" * 60)
    print()

    circuit = build_grover_circuit(args.qubits, args.search, iters)

    if args.save_circuit:
        save_circuit_diagram(circuit, args.save_circuit)
        print(f"  Circuit diagram saved to {args.save_circuit}")

    run_fn = run_noisy if args.noise else run_ideal
    counts = run_fn(circuit, shots=args.shots)
    probs = compute_probabilities(counts, args.qubits)
    marked_prob = extract_marked_probability(counts, args.search)

    sim_label = "Noisy" if args.noise else "Ideal"
    title = f"Grover's Algorithm ({sim_label}) - {args.qubits} qubits, |{label}>"

    top = sorted(probs.items(), key=lambda x: -x[1])[:5]
    print(f"  Measurement Results ({sim_label} Simulator):")
    print(f"  {'State':>8}  {'Probability':>12}")
    print(f"  {'-'*8}  {'-'*12}")
    for state, prob in top:
        marker = "  <- marked" if state in args.search else ""
        print(f"  {state:>8}  {prob:>10.2%}{marker}")
    print()
    print(f"  Marked state(s) |{label}> probability: {marked_prob:.2%}")
    expected = expected_success_probability(args.qubits, num_marked, iters)
    print(f"  Expected (ideal): {expected:.1%}")

    _plot_histogram(probs, args.search, title, args.save_plot)


if __name__ == "__main__":
    main()
