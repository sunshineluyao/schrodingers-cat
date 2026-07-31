#!/usr/bin/env python3
"""Self-contained dark-neon figure generation pipeline.

Generates all figures, animations and the hero banner for the
"Revisiting Schroedinger's Cat" PennyLane challenge solution repo.

Usage:
    python scripts/generate_figures.py --out assets
"""

import argparse
import os

import numpy as np

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)

# ---------------------------------------------------------------------------
# Design system (dark neon)
# ---------------------------------------------------------------------------

BG = "#0B1020"      # deep navy background
PANEL = "#16213B"   # panel fill
TXT = "#E2E8F0"     # main text
SUB = "#94A3B8"     # secondary text
CYAN = "#22D3EE"
MAGENTA = "#E879F9"
VIOLET = "#8B5CF6"
AMBER = "#FBBF24"
GREEN = "#34D399"
RED = "#EF4444"
BLUE = "#60A5FA"

BASIS_COLORS = [CYAN, MAGENTA, VIOLET, AMBER]
BASIS_LABELS = ["|00>", "|01>", "|10>", "|11>"]


def set_rcparams():
    """Global rcParams for the dark theme."""
    rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "savefig.facecolor": BG,
            "savefig.edgecolor": BG,
            "text.color": TXT,
            "axes.edgecolor": SUB,
            "axes.labelcolor": TXT,
            "xtick.color": SUB,
            "ytick.color": SUB,
            "font.size": 11,
            "font.family": "DejaVu Sans",
            "svg.fonttype": "none",
        }
    )


def style_ax_dark(ax, grid=True):
    """Apply the dark theme to a single axes."""
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color((1, 1, 1, 0.15))
    ax.tick_params(colors=SUB, labelcolor=SUB)
    ax.xaxis.label.set_color(TXT)
    ax.yaxis.label.set_color(TXT)
    ax.title.set_color(TXT)
    if grid:
        ax.grid(True, color=(1, 1, 1, 0.06), linewidth=0.8)
    ax.set_axisbelow(True)


def style_ax3d_dark(ax):
    """Apply the dark theme to a 3D axes."""
    ax.set_facecolor(BG)
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_facecolor((0, 0, 0, 0))
        pane.set_edgecolor((1, 1, 1, 0.08))
    ax.xaxis.set_tick_params(colors=SUB, labelcolor=SUB)
    ax.yaxis.set_tick_params(colors=SUB, labelcolor=SUB)
    ax.zaxis.set_tick_params(colors=SUB, labelcolor=SUB)
    ax.xaxis.label.set_color(TXT)
    ax.yaxis.label.set_color(TXT)
    ax.zaxis.label.set_color(TXT)
    ax.title.set_color(TXT)
    ax.xaxis._axinfo["grid"].update(color=(1, 1, 1, 0.06), linewidth=0.6)
    ax.yaxis._axinfo["grid"].update(color=(1, 1, 1, 0.06), linewidth=0.6)
    ax.zaxis._axinfo["grid"].update(color=(1, 1, 1, 0.06), linewidth=0.6)


def glow_line(ax, x, y, color, base_lw=1.8, zorder=5):
    """Draw a line three times for a neon glow."""
    ax.plot(x, y, color=color, lw=base_lw * 3.3, alpha=0.08, zorder=zorder - 2,
            solid_capstyle="round")
    ax.plot(x, y, color=color, lw=base_lw * 1.9, alpha=0.18, zorder=zorder - 1,
            solid_capstyle="round")
    ax.plot(x, y, color=color, lw=base_lw, alpha=1.0, zorder=zorder,
            solid_capstyle="round")


def glow_text(ax, x, y, s, color, fontsize=11, ha="center", va="center",
              weight="bold", zorder=8):
    """Text with a soft glow halo."""
    for lw, alpha in ((6, 0.10), (3, 0.20)):
        ax.text(x, y, s, color=color, fontsize=fontsize, ha=ha, va=va,
                weight=weight, zorder=zorder - 1, alpha=alpha,
                path_effects=[])
    ax.text(x, y, s, color=color, fontsize=fontsize, ha=ha, va=va,
            weight=weight, zorder=zorder)


# ---------------------------------------------------------------------------
# Circuit drawing helpers
# ---------------------------------------------------------------------------

def circuit_canvas(ax, n_wires, width):
    """Prepare a blank dark canvas for a circuit with n_wires wires."""
    ax.set_facecolor(BG)
    ax.set_xlim(0, width)
    ax.set_ylim(-0.8, n_wires - 1 + 0.9)
    ax.invert_yaxis()
    ax.axis("off")


def draw_wires(ax, n_wires, width, labels=None, colors=None, x0=0.9, x1=None):
    """Draw horizontal glowing wires with labels on the left.

    x1 may be a scalar or a per-wire list of end positions."""
    if x1 is None:
        x1 = width - 0.4
    if not hasattr(x1, "__len__"):
        x1 = [x1] * n_wires
    for w in range(n_wires):
        c = colors[w] if colors else SUB
        glow_line(ax, [x0, x1[w]], [w, w], color=(1, 1, 1, 0.5), base_lw=1.4)
        if labels:
            ax.text(x0 - 0.15, w, labels[w], color=c, fontsize=13, ha="right",
                    va="center", weight="bold")


