# Quantum Computing 101 — Zero-Prerequisites Guide

*For readers who have never touched quantum computing. No math beyond "50%" is required.*
*面向完全没有量子计算背景的读者：只需要"抛硬币"的直觉。*

---

## 中文速览（三分钟版）

> **流行文化版故事是错的。** 流传的"薛定谔的猫既死又活"把两件事搞混了：
>
> 1. **叠加态（superposition）**：一枚**正在旋转的硬币**——它真的同时具有正反两面的性质，旋转方向（相位）携带信息。
> 2. **经典不确定（mixed state）**：一枚**扣在碗底下的硬币**——它**早已**是正或反，只是你没看。
>
> 原子和猫纠缠在一起之后，没被测量的猫属于**第二种**：碗底下的硬币，不是旋转的硬币。用 Bloch 球（一个"地球仪"）来说：**纯态在球面上，混合态在球心**——猫待在球心。
>
> **本仓库做的事**：换一个角度去"看"那个原子（换测量基），猫就被" steering（引导）"到了球面上——**真正的既死又活**。而且我们给出了对**任意**纠缠过程都成立的解析公式，100 个随机测试全部通过，误差在机器精度（10⁻¹⁶）量级。
>
> **想动手？** 不需要量子计算机。普通笔记本就能模拟。复制 README 里的代码，或者运行 `python scripts/quantum_sandbox.py`（只需 numpy）。

---

## 1. The five ideas you need (coin analogies)

| Quantum concept | Coin analogy | What it means here |
|---|---|---|
| **Qubit** | A coin that can spin | The atom (or cat) — it has two basic outcomes, $|0\rangle$ and $|1\rangle$ |
| **Superposition** | A coin *spinning in the air* | Genuinely both at once; the spin direction ("phase") carries information |
| **Mixed state** | A coin *under a cup* | Already heads OR tails — you just haven't looked. No phase information |
| **Entanglement** | Two magic coins that always land matching | Atom and cat become one joint system: you cannot describe them separately |
| **Measurement basis** | The angle from which you grab the spinning coin | Grabbing differently (rotated basis) reveals — and creates — different states |

And one map: the **Bloch sphere** is a globe where every *pure* state is a point on the surface, the *center* is the completely mixed state (cup-covered coin), and the distance from the center measures **coherence** (how "quantum" the state is).

## 2. The cat story, retold honestly

**Pop-culture version:** the atom is a spinning coin, so the cat is also a spinning coin — alive AND dead.

**Why it fails:** the atom and the cat are *entangled*. Once two systems entangle, each one **individually** loses its spin — mathematically, the cat's state is the mixed state $\rho_C = \mathrm{diag}(1/2, 1/2)$. The *joint* atom-cat system is quantum (a Bell state); the *cat alone* is classical. "Tracing out" the atom is like looking only at one of the two magic coins: it just looks like a cup-covered coin.

**The rescue (what this repo does):** the same entanglement that destroys the cat's coherence can be used to restore it. If you measure the *atom* along a rotated direction (implemented by the $U3(\theta,\phi,\lambda)$ gate) and keep only the runs where the atom comes out $|0\rangle$, the cat is **steered** onto the Bloch sphere's surface — a genuine $|+\rangle = (|\text{alive}\rangle+|\text{dead}\rangle)/\sqrt{2}$ superposition. This technique is called **quantum steering via post-selection**, and it is how real "Schrödinger cat states" are prepared in labs (with photons, ions, and superconducting circuits — the "cats" are quantum systems, not pets).

**The challenge solved here:** for *any* entangling process $U$, which rotation angles $(\theta,\phi,\lambda)$ do the trick? Answer: a closed formula, derived in the README, verified on 100 random unitaries.

## 3. FAQ

**Is the cat really alive and dead at the same time?**
Only *after* steering — and only in the quantum sense (a spinning coin). Before steering, it is simply "alive or dead, we don't know yet" (a cup-covered coin). The whole point of this repo is the difference between those two sentences.

**Do I need a quantum computer to run this code?**
No. Two qubits are trivially simulated on any laptop. `default.qubit` in PennyLane is a simulator; the NumPy-only sandbox script doesn't even need PennyLane.

**What is a "unitary"?**
A rule for how the spinning coin evolves — a rotation-like operation that never loses information. The challenge lets *any* two-qubit unitary entangle the atom and the cat.

**Why does measuring the atom change the cat?**
Because they are entangled: the measurement outcome of the atom tells you something about the joint state, and keeping only one outcome reshapes ("steers") what is left on the cat's side. Nothing travels between them; the correlation was established when they interacted.

**Where does the formula come from?**
Requiring the two post-selection amplitudes to be equal, $A_{00}=A_{01}$, gives one complex equation. $\lambda$ fixes the phase, $\theta$ fixes the magnitude, $\phi$ turns out to be irrelevant. Full derivation: README → "The mathematical solution".

## 4. Your first 5 lines of quantum code

Copy-paste (needs only `pip install pennylane`):

```python
import pennylane as qml

dev = qml.device("default.qubit", wires=1)

@qml.qnode(dev)
def spin_the_coin():
    qml.Hadamard(wires=0)        # put the qubit into superposition
    return qml.probs(wires=0)    # measurement statistics

print(spin_the_coin())           # [0.5 0.5] — a genuine spinning coin
```

Expected output: `[0.5 0.5]`. Congratulations — you just created a superposition.
Next step: run `python scripts/quantum_sandbox.py` in this repo to steer the cat.

## 5. Learning path (all free)

1. **This repo** — 30 minutes: read the README story, run the sandbox script.
2. **PennyLane Codebook** (pennylane.ai/codebook) — interactive, hands-on, zero setup.
3. **IBM Quantum Learning** (learning.quantum.ibm.com) — free courses + real quantum hardware in the browser.
4. **"Quantum Computing for the Very Curious"** (quantum.country) — Matuschak & Nielsen's mnemonic essay; the best gentle deep-dive.
5. **Nielsen & Chuang**, chapters 1–2 — the standard textbook once you want the real linear algebra.
6. 中文补充：中国大学 MOOC / B 站搜索"量子计算入门"（中科大、清华均有免费公开课）。

## 6. Glossary

| Term | One-line meaning |
|---|---|
| **Qubit** | Quantum bit: $|0\rangle$, $|1\rangle$, or any superposition of them |
| **Superposition** | A spinning-coin state: $\alpha|0\rangle+\beta|1\rangle$ with usable phase |
| **Entanglement** | Joint state of two systems that cannot be described separately |
| **Bell state** | The maximally entangled pair $(|00\rangle+|11\rangle)/\sqrt{2}$ |
| **Density matrix** | The general description of a quantum state, pure or mixed |
| **Partial trace** | Ignoring one half of an entangled pair; turns pure into mixed |
| **Mixed state** | A cup-covered coin: classical probabilities, zero coherence |
| **U3 gate** | The most general single-qubit rotation, 3 angles $(\theta,\phi,\lambda)$ |
| **Post-selection** | Keeping only the runs with a chosen measurement outcome |
| **Quantum steering** | Reshaping one half of an entangled pair by measuring the other |
| **Bloch sphere** | The globe of qubit states: surface = pure, center = mixed |

---

*Back to the [README](../README.md). Found this helpful? Star the repo — it helps other beginners find it.*
