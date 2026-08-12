---
title: Did We Really Prepare the Quantum Cat?
emoji: 🐈
colorFrom: purple
colorTo: indigo
sdk: static
app_file: index.html
fullWidth: true
header: mini
pinned: false
license: mit
short_description: 12-question quantum steering and physical validity OER
tags:
  - quantum-computing
  - education
  - pennylane
---

# Did We Really Prepare the Quantum Cat?

This self-contained static Open Educational Resource (OER) is a beginner-friendly
follow-up to PennyLane's *Revisiting Schrödinger's Cat* challenge.

The original challenge asks for a measurement basis that makes two amplitudes in
the post-selected atom-0 branch equal. This OER develops that task into the same
12-question Socratic path as the repository README: from the cat's reduced state
and quantum steering through the closed-form solution, physical-validity audit,
reproducibility, provenance, citation, and final evidence synthesis.

The complete physical-validity check reports:

1. the original complex-amplitude equality residual;
2. the post-selection probability, `p₀`; and
3. the conditional fidelity with the target cat state, `F`.

Interactive features include a mixed-vs-pure state explorer, a four-step steering
walkthrough, circuit comparison, live analytical U3 solver, amplitude verdict lab,
seeded 1/50/100-sample numerical stress test, deterministic boundary-case
comparator, reproduction routes, repository map, provenance timeline, citation
tools, persistent question progress, and a final three-evidence matching challenge.

The OER remains self-contained: one static page, the repository's existing visual
assets, no backend, and no external JavaScript dependency.

## Local preview

From the repository root:

```bash
python3 -m http.server 8000 --directory oer
```

Then open <http://localhost:8000>.

## Source and context

- [Original challenge solution repository](https://github.com/sunshineluyao/schrodingers-cat)
- [PennyLane challenge statement](https://pennylane.ai/challenges/schrodingers_cat)
- [Interactive Space](https://huggingface.co/spaces/zlysunshine/did-we-really-prepare-the-quantum-cat)

This educational follow-up is not an official PennyLane publication.
