"""Generate ROC curve comparing V20, V22, V23 on Modern SM set."""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

V20_FILE = os.path.join(BASE, "Salah", "modern", "SM_V20_EDWARD_ONLY.csv")
V22_FILE = os.path.join(BASE, "Salah", "modern", "SM_V22_EDWARD_SALAH.csv")
V23_FILE = os.path.join(BASE, "Salah", "modern", "SM_V23_EDWARD_SALAH.csv")

OUT_ROC = os.path.join(BASE, "Salah", "modern", "sm_v20_v22_v23_roc.png")
OUT_PRC = os.path.join(BASE, "Salah", "modern", "sm_v20_v22_v23_prc.png")


def load_and_align():
    df_v20 = pd.read_csv(V20_FILE)
    df_v22 = pd.read_csv(V22_FILE)
    df_v23 = pd.read_csv(V23_FILE)

    # Use category from V22 (same molecules, same labels)
    y_true = (df_v22["category"] == "approved").astype(int)

    v20_scores = pd.to_numeric(df_v20["Edward Score V20"], errors="coerce")
    v22_scores = pd.to_numeric(df_v22["Edward Score V22"], errors="coerce")
    v23_scores = pd.to_numeric(df_v23["Edward Score V23"], errors="coerce")

    return y_true, v20_scores, v22_scores, v23_scores


def main():
    y_true, v20, v22, v23 = load_and_align()
    n = len(y_true)
    n_pos = y_true.sum()

    # ── ROC Curve ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")

    for scores, label, color, lw, ls in [
        (v20, "V20 (Edward Only)", "#B0B0B0", 1.5, "--"),
        (v22, "V22 (Edward + Salah)", "#4A90E2", 2.0, "-"),
        (v23, "V23 (Calibrated Alerts)", "#2ECC71", 2.5, "-"),
    ]:
        pred = 101 - scores  # lower score = better → higher pred
        fpr, tpr, _ = roc_curve(y_true, pred)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, lw=lw, ls=ls,
                label=f"{label}  AUC: {roc_auc:.3f}")

    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC: V20 vs V22 vs V23 — Modern SM (N={n}, {n_pos} approved)", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.02])

    fig.savefig(OUT_ROC, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {OUT_ROC}")

    # ── PRC Curve ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    baseline = n_pos / n

    for scores, label, color, lw, ls in [
        (v20, "V20 (Edward Only)", "#B0B0B0", 1.5, "--"),
        (v22, "V22 (Edward + Salah)", "#4A90E2", 2.0, "-"),
        (v23, "V23 (Calibrated Alerts)", "#2ECC71", 2.5, "-"),
    ]:
        pred = 1 - scores / 100
        prec, rec, _ = precision_recall_curve(y_true, pred)
        ap = average_precision_score(y_true, pred)
        ax.plot(rec, prec, color=color, lw=lw, ls=ls,
                label=f"{label}  AP: {ap:.3f}")

    ax.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
               label=f"Random (baseline: {baseline:.2f})")
    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title(f"PRC: V20 vs V22 vs V23 — Modern SM (N={n}, {n_pos} approved)", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])

    fig.savefig(OUT_PRC, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {OUT_PRC}")

    print("\nDone!")


if __name__ == "__main__":
    main()
