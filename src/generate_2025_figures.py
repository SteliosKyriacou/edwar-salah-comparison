"""Generate calibration bar chart, ROC, and PRC for 2025 drug data (V23)."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
V23_FILE = os.path.join(BASE, "Salah", "2025", "2025_V23_EDWARD_SALAH.csv")
OUT_DIR = os.path.join(BASE, "Salah", "2025")


def main():
    df = pd.read_csv(V23_FILE)
    scores = pd.to_numeric(df["Edward Score V23"], errors="coerce")
    # Label: approved=1, failed=0
    y_true = (df["category"] == "Approved").astype(int)
    n = len(df)
    n_pos = y_true.sum()

    print(f"2025 dataset: N={n}, Approved={n_pos}, Failed={n - n_pos}")

    # ── Calibration Bar Chart ──────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("white")
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    bin_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                  "50-60", "60-70", "70-80", "80-90", "90-100"]

    outcome = df["MedChem_D"].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )
    df_temp = pd.DataFrame({"score": scores, "outcome": outcome})
    df_temp["bin"] = pd.cut(df_temp["score"], bins=bins, labels=bin_labels, include_lowest=True)
    ct = pd.crosstab(df_temp["bin"], df_temp["outcome"])
    for c in ["Approved", "Liability"]:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[["Approved", "Liability"]]

    # Print counts
    ct_display = ct.copy()
    ct_display["Total"] = ct_display["Approved"] + ct_display["Liability"]
    ct_display["Approved %"] = (ct_display["Approved"] / ct_display["Total"] * 100).round(1)
    print("\nBin counts:")
    print(ct_display.to_string())

    # Stacked proportion bar
    ct_norm = ct.div(ct.sum(axis=1), axis=0).fillna(0)
    ct_norm.plot(kind="bar", stacked=True, ax=ax,
                 color=["#B7E4C7", "#FF7F50"], edgecolor="black", width=0.8)

    # Add count labels on bars
    for i, (idx, row) in enumerate(ct.iterrows()):
        total = row["Approved"] + row["Liability"]
        if total > 0:
            ax.text(i, 1.02, f"n={int(total)}", ha="center", va="bottom",
                    fontsize=9, fontweight="bold")

    ax.set_title(f"V23 Calibration — 2025 Drug Data (N={n})", fontsize=14, fontweight="bold")
    ax.set_xlabel("Edward Score V23 Bin", fontsize=12)
    ax.set_ylabel("Proportion", fontsize=12)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left", fontsize=10)
    ax.set_ylim(0, 1.15)

    out = os.path.join(OUT_DIR, "2025_v23_calibration.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\nSaved: {out}")

    # ── ROC Curve ──────────────────────────────────────────────────────────
    pred = 101 - scores
    valid = ~scores.isna()
    y_v = y_true[valid]
    p_v = pred[valid]

    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")

    fpr, tpr, _ = roc_curve(y_v, p_v)
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, color="#2ECC71", lw=2.5,
            label=f"V23 (Edward + Salah)  AUC: {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC: V23 — 2025 Drug Data (N={n}, {n_pos} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.02])

    out = os.path.join(OUT_DIR, "2025_v23_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── PRC Curve ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    baseline = n_pos / n

    pred_prc = 1 - scores[valid] / 100
    prec, rec, _ = precision_recall_curve(y_v, pred_prc)
    ap = average_precision_score(y_v, pred_prc)

    ax.plot(rec, prec, color="#2ECC71", lw=2.5,
            label=f"V23 (Edward + Salah)  AP: {ap:.3f}")
    ax.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
               label=f"Random (baseline: {baseline:.2f})")
    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title(f"PRC: V23 — 2025 Drug Data (N={n}, {n_pos} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])

    out = os.path.join(OUT_DIR, "2025_v23_prc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    print("\nDone!")


if __name__ == "__main__":
    main()
