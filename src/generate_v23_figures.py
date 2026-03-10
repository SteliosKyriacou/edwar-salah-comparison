"""Generate V23-specific figures: calibration bar chart + V20 vs V23 ROC."""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

V20_FILE = os.path.join(BASE, "Salah", "modern", "SM_V20_EDWARD_ONLY.csv")
V22_FILE = os.path.join(BASE, "Salah", "modern", "SM_V22_EDWARD_SALAH.csv")
V23_FILE = os.path.join(BASE, "Salah", "modern", "SM_V23_EDWARD_SALAH.csv")

OUT_DIR = os.path.join(BASE, "Salah", "modern")


def load_data():
    v20 = pd.read_csv(V20_FILE)
    v22 = pd.read_csv(V22_FILE)
    v23 = pd.read_csv(V23_FILE)

    v20["Edward Score V20"] = pd.to_numeric(v20["Edward Score V20"], errors="coerce")
    v22["Edward Score V22"] = pd.to_numeric(v22["Edward Score V22"], errors="coerce")
    v23["Edward Score V23"] = pd.to_numeric(v23["Edward Score V23"], errors="coerce")

    # Use category from v22 as ground truth
    label = (v22["category"] == "approved").astype(int)
    outcome = v22["MedChem_Descriptor_Tag"].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )
    return v20, v22, v23, label, outcome


def plot_calibration_v23(v20, v22, v23, outcome):
    """3-panel calibration bar chart: V20 vs V22 vs V23."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(22, 7), sharey=True)
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    bin_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                  "50-60", "60-70", "70-80", "80-90", "90-100"]

    for ax, scores, title, color_tag in [
        (ax1, v20["Edward Score V20"], "V20 — Edward (No Biology)", "#B0B0B0"),
        (ax2, v22["Edward Score V22"], "V22 — Edward + Salah", "#4A90E2"),
        (ax3, v23["Edward Score V23"], "V23 — Calibrated Alerts", "#2ECC71"),
    ]:
        df_temp = pd.DataFrame({"score": scores, "outcome": outcome})
        df_temp["bin"] = pd.cut(df_temp["score"], bins=bins, labels=bin_labels, include_lowest=True)
        pivot = pd.crosstab(df_temp["bin"], df_temp["outcome"], normalize="index")
        for c in ["Approved", "Liability"]:
            if c not in pivot.columns:
                pivot[c] = 0
        pivot = pivot[["Approved", "Liability"]]
        pivot.plot(kind="bar", stacked=True, ax=ax,
                   color=["#B7E4C7", "#FF7F50"], edgecolor="black", width=0.8)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel("Edward Score Bin", fontsize=11)
        ax.set_ylabel("Proportion", fontsize=11)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="upper left", fontsize=9)

    n = len(outcome)
    plt.suptitle(f"Calibration: V20 vs V22 vs V23 — Modern SM (N={n})",
                 fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    out = os.path.join(OUT_DIR, "sm_v20_v22_v23_calibration.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


def plot_roc_v20_vs_v23(v20, v23, label):
    """V20 vs V23 direct ROC comparison."""
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")

    fpr20, tpr20, _ = roc_curve(label, 101 - v20["Edward Score V20"])
    auc20 = auc(fpr20, tpr20)
    ax.plot(fpr20, tpr20, color="#B0B0B0", lw=2, ls="--",
            label=f"V20 (Edward Only)  AUC: {auc20:.3f}")

    fpr23, tpr23, _ = roc_curve(label, 101 - v23["Edward Score V23"])
    auc23 = auc(fpr23, tpr23)
    ax.plot(fpr23, tpr23, color="#2ECC71", lw=2.5,
            label=f"V23 (Calibrated Alerts)  AUC: {auc23:.3f}")

    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    n = len(label)
    n_pos = label.sum()
    ax.set_title(f"ROC: V20 vs V23 — Modern SM (N={n}, {n_pos} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.02])

    out = os.path.join(OUT_DIR, "sm_v20_vs_v23_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


def main():
    v20, v22, v23, label, outcome = load_data()
    plot_calibration_v23(v20, v22, v23, outcome)
    plot_roc_v20_vs_v23(v20, v23, label)
    print("\nDone!")


if __name__ == "__main__":
    main()
