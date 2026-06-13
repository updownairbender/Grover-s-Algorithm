import pytest

from src.oracle import create_oracle, create_multi_oracle
from src.diffuser import create_diffuser
from src.pipeline import (
    optimal_iterations,
    build_grover_circuit,
    run_ideal,
    extract_marked_probability,
    expected_success_probability,
)


class TestOracle:
    def test_oracle_rejects_invalid_input(self) -> None:
        with pytest.raises(ValueError, match="length"):
            create_oracle(4, "101")
        with pytest.raises(ValueError, match="binary"):
            create_oracle(4, "1021")

    @pytest.mark.parametrize("num_qubits,marked,num_x", [
        (2, "00", 2), (2, "01", 1), (2, "10", 1), (2, "11", 0),
        (3, "101", 1),
        (4, "1010", 2),
    ])
    def test_oracle_has_correct_x_gate_count(
        self, num_qubits: int, marked: str, num_x: int
    ) -> None:
        oracle = create_oracle(num_qubits, marked)
        ops = oracle.count_ops()
        assert ops.get("x", 0) == 2 * num_x

    def test_oracle_creates_correct_name(self) -> None:
        oracle = create_oracle(4, "1010")
        assert oracle.name == "Oracle(|1010)"

    def test_multi_oracle_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            create_multi_oracle(3, [])

    def test_multi_oracle_includes_all_states(self) -> None:
        oracle = create_multi_oracle(3, ["000", "111"])
        assert "|000>" in oracle.name
        assert "|111>" in oracle.name

    def test_multi_oracle_runs_without_error(self) -> None:
        oracle = create_multi_oracle(3, ["000", "111"])
        assert oracle.num_qubits == 3


class TestDiffuser:
    @pytest.mark.parametrize("num_qubits,expected_h,expected_x", [
        (2, 4, 4), (3, 6, 6), (4, 8, 8),
    ])
    def test_diffuser_has_correct_gate_counts(
        self, num_qubits: int, expected_h: int, expected_x: int
    ) -> None:
        diffuser = create_diffuser(num_qubits)
        ops = diffuser.count_ops()
        assert ops.get("h", 0) == expected_h
        assert ops.get("x", 0) == expected_x

    def test_diffuser_contains_mcz(self) -> None:
        diffuser = create_diffuser(3)
        ops = diffuser.count_ops()
        assert "cz" in ops or "mcx" in ops or "ccz" in ops or "mcz" in ops


class TestOptimalIterations:
    def test_one_qubit(self) -> None:
        assert optimal_iterations(1, 1) == 1

    def test_two_qubits(self) -> None:
        assert optimal_iterations(2, 1) == 1

    def test_three_qubits(self) -> None:
        assert optimal_iterations(3, 1) == 2

    def test_four_qubits(self) -> None:
        assert optimal_iterations(4, 1) == 3

    def test_two_marked_states(self) -> None:
        n_iters_1 = optimal_iterations(4, 1)
        n_iters_2 = optimal_iterations(4, 2)
        assert n_iters_2 <= n_iters_1

    def test_formula_monotonic_increasing(self) -> None:
        prev = 0
        for n in range(1, 15):
            r = optimal_iterations(n, 1)
            assert r >= prev, f"iterations should not decrease with n, got {r} < {prev}"
            prev = r

    def test_iterations_reduce_with_more_marked_states(self) -> None:
        for n in range(2, 8):
            r1 = optimal_iterations(n, 1)
            r2 = optimal_iterations(n, 2)
            assert r2 <= r1
            r4 = optimal_iterations(n, 4)
            assert r4 <= r2


class TestExpectedProbability:
    def test_single_marked_one_qubit(self) -> None:
        prob = expected_success_probability(1, 1, 1)
        assert prob == pytest.approx(0.5, abs=1e-10)

    def test_single_marked_two_qubits(self) -> None:
        prob = expected_success_probability(2, 1, 1)
        assert prob == pytest.approx(1.0, abs=1e-10)

    def test_single_marked_three_qubits(self) -> None:
        prob = expected_success_probability(3, 1, 2)
        assert prob == pytest.approx(0.945, abs=1e-2)

    def test_two_marked_four_qubits(self) -> None:
        prob = expected_success_probability(4, 2, 2)
        assert prob == pytest.approx(0.945, abs=1e-2)


class TestFullPipeline:
    @pytest.mark.parametrize("num_qubits,marked", [
        (2, "01"),
        (3, "110"),
        (4, "1011"),
    ])
    def test_marked_state_has_highest_probability(
        self, num_qubits: int, marked: str
    ) -> None:
        circuit = build_grover_circuit(num_qubits, marked)
        counts = run_ideal(circuit, shots=4096)

        marked_prob = extract_marked_probability(counts, marked)

        qiskit_marked = marked[::-1]
        other_probs = []
        for state, count in counts.items():
            if state != qiskit_marked:
                other_probs.append(count / 4096)

        assert marked_prob > 0.5, (
            f"Marked state |{marked}> has prob {marked_prob:.2%}, expected >50%"
        )
        if other_probs:
            assert marked_prob >= max(other_probs), (
                f"Marked state ({marked_prob:.2%}) should be highest prob"
            )

    def test_single_qubit_works(self) -> None:
        circuit = build_grover_circuit(1, "1")
        counts = run_ideal(circuit, shots=4096)
        prob = extract_marked_probability(counts, "1")
        assert prob > 0.45

    def test_circuit_name_is_informative(self) -> None:
        circuit = build_grover_circuit(3, "101", iterations=2)
        assert "Grover" in circuit.name
        assert "101" in circuit.name
        assert "3" in circuit.name
        assert "2" in circuit.name

    def test_circuit_name_with_multi_marked(self) -> None:
        circuit = build_grover_circuit(3, ["000", "111"], iterations=1)
        assert "000" in circuit.name
        assert "111" in circuit.name

    def test_both_states_marked_in_multi(self) -> None:
        circuit = build_grover_circuit(3, ["000", "111"])
        counts = run_ideal(circuit, shots=4096)
        prob = extract_marked_probability(counts, ["000", "111"])
        assert prob > 0.7, f"Combined marked probability {prob:.2%} should be >70%"

    def test_expected_probability_matches_simulation(self) -> None:
        n, marked, iters = 3, "101", 2
        circuit = build_grover_circuit(n, marked, iters)
        counts = run_ideal(circuit, shots=8192)
        empirical = extract_marked_probability(counts, marked)
        expected = expected_success_probability(n, 1, iters)
        assert abs(empirical - expected) < 0.05, (
            f"Empirical {empirical:.3f} vs expected {expected:.3f} diff > 0.05"
        )