def glow_box(ax, x, wire, width, height, color, label, fontsize=12,
             rounding=0.08, label_color="#FFFFFF"):
    """Neon gate box: FancyBboxPatch drawn three times for a glow."""
    x0, y0 = x - width / 2, wire - height / 2
    rs = rounding
    for pad_extra, lw, alpha, zorder in ((0.10, 6, 0.08, 4), (0.05, 3.5, 0.18, 5),
                                         (0.0, 1.8, 1.0, 6)):
        patch = FancyBboxPatch(
            (x0 - pad_extra, y0 - pad_extra),
            width + 2 * pad_extra,
            height + 2 * pad_extra,
            boxstyle=f"round,pad=0,rounding_size={rs}",
            linewidth=lw,
            edgecolor=color,
            facecolor=PANEL if alpha == 1.0 else "none",
            alpha=alpha,
            zorder=zorder,
        )
        ax.add_patch(patch)
    ax.text(x, wire, label, color=label_color, fontsize=fontsize, ha="center",
            va="center", weight="bold", zorder=7)


def cnot(ax, x, ctrl, tgt, color=MAGENTA):
    """Glowing CNOT: control dot on ctrl, target circle-plus on tgt."""
    # vertical connector
    glow_line(ax, [x, x], [ctrl, tgt], color=color, base_lw=1.6)
    # control dot
    for r, alpha, zo in ((0.14, 0.10, 5), (0.10, 0.25, 6), (0.06, 1.0, 7)):
        ax.scatter([x], [ctrl], s=1600 * r * 6, color=color, alpha=alpha,
                   zorder=zo, edgecolors="none")
    # target: circle with plus
    r = 0.16
    for rr, lw, alpha, zo in ((r * 1.9, 5, 0.08, 5), (r * 1.4, 3, 0.20, 6),
                              (r, 1.8, 1.0, 7)):
        circle = plt.Circle((x, tgt), rr, fill=(alpha == 1.0), facecolor=BG,
                            edgecolor=color, lw=lw, alpha=alpha, zorder=zo)
        ax.add_patch(circle)
    ax.plot([x - r * 0.75, x + r * 0.75], [tgt, tgt], color=color, lw=1.8,
            zorder=8)
    ax.plot([x, x], [tgt - r * 0.75, tgt + r * 0.75], color=color, lw=1.8,
            zorder=8)


def meter(ax, wire, x, color=SUB, size=0.42):
    """Measurement box with an arc + needle glyph."""
    glow_box(ax, x, wire, size, size * 0.78, color, "", rounding=0.06)
    t = np.linspace(np.pi * 0.15, np.pi * 0.85, 30)
    r = size * 0.22
    ax.plot(x + r * np.cos(t), wire + size * 0.05 + r * np.sin(t), color=color,
            lw=1.4, zorder=8)
    ax.plot([x, x + r * 0.7], [wire + size * 0.05, wire - size * 0.13],
            color=color, lw=1.4, zorder=8)


# ---------------------------------------------------------------------------
# Physics: exact state evolution and the closed-form solution
# ---------------------------------------------------------------------------

def bell_state_history():
    """Exact two-qubit state after each circuit step (wire order: atom, cat).

    Returns a list of 4 complex state vectors of length 4:
    step 0: |00>; step 1: H on atom; step 2: CNOT atom->cat (Bell state);
    step 3: U3(pi/2, 0, -pi) on atom, post-selected on atom = |0>,
    renormalized.
    """
    state0 = np.array([1, 0, 0, 0], dtype=complex)

    # U_BELL = CNOT . (H x I), basis (|00>,|01>,|10>,|11>)
    s = 1 / np.sqrt(2)
    u_bell = s * np.array(
        [
            [1, 1, 0, 0],
            [0, 0, 1, 1],
            [0, 0, 1, -1],
            [1, -1, 0, 0],
        ],
        dtype=complex,
    )
    state2 = u_bell @ state0  # Bell state (|00>+|11>)/sqrt(2)
    state1 = np.array([s, s, 0, 0], dtype=complex)  # after H on atom

    theta, phi, lam = np.pi / 2, 0.0, -np.pi
    u3 = np.array(
        [
            [np.cos(theta / 2), -np.exp(1j * lam) * np.sin(theta / 2)],
            [np.exp(1j * phi) * np.sin(theta / 2),
             np.exp(1j * (phi + lam)) * np.cos(theta / 2)],
        ],
        dtype=complex,
    )
    state3_full = np.kron(u3, np.eye(2)) @ state2
    kept = state3_full[:2]  # atom = |0> branch
    norm = np.linalg.norm(kept)
    state3 = np.zeros(4, dtype=complex)
    state3[:2] = kept / norm  # renormalized post-selected branch
    return [state0, state1, state2, state3]


