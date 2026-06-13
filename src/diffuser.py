from qiskit import QuantumCircuit
from qiskit.circuit.library import ZGate


def create_diffuser(num_qubits: int) -> QuantumCircuit:
    diffuser = QuantumCircuit(num_qubits, name="Diffuser")

    diffuser.h(range(num_qubits))
    diffuser.x(range(num_qubits))

    if num_qubits == 1:
        diffuser.z(0)
    else:
        mcz = ZGate().control(num_qubits - 1)
        diffuser.append(mcz, range(num_qubits))

    diffuser.x(range(num_qubits))
    diffuser.h(range(num_qubits))

    return diffuser
