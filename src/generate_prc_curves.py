"""Generate Precision-Recall Curves for Edward (V20) vs Edward+Salah (V22) across all sets."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

SETS = {
    "modern": {
        "v20": os.path.join(BASE, "Salah", "modern", "SM_V20_EDWARD_ONLY.csv"),
        "v22": os.path.join(BASE, "Salah", "modern", "SM_V22_EDWARD_SALAH.csv"),
        "label": "Modern Era (Post-1999)",
    },
    "global": {
        "v20": os.path.join(BASE, "Salah", "global", "SM_V20_EDWARD_ONLY_GLOBAL.csv"),
        "v22": os.path.join(BASE, "Salah", "global", "SM_V22_EDWARD_SALAH_GLOBAL.csv"),
        "label": "Global (All Molecules)",
    },
    "legacy": {
        "v20": os.path.join(BASE, "Salah", "legacy", "SM_V20_EDWARD_ONLY_LEGACY.csv"),
        "v22": os.path.join(BASE, "Salah", "legacy", "SM_V22_EDWARD_SALAH_LEGACY.csv"),
        "label": "Legacy (Pre-1999)",
    },
}


def make_y_true(df):
    """Binary label: approved=1, everything else=0."""
    return (df["category"] == "approved").astype(int)


def score_to_prob(scores):
    """Lower Edward Score = better drug → higher predicted P(approved)."""
    return 1 - scores / 100


def plot_prc(ax, df_v20, df_v22, title, n):
    y_true = make_y_true(df_v22)
    n_pos = y_true.sum()
    n_neg = len(y_true) - n_pos
    baseline = n_pos / len(y_true)

    # V20 — Edward Only
    v20_scores = score_to_prob(df_v20["Edward Score V20"])
    prec_v20, rec_v20, _ = precision_recall_curve(y_true, v20_scores)
    ap_v20 = average_precision_score(y_true, v20_scores)

    # V22 — Edward + Salah
    v22_scores = score_to_prob(df_v22["Edward Score V22"])
    prec_v22, rec_v22, _ = precision_recall_curve(y_true, v22_scores)
    ap_v22 = average_precision_score(y_true, v22_scores)

    ax.plot(rec_v20, prec_v20, color="#B0B0B0", linewidth=1.5, linestyle="--",
            label=f"Edward (No Biology) AP: {ap_v20:.3f}")
    ax.plot(rec_v22, prec_v22, color="#4A90E2", linewidth=2.2,
            label=f"Edward + Salah (Coordinated) AP: {ap_v22:.3f}")
    ax.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
               label=f"Random (baseline: {baseline:.2f})")

    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.set_title(f"PRC: Edward vs Edward+Salah — {title} (N={n})", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.grid(True, alpha=0.2)


# ── Generate per-set PRC plots ─────────────────────────────────────────────
for key, cfg in SETS.items():
    df_v20 = pd.read_csv(cfg["v20"])
    df_v22 = pd.read_csv(cfg["v22"])
    n = len(df_v22)

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor("white")
    plot_prc(ax, df_v20, df_v22, cfg["label"], n)

    out_path = os.path.join(BASE, "Salah", key, "sm_edward_vs_edward_salah_prc.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


# ── Combined 3-panel figure ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
fig.patch.set_facecolor("white")

for ax, (key, cfg) in zip(axes, SETS.items()):
    df_v20 = pd.read_csv(cfg["v20"])
    df_v22 = pd.read_csv(cfg["v22"])
    plot_prc(ax, df_v20, df_v22, cfg["label"], len(df_v22))

fig.suptitle("Precision-Recall Curves — Edward vs Edward+Salah", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()

combined_path = os.path.join(BASE, "Salah", "prc_all_sets_combined.png")
fig.savefig(combined_path, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {combined_path}")

print("\nDone!")