def haar_unitary(rng):
    """Haar-random 4x4 unitary via the Mezzadri QR method."""
    z = (rng.standard_normal((4, 4)) + 1j * rng.standard_normal((4, 4))) / np.sqrt(2)
    q, r = np.linalg.qr(z)
    d = np.diagonal(r)
    return q * (d / np.abs(d))


def solve_parameters(u):
    """Closed-form steering parameters for any 4x4 unitary U.

    Let (a,b,c,d) be the first column of U; alpha = a-b, beta = c-d.
    lambda = arg(alpha)-arg(beta); theta = 2 arctan(|alpha|/|beta|); phi = 0.
    Degenerate cases: |beta|=0 -> theta=pi; |alpha|=0 -> theta=0.
    """
    a, b, c, d = u[:, 0]
    alpha, beta = a - b, c - d
    lam = np.angle(alpha) - np.angle(beta)
    eps = 1e-14
    if abs(beta) < eps:
        theta = np.pi
    elif abs(alpha) < eps:
        theta = 0.0
    else:
        theta = 2 * np.arctan(abs(alpha) / abs(beta))
    return theta, 0.0, lam


def u3_matrix(theta, phi, lam):
    """PennyLane U3 gate matrix."""
    return np.array(
        [
            [np.cos(theta / 2), -np.exp(1j * lam) * np.sin(theta / 2)],
            [np.exp(1j * phi) * np.sin(theta / 2),
             np.exp(1j * (phi + lam)) * np.cos(theta / 2)],
        ],
        dtype=complex,
    )


def verify_solution(u, theta, phi, lam):
    """Post-select atom=|0> after U3 on the atom and check the cat is |+>.

    Returns the verification error |A_00 - A_01| of the renormalized cat
    state in vector form (should be ~1e-16 for a perfect |+>).
    """
    state = u @ np.array([1, 0, 0, 0], dtype=complex)
    state3 = np.kron(u3_matrix(theta, phi, lam), np.eye(2)) @ state
    kept = state3[:2]
    norm = np.linalg.norm(kept)
    if norm < 1e-12:
        return np.inf
    cat = kept / norm
    return abs(cat[0] - cat[1])


def bloch_vector(rho):
    """Bloch vector of a 2x2 density matrix."""
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    return np.array(
        [np.real(np.trace(rho @ sx)),
         np.real(np.trace(rho @ sy)),
         np.real(np.trace(rho @ sz))]
    )


# ---------------------------------------------------------------------------
# Figure 1: the original challenge circuit
# ---------------------------------------------------------------------------

