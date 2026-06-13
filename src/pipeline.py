import math
import os

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_aer.noise.errors import depolarizing_error, pauli_error

from src.oracle import create_oracle, create_multi_oracle
from src.diffuser import create_diffuser


def optimal_iterations(num_qubits: int, num_marked: int = 1) -> int:
    N = 2**num_qubits
    theta = math.asin(math.sqrt(num_marked / N))
    R = (math.pi / 2 - theta) / (2 * theta)
    return max(1, round(R))


def _normalize_states(marked_states: str | list[str]) -> list[str]:
    if isinstance(marked_states, str):
        return [marked_states]
    return marked_states


def build_grover_circuit(
    num_qubits: int,
    marked_states: str | list[str],
    iterations: int | None = None,
) -> QuantumCircuit:
    states = _normalize_states(marked_states)
    num_marked = len(states)

    if iterations is None:
        iterations = optimal_iterations(num_qubits, num_marked)

    qc = QuantumCircuit(num_qubits, num_qubits)

    qc.h(range(num_qubits))

    oracle = create_multi_oracle(num_qubits, states) if num_marked > 1 else create_oracle(num_qubits, states[0])
    diffuser = create_diffuser(num_qubits)

    for _ in range(iterations):
        qc.compose(oracle, range(num_qubits), inplace=True)
        qc.compose(diffuser, range(num_qubits), inplace=True)

    qc.measure(range(num_qubits), range(num_qubits))

    label = ",".join(states) if num_marked > 1 else states[0]
    qc.name = f"Grover({num_qubits}q,|{label}>,{iterations}iters)"
    return qc.decompose(reps=3)


NOISE_MODEL = NoiseModel()
ERROR_1Q = depolarizing_error(0.001, 1)
ERROR_2Q = depolarizing_error(0.01, 2)
NOISE_MODEL.add_all_qubit_quantum_error(ERROR_1Q, ["u1", "u2", "u3"])
NOISE_MODEL.add_all_qubit_quantum_error(ERROR_2Q, ["cx"])

READOUT_ERROR = pauli_error([("X", 0.02), ("I", 0.98)])
NOISE_MODEL.add_all_qubit_quantum_error(READOUT_ERROR, ["measure"])


def _transpile(circuit: QuantumCircuit, backend: AerSimulator) -> QuantumCircuit:
    pm = generate_preset_pass_manager(backend=backend, optimization_level=0)
    return pm.run(circuit)


def run_ideal(
    circuit: QuantumCircuit,
    shots: int = 8192,
) -> dict:
    backend = AerSimulator()
    t_circuit = _transpile(circuit, backend)
    result = backend.run(t_circuit, shots=shots).result()
    return result.get_counts()


def run_noisy(
    circuit: QuantumCircuit,
    noise_model: NoiseModel | None = None,
    shots: int = 8192,
) -> dict:
    if noise_model is None:
        noise_model = NOISE_MODEL
    backend = AerSimulator(noise_model=noise_model)
    t_circuit = _transpile(circuit, backend)
    result = backend.run(t_circuit, shots=shots).result()
    return result.get_counts()


def compute_probabilities(counts: dict, num_qubits: int) -> dict:
    total = sum(counts.values())
    probs = {}
    for i in range(2**num_qubits):
        state = format(i, f"0{num_qubits}b")
        qiskit_key = state[::-1]
        probs[state] = counts.get(qiskit_key, 0) / total
    return probs


def extract_marked_probability(
    counts: dict,
    marked_states: str | list[str],
) -> float:
    total = sum(counts.values())
    states = _normalize_states(marked_states)
    marked_counts = sum(counts.get(s[::-1], 0) for s in states)
    return marked_counts / total


def expected_success_probability(num_qubits: int, num_marked: int, iterations: int) -> float:
    N = 2**num_qubits
    theta = math.asin(math.sqrt(num_marked / N))
    return math.sin((2 * iterations + 1) * theta) ** 2


def save_circuit_diagram(
    circuit: QuantumCircuit,
    filepath: str = "outputs/circuit_diagram.png",
) -> None:
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    fold = 80
    if filepath.lower().endswith(".png"):
        circuit.draw(output="mpl", filename=filepath, fold=fold, scale=0.8)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(circuit.draw(output="text", fold=fold)))
