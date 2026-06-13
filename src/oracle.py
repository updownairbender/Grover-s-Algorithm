from qiskit import QuantumCircuit
from qiskit.circuit.library import ZGate


def create_oracle(num_qubits: int, marked_state: str) -> QuantumCircuit:
    if len(marked_state) != num_qubits:
        raise ValueError(
            f"marked_state '{marked_state}' length {len(marked_state)} "
            f"does not match num_qubits={num_qubits}"
        )
    if not all(b in "01" for b in marked_state):
        raise ValueError(f"marked_state must be a binary string, got '{marked_state}'")

    oracle = QuantumCircuit(num_qubits, name=f"Oracle(|{marked_state})")

    for i, bit in enumerate(marked_state):
        if bit == "0":
            oracle.x(i)

    if num_qubits == 1:
        oracle.z(0)
    else:
        mcz = ZGate().control(num_qubits - 1)
        oracle.append(mcz, range(num_qubits))

    for i, bit in enumerate(marked_state):
        if bit == "0":
            oracle.x(i)

    return oracle


def create_multi_oracle(num_qubits: int, marked_states: list[str]) -> QuantumCircuit:
    if not marked_states:
        raise ValueError("marked_states must be a non-empty list")
    if not all(isinstance(s, str) for s in marked_states):
        raise ValueError("each marked state must be a string")

    name = f"Oracle({','.join(f'|{s}>' for s in marked_states)})"
    oracle = QuantumCircuit(num_qubits, name=name)
    for state in marked_states:
        single = create_oracle(num_qubits, state)
        oracle.compose(single, range(num_qubits), inplace=True)
    return oracle