def fig1_original_circuit(outdir):
    fig, ax = plt.subplots(figsize=(8.6, 3.6), dpi=140)
    fig.patch.set_facecolor(BG)
    circuit_canvas(ax, 2, 10)
    draw_wires(ax, 2, 10, labels=["atom", "cat"], colors=[CYAN, MAGENTA])

    glow_box(ax, 2.2, 0, 0.7, 0.62, CYAN, "H", fontsize=14)
    cnot(ax, 4.0, 0, 1, color=MAGENTA)
    meter(ax, 1, 6.2, color=AMBER)

    ax.text(4.65, 0.45, "entangle", color=SUB, fontsize=9.5, ha="left")
    ax.annotate(
        "?",
        xy=(6.2, 1.52), fontsize=20, color=RED, weight="bold",
        ha="center", va="center",
    )
    ax.text(
        6.75, 1.52,
        "mixed state  $\\rho_C = I/2$\nNOT a superposition",
        color=RED, fontsize=11, ha="left", va="center", weight="bold",
    )
    ax.text(
        5.0, -0.68,
        "The original challenge circuit: entangle, then measure the cat",
        color=TXT, fontsize=12.5, ha="center", weight="bold",
    )
    ax.text(
        5.0, -0.44,
        "Tracing out the atom destroys all coherence - the cat is classical 50/50",
        color=SUB, fontsize=10, ha="center",
    )
    fig.savefig(os.path.join(outdir, "figures", "fig1_original_circuit.png"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    fig.savefig(os.path.join(outdir, "figures", "fig1_original_circuit.svg"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: the generalized solution circuit
# ---------------------------------------------------------------------------

def fig2_general_circuit(outdir):
    fig, ax = plt.subplots(figsize=(10.6, 4.0), dpi=140)
    fig.patch.set_facecolor(BG)
    circuit_canvas(ax, 2, 13)
    draw_wires(ax, 2, 13, labels=["atom", "cat"], colors=[CYAN, MAGENTA],
               x1=[7.7, 9.8])

    # Any 2-qubit unitary spanning both wires
    glow_box(ax, 2.6, 0.5, 1.35, 1.62, VIOLET, "U", fontsize=16)
    ax.text(2.6, 1.52, "any 2-qubit unitary", color=SUB, fontsize=9,
            ha="center", va="top")

    # U3 on the atom
    glow_box(ax, 5.1, 0, 1.7, 0.66, CYAN, "U3($\\theta,\\phi,\\lambda$)",
             fontsize=12)

    # meter on atom
    meter(ax, 0, 7.1, color=AMBER)

    # dashed arrow: post-selection info flows to the cat box
    arrow = FancyArrowPatch(
        (7.55, 0), (9.6, 1.0), connectionstyle="arc3,rad=-0.25",
        arrowstyle="-|>", mutation_scale=16, lw=1.8, color=GREEN,
        linestyle=(0, (4, 3)), zorder=6, alpha=0.95,
    )
    ax.add_patch(arrow)
    ax.text(8.85, 0.14, "post-select\natom = $|0\\rangle$", color=GREEN,
            fontsize=9.5, ha="center", va="center", weight="bold")

    # steered cat box
    glow_box(ax, 10.9, 1, 2.2, 0.66, MAGENTA, "= $|+\\rangle$ steered cat",
             fontsize=12)

    ax.text(
        6.5, -0.70,
        "The fix: one rotation on the atom + post-selection steers the cat",
        color=TXT, fontsize=12.5, ha="center", weight="bold",
    )
    ax.text(
        6.5, 1.80,
        "$\\lambda = \\arg(\\alpha) - \\arg(\\beta)$      "
        "$\\theta = 2\\,\\arctan(|\\alpha|/|\\beta|)$      $\\phi = 0$ (free)",
        color=CYAN, fontsize=11.5, ha="center",
    )
    fig.savefig(os.path.join(outdir, "figures", "fig2_general_circuit.png"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    fig.savefig(os.path.join(outdir, "figures", "fig2_general_circuit.svg"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Visualization: state evolution (static + animated)
# ---------------------------------------------------------------------------

STEP_TITLES = [
    "Start: $|00\\rangle$",
    "H on atom",
    "CNOT (entangle)",
    "U3 + post-select\natom = $|0\\rangle$",
]


def viz_state_evolution(outdir):
    states = bell_state_history()
    probs = [np.abs(s) ** 2 for s in states]

    fig, axes = plt.subplots(1, 4, figsize=(12.8, 4.0), dpi=140, sharey=True)
    fig.patch.set_facecolor(BG)
    x = np.arange(4)
    for i, (ax, p, title) in enumerate(zip(axes, probs, STEP_TITLES)):
        style_ax_dark(ax)
        bars = ax.bar(x, p, width=0.62, color=BASIS_COLORS,
                      edgecolor="none", zorder=5)
        for rect, col in zip(bars, BASIS_COLORS):
            rect.set_alpha(0.9)
        # glow rims on the bars
        for rect, col in zip(bars, BASIS_COLORS):
            ax.plot([rect.get_x(), rect.get_x() + rect.get_width()],
                    [rect.get_height()] * 2, color=col, lw=3, alpha=0.6,
                    zorder=6, solid_capstyle="round")
        ax.set_title(title, fontsize=10.5, color=TXT, pad=8)
        ax.set_xticks(x)
        if i == 0:
            ax.set_xticklabels(BASIS_LABELS, fontsize=9)
            ax.set_ylabel("Probability $|\\psi_i|^2$")
        else:
            ax.set_xticklabels(["00", "01", "10", "11"], fontsize=9)
        ax.set_ylim(0, 1.08)
    fig.suptitle("State evolution: from product state to steered cat",
                 color=TXT, fontsize=15, weight="bold", y=1.09)
    fig.text(0.5, 1.015,
             "After post-selecting atom = $|0\\rangle$, the kept branch "
             "renormalizes to the cat in $|+\\rangle$",
             color=SUB, fontsize=10.5, ha="center")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "figures", "viz_state_evolution.png"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


def anim_state_evolution(outdir):
    states = bell_state_history()
    probs = [np.abs(s) ** 2 for s in states]

    hold, trans = 18, 16
    segments = []  # (from, to, n_frames) interpolation schedule
    for i in range(len(probs) - 1):
        segments.append((i, i, hold))
        segments.append((i, i + 1, trans))
    segments.append((len(probs) - 1, len(probs) - 1, hold))

    schedule = []
    for a, b, n in segments:
        for k in range(n):
            t = k / max(n - 1, 1) if a != b else 0.0
            # smoothstep easing for transitions
            t = t * t * (3 - 2 * t)
            schedule.append((a, b, t))

    fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=90, facecolor=BG)
    fig.patch.set_facecolor(BG)
    style_ax_dark(ax)
    x = np.arange(4)
    bars = ax.bar(x, probs[0], width=0.6, color=BASIS_COLORS, zorder=5)
    step_text = ax.text(0.5, 1.04, STEP_TITLES[0].replace("\n", " "),
                        transform=ax.transAxes, color=TXT, fontsize=13,
                        weight="bold", ha="center")
    sub_text = ax.text(0.5, 0.975, "", transform=ax.transAxes, color=SUB,
                       fontsize=9.5, ha="center")
    ax.set_xticks(x)
    ax.set_xticklabels(BASIS_LABELS, fontsize=10)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Probability")

    SUBS = [
        "separable product state",
        "atom in superposition",
        "Bell state $(|00\\rangle+|11\\rangle)/\\sqrt{2}$",
        "cat steered to $|+\\rangle$",
    ]

    def update(frame):
        fig.patch.set_facecolor(BG)
        a, b, t = schedule[frame]
        p = (1 - t) * probs[a] + t * probs[b]
        for rect, h in zip(bars, p):
            rect.set_height(h)
        label_i = a if t < 0.5 else b
        step_text.set_text(STEP_TITLES[label_i].replace("\n", " "))
        sub_text.set_text(SUBS[label_i])
        return list(bars) + [step_text, sub_text]

    ani = FuncAnimation(fig, update, frames=len(schedule), interval=70,
                        blit=False)
    writer = PillowWriter(fps=14)
    ani.save(os.path.join(outdir, "anim", "state_evolution.gif"),
             writer=writer, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    return len(schedule)


# ---------------------------------------------------------------------------
# Bloch sphere helper
# ---------------------------------------------------------------------------

def draw_bloch(ax, vec=None, vec_color=CYAN, vec_label=None):
    """Draw a dark 3D Bloch sphere on ax. Optionally add a glowing state
    vector (Bloch vector, length <= 1)."""
    style_ax3d_dark(ax)
    ax.set_box_aspect((1, 1, 1))

    # translucent sphere surface
    u = np.linspace(0, 2 * np.pi, 46)
    v = np.linspace(0, np.pi, 26)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(xs, ys, zs, color=PANEL, alpha=0.10, linewidth=0,
                    shade=False, zorder=1)

    # wireframe latitudes and longitudes
    th = np.linspace(0, 2 * np.pi, 90)
    for lat in np.linspace(-np.pi / 2 + 0.3, np.pi / 2 - 0.3, 5):
        r = np.cos(lat)
        ax.plot(r * np.cos(th), r * np.sin(th), np.full_like(th, np.sin(lat)),
                color=(1, 1, 1, 0.12), lw=0.7, zorder=2)
    for lon in np.linspace(0, np.pi, 6, endpoint=False):
        ax.plot(np.cos(th) * np.cos(lon), np.cos(th) * np.sin(lon),
                np.sin(th), color=(1, 1, 1, 0.12), lw=0.7, zorder=2)
    # equator slightly brighter
    ax.plot(np.cos(th), np.sin(th), np.zeros_like(th),
            color=(1, 1, 1, 0.20), lw=0.9, zorder=2)

    # axes with ket labels
    L = 1.28
    ax.quiver(0, 0, 0, 0, 0, L, color=(1, 1, 1, 0.35), lw=1.0,
              arrow_length_ratio=0.08, zorder=3)
    ax.quiver(0, 0, 0, L, 0, 0, color=(1, 1, 1, 0.35), lw=1.0,
              arrow_length_ratio=0.08, zorder=3)
    ax.quiver(0, 0, 0, 0, L, 0, color=(1, 1, 1, 0.35), lw=1.0,
              arrow_length_ratio=0.08, zorder=3)
    labels = [
        ((0, 0, 1.42), "$|0\\rangle$", TXT),
        ((0, 0, -1.42), "$|1\\rangle$", TXT),
        ((1.45, 0, 0), "$|+\\rangle$", CYAN),
        ((-1.5, 0, 0), "$|-\\rangle$", CYAN),
        ((0, 1.48, 0), "$|+i\\rangle$", VIOLET),
        ((0, -1.55, 0), "$|-i\\rangle$", VIOLET),
    ]
    for pos, s, c in labels:
        ax.text(*pos, s, color=c, fontsize=10, ha="center", va="center",
                zorder=9)

    if vec is not None:
        vx, vy, vz = vec
        # 3-layer glowing quiver
        for lw, alpha in ((6.0, 0.08), (3.5, 0.18)):
            ax.quiver(0, 0, 0, vx, vy, vz, color=vec_color, lw=lw, alpha=alpha,
                      arrow_length_ratio=0.0, zorder=5)
        ax.quiver(0, 0, 0, vx, vy, vz, color=vec_color, lw=2.2, alpha=1.0,
                  arrow_length_ratio=0.12, zorder=6)
        ax.scatter([vx], [vy], [vz], s=90, color=vec_color, zorder=8,
                   edgecolors="white", linewidths=0.6)
        if vec_label:
            ax.text(vx * 0.5, vy * 0.5, vz * 0.5 + 0.28, vec_label,
                    color=vec_color, fontsize=10, weight="bold", ha="center",
                    zorder=9)

    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    ax.set_zlim(-1.25, 1.25)
    ax.set_xticks([]), ax.set_yticks([]), ax.set_zticks([])
    ax.view_init(elev=20, azim=-60)
    ax.set_axis_off()


def viz_bloch_myth_vs_reality(outdir):
    fig = plt.figure(figsize=(12.4, 6.2), dpi=130)
    fig.patch.set_facecolor(BG)
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")

    # Left: the myth - a pure |+> on the surface
    draw_bloch(ax1, vec=np.array([1.0, 0.0, 0.0]), vec_color=MAGENTA,
               vec_label="$|+\\rangle$ (surface)")
    ax1.set_title("Pop-culture myth", color=TXT, fontsize=14, weight="bold",
                  pad=14)
    ax1.text2D(0.5, 0.09, "X  wrong for the unmeasured cat",
               transform=ax1.transAxes, color=RED, fontsize=13, weight="bold",
               ha="center",
               bbox=dict(boxstyle="round,pad=0.35", facecolor=PANEL,
                         edgecolor=RED, linewidth=1.4, alpha=0.9))

    # Right: the reality - mixed state at the center
    draw_bloch(ax2)
    for s, alpha in ((380, 0.15), (200, 0.35), (110, 1.0)):
        ax2.scatter([0], [0], [0], s=s, color=RED, alpha=alpha, zorder=8,
                    edgecolors="none")
    ax2.text2D(0.5, 0.09, "$\\rho_C = I/2$ (mixed) - center, not surface",
               transform=ax2.transAxes, color=RED, fontsize=12, weight="bold",
               ha="center",
               bbox=dict(boxstyle="round,pad=0.35", facecolor=PANEL,
                         edgecolor=RED, linewidth=1.4, alpha=0.9))
    # faded ghost arrow showing the |+> that is NOT there
    ax2.quiver(0, 0, 0, 1.0, 0, 0, color=(1, 1, 1, 0.25), lw=1.4,
               linestyle="dashed", arrow_length_ratio=0.10, zorder=4)
    ax2.text(0.5, 0, -0.30, "no coherent superposition", color=SUB,
             fontsize=9, ha="center", zorder=9)
    ax2.set_title("Reality: unmeasured cat", color=TXT, fontsize=14,
                  weight="bold", pad=14)

    fig.suptitle("The unmeasured cat sits at the CENTER of the Bloch sphere - "
                 "classical 50/50, not alive-and-dead",
                 color=TXT, fontsize=14.5, weight="bold", y=0.98)
    fig.savefig(os.path.join(outdir, "figures", "viz_bloch_myth_vs_reality.png"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Animation: steering the cat onto the Bloch sphere
# ---------------------------------------------------------------------------

def _lerp_color(c1, c2, t):
    a = np.array(matplotlib.colors.to_rgb(c1))
    b = np.array(matplotlib.colors.to_rgb(c2))
    return tuple((1 - t) * a + t * b)


def anim_bloch_steering(outdir, n_frames=60):
    fig = plt.figure(figsize=(7.0, 6.0), dpi=90, facecolor=BG)
    fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111, projection="3d")
    draw_bloch(ax)
    ax.set_title("Quantum steering: pulling the cat onto the Bloch sphere",
                 color=TXT, fontsize=12.5, weight="bold", pad=10)

    # ghost of the target |+>
    ax.quiver(0, 0, 0, 1.0, 0, 0, color=(1, 1, 1, 0.18), lw=1.2,
              arrow_length_ratio=0.10, zorder=4)
    ax.text(1.06, 0, 0.12, "target $|+\\rangle$", color=SUB, fontsize=9,
            ha="center", zorder=9)

    state_dot = ax.scatter([0], [0], [0], s=110, color=RED, zorder=8,
                           edgecolors="none")
    state_dot._facecolor3d = np.array([[1, 0, 0, 1]])
    (vec_line,) = ax.plot([], [], [], lw=2.4, color=RED, zorder=6)
    (vec_glow1,) = ax.plot([], [], [], lw=6, color=RED, alpha=0.08, zorder=5)
    (vec_glow2,) = ax.plot([], [], [], lw=3.5, color=RED, alpha=0.18, zorder=5)
    # faint rotating arc hinting at the U3 rotation on the atom
    th = np.linspace(0, 2 * np.pi, 80)
    (arc_line,) = ax.plot([], [], [], lw=1.0, color=VIOLET, alpha=0.35,
                          zorder=4)
    rlabel = ax.text2D(0.5, 0.04, "", transform=ax.transAxes, color=TXT,
                       fontsize=11, ha="center", weight="bold")

    def update(frame):
        fig.patch.set_facecolor(BG)
        t = frame / (n_frames - 1)
        vec = np.array([t, 0.0, 0.0])
        if t < 0.5:
            color = _lerp_color(RED, AMBER, t / 0.5)
        else:
            color = _lerp_color(AMBER, GREEN, (t - 0.5) / 0.5)
        x, y, z = vec
        state_dot._offsets3d = ([x], [y], [z])
        state_dot.set_facecolor([color])
        state_dot.set_edgecolor([color])
        for line in (vec_line, vec_glow1, vec_glow2):
            line.set_data([0, x], [0, y])
            line.set_3d_properties([0, z])
            line.set_color(color)
        # rotating violet arc (the U3 acting on the atom)
        phase = 2 * np.pi * frame / n_frames
        arc_line.set_data(0.72 * np.cos(th + phase), 0.72 * np.sin(th + phase))
        arc_line.set_3d_properties(0.35 * np.sin(th))
        rlabel.set_text(f"steering progress: r = {t:.2f}")
        rlabel.set_color(color)
        return [state_dot, vec_line, vec_glow1, vec_glow2, arc_line, rlabel]

    ani = FuncAnimation(fig, update, frames=n_frames, interval=70, blit=False)
    ani.save(os.path.join(outdir, "anim", "bloch_steering.gif"),
             writer=PillowWriter(fps=14), savefig_kwargs={"facecolor": BG})
    plt.close(fig)


# ---------------------------------------------------------------------------
# Density-matrix city plots
# ---------------------------------------------------------------------------

def _bar3d_city(ax, mat, title):
    """3D bar 'city plot' of |mat_ij|; diagonals CYAN, off-diagonals MAGENTA."""
    style_ax3d_dark(ax)
    n = mat.shape[0]
    xs, ys, dzs, colors = [], [], [], []
    for i in range(n):
        for j in range(n):
            xs.append(i - 0.28)
            ys.append(j - 0.28)
            dzs.append(abs(mat[i, j]))
            colors.append(CYAN if i == j else MAGENTA)
    ax.bar3d(xs, ys, np.zeros(len(xs)), 0.56, 0.56, dzs, color=colors,
             alpha=0.92, shade=True, zorder=5)
    # glow edges
    for x, y, h, c in zip(xs, ys, dzs, colors):
        ax.plot([x, x + 0.56], [y, y], [h, h], color=c, lw=1.2, alpha=0.9)
    ax.set_xticks([0, 1]), ax.set_yticks([0, 1])
    ax.set_xticklabels(["$|0\\rangle$", "$|1\\rangle$"], fontsize=10)
    ax.set_yticklabels(["$\\langle0|$", "$\\langle1|$"], fontsize=10)
    ax.set_zlim(0, 0.62)
    ax.set_zlabel("$|\\rho_{ij}|$", fontsize=11)
    ax.set_title(title, color=TXT, fontsize=11.5, weight="bold", pad=12)
    ax.view_init(elev=28, azim=-58)


def viz_density_matrix_city(outdir):
    rho_unsteered = np.diag([0.5, 0.5])
    rho_steered = 0.5 * np.ones((2, 2))  # |+><+|

    fig = plt.figure(figsize=(12.4, 5.8), dpi=130)
    fig.patch.set_facecolor(BG)
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    _bar3d_city(ax1, rho_unsteered,
                "Before steering: $\\rho_C = I/2$ - classical 50/50")
    _bar3d_city(ax2, rho_steered,
                "After steering: $|+\\rangle\\langle+|$ - "
                "off-diagonals = coherence")
    fig.suptitle("Density matrix of the cat: steering creates coherence",
                 color=TXT, fontsize=15, weight="bold", y=1.00)
    fig.text(0.5, 0.925, "Diagonal bars (cyan) = populations · "
             "off-diagonal bars (magenta) = quantum coherence",
             color=SUB, fontsize=10.5, ha="center")
    fig.savefig(os.path.join(outdir, "figures", "viz_density_matrix_city.png"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Parameter analysis over 50 Haar-random unitaries
# ---------------------------------------------------------------------------

def viz_parameter_analysis(outdir, n=50):
    rng = np.random.default_rng(7)
    thetas, lams, errs = [], [], []
    for _ in range(n):
        u = haar_unitary(rng)
        theta, phi, lam = solve_parameters(u)
        err = verify_solution(u, theta, phi, lam)
        thetas.append(theta)
        lams.append(lam)
        errs.append(err)
    thetas = np.array(thetas)
    lams = np.array(lams)
    errs16 = np.array(errs) * 1e16

    fig = plt.figure(figsize=(14.6, 4.9), dpi=130)
    fig.patch.set_facecolor(BG)

    axa = fig.add_subplot(1, 3, 1)
    style_ax_dark(axa)
    axa.hist(thetas, bins=14, color=CYAN, alpha=0.85, edgecolor=BG)
    axa.set_xlabel(r"$\theta$ (rad)")
    axa.set_ylabel("count")
    axa.set_title(r"Distribution of solved $\theta$", fontsize=11.5, pad=8)
    axa.axvline(np.pi / 2, color=AMBER, lw=1.4, ls="--", alpha=0.8)

    axb = fig.add_subplot(1, 3, 2)
    style_ax_dark(axb)
    axb.hist(lams, bins=14, color=MAGENTA, alpha=0.85, edgecolor=BG)
    axb.set_xlabel(r"$\lambda$ (rad)")
    axb.set_ylabel("count")
    axb.set_title(r"Distribution of solved $\lambda$", fontsize=11.5, pad=8)

    axc = fig.add_subplot(1, 3, 3, projection="3d")
    style_ax3d_dark(axc)
    # translucent "cylinder": scatter on theta/lambda cylinder coords
    axc.scatter(thetas, lams, errs16, s=52, color=VIOLET, alpha=0.95,
                edgecolors="white", linewidths=0.4, depthshade=False,
                zorder=6)
    axc.scatter(thetas, lams, errs16, s=150, color=VIOLET, alpha=0.12,
                edgecolors="none", depthshade=False, zorder=5)
    axc.set_xlabel(r"$\theta$", fontsize=10, labelpad=6)
    axc.set_ylabel(r"$\lambda$", fontsize=10, labelpad=6)
    axc.set_zlabel(r"error $\times 10^{16}$", fontsize=10, labelpad=6)
    axc.set_title(r"$(\theta,\lambda)$ vs verification error", fontsize=11.5,
                  pad=8)
    axc.set_zlim(0, max(errs16.max() * 1.4, 4.0))
    axc.view_init(elev=22, azim=-55)

    fig.suptitle("Solved parameters for 50 random unitaries - all errors at "
                 "machine precision", color=TXT, fontsize=15, weight="bold",
                 y=1.04)
    fig.text(0.5, 0.965,
             r"$\lambda = \arg(\alpha) - \arg(\beta)$   ·   "
             r"$\theta = 2\,\arctan(|\alpha|/|\beta|)$   ·   "
             r"error $= |A_{00} - A_{01}|$ after renormalization",
             color=SUB, fontsize=10.5, ha="center")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "figures", "viz_parameter_analysis.png"),
                facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return float(np.max(errs))


# ---------------------------------------------------------------------------
# Hero banner (SVG)
# ---------------------------------------------------------------------------

def hero_banner(outdir):
    fig = plt.figure(figsize=(12, 4), dpi=128)
    fig.patch.set_facecolor(BG)

    # Left: mini circuit
    axc = fig.add_axes([0.035, 0.10, 0.30, 0.80])
    circuit_canvas(axc, 2, 9)
    draw_wires(axc, 2, 9, labels=["atom", "cat"], colors=[CYAN, MAGENTA],
               x1=7.4)
    glow_box(axc, 1.8, 0.5, 1.05, 1.55, VIOLET, "U", fontsize=13)
    glow_box(axc, 3.9, 0, 1.5, 0.62, CYAN, "U3", fontsize=12)
    meter(axc, 0, 5.5, color=AMBER, size=0.4)
    arrow = FancyArrowPatch(
        (5.95, 0), (7.1, 1.0), connectionstyle="arc3,rad=-0.3",
        arrowstyle="-|>", mutation_scale=12, lw=1.5, color=GREEN,
        linestyle=(0, (4, 3)), zorder=6,
    )
    axc.add_patch(arrow)
    glow_box(axc, 8.0, 1, 1.15, 0.6, MAGENTA, "$|+\\rangle$", fontsize=12)
    glow_line(axc, [7.4, 7.45], [1, 1], color=(1, 1, 1, 0.5), base_lw=1.4)

    # Right: titles
    axt = fig.add_axes([0.36, 0.0, 0.62, 1.0])
    axt.set_facecolor(BG)
    axt.axis("off")
    glow_text(axt, 0.02, 0.70, "Revisiting Schrödinger's Cat", TXT,
              fontsize=31, ha="left", weight="bold")
    axt.text(0.02, 0.44,
             "Any entangler U · one rotation U3(θ,φ,λ) · a steered |+⟩ cat",
             color=SUB, fontsize=15, ha="left", va="center")
    axt.text(0.02, 0.22,
             "PennyLane challenge · closed-form solution · 100/100 random tests",
             color=CYAN, fontsize=13.5, ha="left", va="center", weight="bold")

    fig.savefig(os.path.join(outdir, "hero", "banner.svg"), facecolor=BG,
                bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build_all(outdir):
    set_rcparams()
    for sub in ("figures", "anim", "hero"):
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)

    saved = []

    fig1_original_circuit(outdir)
    saved += [os.path.join(outdir, "figures", f)
              for f in ("fig1_original_circuit.png", "fig1_original_circuit.svg")]

    fig2_general_circuit(outdir)
    saved += [os.path.join(outdir, "figures", f)
              for f in ("fig2_general_circuit.png", "fig2_general_circuit.svg")]

    viz_state_evolution(outdir)
    saved.append(os.path.join(outdir, "figures", "viz_state_evolution.png"))

    viz_bloch_myth_vs_reality(outdir)
    saved.append(os.path.join(outdir, "figures", "viz_bloch_myth_vs_reality.png"))

    viz_density_matrix_city(outdir)
    saved.append(os.path.join(outdir, "figures", "viz_density_matrix_city.png"))

    max_err = viz_parameter_analysis(outdir)
    saved.append(os.path.join(outdir, "figures", "viz_parameter_analysis.png"))

    n_frames = anim_state_evolution(outdir)
    saved.append(os.path.join(outdir, "anim", "state_evolution.gif"))

    anim_bloch_steering(outdir)
    saved.append(os.path.join(outdir, "anim", "bloch_steering.gif"))

    hero_banner(outdir)
    saved.append(os.path.join(outdir, "hero", "banner.svg"))

    print(f"[check] max verification error over 50 random unitaries: "
          f"{max_err:.3e}")
    print(f"[check] state-evolution animation frames: {n_frames}")
    for path in saved:
        print(f"saved: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate all dark-neon figures for the "
                    "schrodingers-cat repo."
    )
    parser.add_argument("--out", default="assets",
                        help="output directory (default: assets)")
    args = parser.parse_args()
    build_all(args.out)


if __name__ == "__main__":
    main()
