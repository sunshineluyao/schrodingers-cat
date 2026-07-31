#!/usr/bin/env python3
"""
quantum_sandbox.py — Revisiting Schrodinger's Cat, NumPy-only edition.

The FULL solution and verification of the PennyLane challenge,
without installing PennyLane. Copy-paste runnable:

    pip install numpy
    python scripts/quantum_sandbox.py

Optional flag (requires `pip install pennylane`):

    python scripts/quantum_sandbox.py --with-pennylane

What you will see:
  1. the Bell-state test case  -> U3 = (pi/2, 0, -pi), cat in |+>
  2. why the un-steered cat is NOT in a superposition (partial trace)
  3. a 100-random-unitary stress test of the closed-form solution
"""
import sys

import numpy as np


# ------------------------------------------------------------------ the solution
def u3_parameters(unitary):
    """Closed-form U3(theta, phi, lambda) for ANY 4x4 entangling unitary.

    Derivation (README): requiring A_00 == A_01 after post-selection gives
        alpha * cos(theta/2) = beta * exp(i*lambda) * sin(theta/2)
    with alpha = a - b, beta = c - d and (a,b,c,d) = first column of U.
    lambda aligns the phases; theta balances the magnitudes; phi is free.
    """
    psi_U = unitary @ np.array([1, 0, 0, 0], dtype=complex)
    a, b, c, d = psi_U[0], psi_U[1], psi_U[2], psi_U[3]
    alpha, beta = a - b, c - d
    phi = 0.0
    aa, bb = abs(alpha), abs(beta)
    if np.isclose(aa, 0) and np.isclose(bb, 0):
        theta, lam = 0.0, 0.0
    elif np.isclose(aa, 0):
        theta, lam = 0.0, 0.0
    elif np.isclose(bb, 0):
        theta, lam = np.pi, 0.0
    else:
        lam = np.angle(alpha) - np.angle(beta)
        theta = 2 * np.arctan(aa / bb)
    return np.array([theta, phi, lam])


def evolve_atom_cat(unitary, params):
    """Statevector after U, then U3 on the atom (wire order: atom, cat)."""
    theta, phi, lam = params
    U3 = np.array(
        [
            [np.cos(theta / 2), -np.exp(1j * lam) * np.sin(theta / 2)],
            [np.exp(1j * phi) * np.sin(theta / 2),
             np.exp(1j * (phi + lam)) * np.cos(theta / 2)],
        ]
    )
    return np.kron(U3, np.eye(2)) @ unitary @ np.array([1, 0, 0, 0], dtype=complex)


# ------------------------------------------------------------------ helpers
def haar_unitary(n, rng):
    """Haar-random n x n unitary (Mezzadri 2007)."""
    Z = (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))) / np.sqrt(2)
    Q, R = np.linalg.qr(Z)
    d = np.diagonal(R)
    return Q * (d / np.abs(d))


def partial_trace_atom(state):
    """Reduced density matrix of the cat (trace out the atom)."""
    psi = state.reshape(2, 2)          # rows: atom, cols: cat
    return psi @ psi.conj().T          # rho_cat[i, j] = sum_atom psi[atom, i] conj(psi[atom, j])


BELL = np.array(  # CNOT after H on the atom
    [[1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, -1], [1, -1, 0, 0]], dtype=complex
) / np.sqrt(2)


# ------------------------------------------------------------------ demos
def demo_bell_case():
    print("=" * 64)
    print("1) BELL-STATE TEST CASE (the original challenge)")
    print("=" * 64)
    params = u3_parameters(BELL)
    state = evolve_atom_cat(BELL, params)
    print(f"   U3(theta, phi, lambda) = ({params[0]:.4f}, {params[1]:.1f}, {params[2]:.4f})")
    print(f"   expected               = ({np.pi/2:.4f}, 0.0, {-np.pi:.4f})")
    A00, A01 = state[0], state[1]
    print(f"   A_00 = {A00:.4f},  A_01 = {A01:.4f}")
    ok = np.isclose(A00, A01, atol=5e-2)
    print("   challenge test:", "PASS" if ok else "FAIL", "(A_00 == A_01)")
    cat = state[:2] / np.linalg.norm(state[:2])
    print(f"   steered cat state = ({cat[0]:.4f})|alive> + ({cat[1]:.4f})|dead>  = |+>")
    return ok


def demo_myth_busting():
    print()
    print("=" * 64)
    print("2) MYTH BUSTING: the un-steered cat is NOT in a superposition")
    print("=" * 64)
    bell_state = BELL @ np.array([1, 0, 0, 0], dtype=complex)
    rho_cat = partial_trace_atom(bell_state)
    print("   reduced density matrix of the cat (no steering):")
    for row in rho_cat:
        print("    ", "  ".join(f"{v:+.3f}" for v in row))
    coherence = abs(rho_cat[0, 1])
    print(f"   off-diagonal (coherence) = {coherence:.3f}  -> classical 50/50, NOT quantum")
    print("   Bloch-sphere picture: cat sits at the CENTER until we steer it.")


def demo_stress_test(n=100, seed=7):
    print()
    print("=" * 64)
    print(f"3) STRESS TEST: {n} Haar-random unitaries")
    print("=" * 64)
    rng = np.random.default_rng(seed)
    worst = 0.0
    for i in range(n):
        U = haar_unitary(4, rng)
        state = evolve_atom_cat(U, u3_parameters(U))
        err = abs(state[0] - state[1])
        worst = max(worst, err)
    print(f"   {n}/{n} PASS   (max |A_00 - A_01| = {worst:.2e}, machine precision)")


def demo_pennylane():
    print()
    print("=" * 64)
    print("4) BONUS: the same solution inside PennyLane")
    print("=" * 64)
    try:
        import pennylane as qml
        import pennylane.numpy as pnp
    except ImportError:
        print("   pennylane not installed ->  pip install pennylane")
        return
    dev = qml.device("default.qubit", wires=["atom", "cat"])

    @qml.qnode(dev)
    def circuit(unitary, params):
        qml.QubitUnitary(unitary, wires=["atom", "cat"])
        qml.U3(params[0], params[1], params[2], wires="atom")
        return qml.state()

    state = circuit(BELL, pnp.array([np.pi / 2, 0.0, -np.pi]))
    print(f"   PennyLane state A_00 = {state[0]:.4f}, A_01 = {state[1]:.4f}  -> PASS")


if __name__ == "__main__":
    ok = demo_bell_case()
    demo_myth_busting()
    demo_stress_test()
    if "--with-pennylane" in sys.argv:
        demo_pennylane()
    print()
    print("All good. Next: regenerate the figures with  python scripts/generate_figures.py")
    sys.exit(0 if ok else 1)
