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
short_description: A zero-prerequisite OER on post-selection and physical validity.
tags:
  - quantum-computing
  - education
  - pennylane
---

# Did We Really Prepare the Quantum Cat?

This self-contained static Open Educational Resource (OER) is a beginner-friendly
follow-up to PennyLane's *Revisiting Schrödinger's Cat* challenge.

The original challenge asks for a measurement basis that makes two amplitudes in
the post-selected atom-0 branch equal. This OER asks one additional physical
question: **does that branch occur with non-zero probability?**

The complete validity check reports both:

1. the post-selection probability, `p₀`; and
2. the conditional fidelity with the target cat state, `F`.

The OER is intentionally small: one page, two fixed examples, one understanding
check, and no backend or external JavaScript dependencies.

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
