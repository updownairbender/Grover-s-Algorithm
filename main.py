import argparse
import os
import re


def _parse_search(value: str) -> list[str]:
    """Parse comma-separated binary search states into a list."""
    parts = [s.strip() for s in value.split(",")]
    for p in parts:
        if not re.fullmatch(r"[01]+", p):
            raise ValueError(
                f"Invalid search state '{p}'. Must be a binary string."
            )
    return parts


def _validate_args(args: argparse.Namespace) -> None:
    """Validate qubits count and lengths of search state(s)."""
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
    """Plot or save a probability histogram with marked states highlighted."""
    # Lazy import so `-h` stays instant
    import matplotlib.pyplot as plt

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


def _print_header(args: argparse.Namespace, iters: int, label: str) -> None:
    """Print run configuration banner."""
    print()
    print("=" * 60)
    print(f"  Grover's Search Algorithm")
    print("=" * 60)
    print(f"  Qubits:          {args.qubits}")
    print(f"  Search state(s): |{label}>")
    if len(args.search) > 1:
        print(f"  Marked count:    {len(args.search)}")
    print(f"  Optimal iters:   {iters}")
    print(f"  Shots:           {args.shots}")
    print(f"  Noise model:     {'Enabled' if args.noise else 'Disabled'}")
    print("=" * 60)
    print()


def _print_results(
    probs: dict,
    marked_prob: float,
    expected: float,
    args: argparse.Namespace,
    label: str,
) -> None:
    """Print top-5 measurement results and marked-state probability."""
    sim_label = "Noisy" if args.noise else "Ideal"
    top = sorted(probs.items(), key=lambda x: -x[1])[:5]
    print(f"  Measurement Results ({sim_label} Simulator):")
    print(f"  {'State':>8}  {'Probability':>12}")
    print(f"  {'-'*8}  {'-'*12}")
    for state, prob in top:
        marker = "  <- marked" if state in args.search else ""
        print(f"  {state:>8}  {prob:>10.2%}{marker}")
    print()
    print(f"  Marked state(s) |{label}> probability: {marked_prob:.2%}")
    print(f"  Expected (ideal): {expected:.1%}")


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser with all CLI flags."""
    parser = argparse.ArgumentParser(
        description="Grover's Search Algorithm -- dynamic oracle, M-state search, noise simulation",
        epilog=(
            "Examples:\n"
            "  python main.py --qubits 3 --search 101\n"
            "  python main.py --qubits 4 --search 1101 --noise --shots 4096\n"
            "  python main.py --qubits 3 --search \"000,111\" --save-plot outputs/hist.png\n"
            "  python main.py --qubits 5 --search 10101 --save-circuit outputs/circ.png"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--qubits",
        type=int,
        default=4,
        help="Number of qubits (n). Search space = 2^n states (default: 4)",
    )
    parser.add_argument(
        "--search",
        type=str,
        required=True,
        help="Binary state(s) to search for. Comma-separated for multi-state (e.g. 1101 or 000,111)",
    )
    parser.add_argument(
        "--noise",
        action="store_true",
        help="Enable noise model (depolarizing gate + readout errors)",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=8192,
        help="Measurement repetitions. Higher = less sampling noise (default: 8192)",
    )
    parser.add_argument(
        "--save-plot",
        type=str,
        default=None,
        help="Save probability histogram as PNG (e.g. outputs/histogram.png)",
    )
    parser.add_argument(
        "--save-circuit",
        type=str,
        default=None,
        help="Save circuit diagram. .png = mpl style, .txt = ASCII (e.g. outputs/circuit.png)",
    )
    return parser


def main() -> None:
    # ── Build argument parser ──
    parser = _build_parser()

    # ── Parse and validate arguments ──
    args = parser.parse_args()
    args.search = _parse_search(args.search)
    _validate_args(args)


    # Lazy imports: Qiskit, Aer load here so `-h` stays instant
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

    # ── Display run configuration ──
    num_marked = len(args.search)
    label = ",".join(args.search) if num_marked > 1 else args.search[0]
    iters = optimal_iterations(args.qubits, num_marked)

    _print_header(args, iters, label)

    # ── Build Grover circuit ──
    circuit = build_grover_circuit(args.qubits, args.search, iters)
    if args.save_circuit:
        save_circuit_diagram(circuit, args.save_circuit)
        print(f"  Circuit diagram saved to {args.save_circuit}")

    # ── Run simulation ──
    run_fn = run_noisy if args.noise else run_ideal
    counts = run_fn(circuit, shots=args.shots)
    probs = compute_probabilities(counts, args.qubits)
    marked_prob = extract_marked_probability(counts, args.search)


    # ── Display results ──
    expected = expected_success_probability(args.qubits, num_marked, iters)
    _print_results(probs, marked_prob, expected, args, label)

    # ── Plot histogram ──
    sim_label = "Noisy" if args.noise else "Ideal"
    title = f"Grover's Algorithm ({sim_label}) - {args.qubits} qubits, |{label}>"
    _plot_histogram(probs, args.search, title, args.save_plot)


if __name__ == "__main__":
    main()
