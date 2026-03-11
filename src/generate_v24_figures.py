"""Generate V20 vs V22 vs V23 vs V24 figures for all sets."""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")


def plot_roc(datasets, title, out_path):
    """Plot ROC curves for multiple versions."""
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")

    for scores, y_true, label, color, lw, ls in datasets:
        valid = ~scores.isna()
        pred = 101 - scores[valid]
        fpr, tpr, _ = roc_curve(y_true[valid], pred)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, lw=lw, ls=ls,
                label=f"{label}  AUC: {roc_auc:.3f}")

    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])

    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_prc(datasets, y_true, title, out_path):
    """Plot PRC curves for multiple versions."""
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    n = len(y_true)
    baseline = y_true.sum() / n

    for scores, _, label, color, lw, ls in datasets:
        valid = ~scores.isna()
        pred = 1 - scores[valid] / 100
        prec, rec, _ = precision_recall_curve(y_true[valid], pred)
        ap = average_precision_score(y_true[valid], pred)
        ax.plot(rec, prec, color=color, lw=lw, ls=ls,
                label=f"{label}  AP: {ap:.3f}")

    ax.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
               label=f"Random (baseline: {baseline:.2f})")
    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])

    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_calibration(score_list, y_true, outcome, title, out_path):
    """Plot multi-panel calibration bar chart."""
    n_panels = len(score_list)
    fig, axes = plt.subplots(1, n_panels, figsize=(7 * n_panels, 7), sharey=True)
    if n_panels == 1:
        axes = [axes]

    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    bin_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                  "50-60", "60-70", "70-80", "80-90", "90-100"]

    for ax, (scores, panel_title) in zip(axes, score_list):
        df_temp = pd.DataFrame({"score": scores, "outcome": outcome})
        df_temp["bin"] = pd.cut(df_temp["score"], bins=bins, labels=bin_labels, include_lowest=True)
        pivot = pd.crosstab(df_temp["bin"], df_temp["outcome"], normalize="index")
        for c in ["Approved", "Liability"]:
            if c not in pivot.columns:
                pivot[c] = 0
        pivot = pivot[["Approved", "Liability"]]
        pivot.plot(kind="bar", stacked=True, ax=ax,
                   color=["#B7E4C7", "#FF7F50"], edgecolor="black", width=0.8)
        ax.set_title(panel_title, fontsize=13, fontweight="bold")
        ax.set_xlabel("Edward Score Bin", fontsize=11)
        ax.set_ylabel("Proportion", fontsize=11)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="upper left", fontsize=9)

    n = len(y_true)
    plt.suptitle(f"{title} (N={n})", fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def process_set(set_name, dir_path, v20_file, v22_file, v23_file, v24_file, cat_col="category", cat_val="approved", tag_col="MedChem_Descriptor_Tag"):
    """Process one dataset (modern/legacy/global)."""
    print(f"\n{'='*60}")
    print(f"  {set_name}")
    print(f"{'='*60}")

    v20 = pd.read_csv(v20_file)
    v22 = pd.read_csv(v22_file)
    v23 = pd.read_csv(v23_file)
    v24 = pd.read_csv(v24_file)

    s20 = pd.to_numeric(v20["Edward Score V20"], errors="coerce")
    s22 = pd.to_numeric(v22["Edward Score V22"], errors="coerce")
    s23 = pd.to_numeric(v23["Edward Score V23"], errors="coerce")
    s24 = pd.to_numeric(v24["Edward Score V24"], errors="coerce")
    y_true = (v22[cat_col] == cat_val).astype(int)

    n = len(y_true)
    n_pos = y_true.sum()
    print(f"N={n}, Approved={n_pos}, Failed={n - n_pos}")

    # Colors: V20=grey, V22=blue, V23=green, V24=red
    versions = [
        (s20, y_true, "V20 (Edward Only)", "#B0B0B0", 1.5, "--"),
        (s22, y_true, "V22 (Edward + Salah)", "#4A90E2", 1.5, "--"),
        (s23, y_true, "V23 (Calibrated Alerts)", "#2ECC71", 2.0, "-"),
        (s24, y_true, "V24 (Context-Aware)", "#E74C3C", 2.5, "-"),
    ]

    # ROC
    plot_roc(versions,
             f"ROC: V20 vs V22 vs V23 vs V24 — {set_name} (N={n}, {n_pos} approved)",
             os.path.join(dir_path, "sm_v20_v22_v23_v24_roc.png"))

    # PRC
    plot_prc(versions, y_true,
             f"PRC: V20 vs V22 vs V23 vs V24 — {set_name} (N={n}, {n_pos} approved)",
             os.path.join(dir_path, "sm_v20_v22_v23_v24_prc.png"))

    # Calibration (4-panel)
    outcome = v22[tag_col].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )
    plot_calibration(
        [(s20, "V20 — Edward Only"), (s22, "V22 — Edward+Salah"),
         (s23, "V23 — Calibrated"), (s24, "V24 — Context-Aware")],
        y_true, outcome,
        f"Calibration: V20→V24 — {set_name}",
        os.path.join(dir_path, "sm_v20_v22_v23_v24_calibration.png"))


def main():
    # Modern
    process_set("Modern",
                os.path.join(BASE, "Salah", "modern"),
                os.path.join(BASE, "Salah", "modern", "SM_V20_EDWARD_ONLY.csv"),
                os.path.join(BASE, "Salah", "modern", "SM_V22_EDWARD_SALAH.csv"),
                os.path.join(BASE, "Salah", "modern", "SM_V23_EDWARD_SALAH.csv"),
                os.path.join(BASE, "Salah", "modern", "SM_V24_EDWARD_SALAH.csv"))

    # Legacy
    process_set("Legacy",
                os.path.join(BASE, "Salah", "legacy"),
                os.path.join(BASE, "Salah", "legacy", "SM_V20_EDWARD_ONLY_LEGACY.csv"),
                os.path.join(BASE, "Salah", "legacy", "SM_V22_EDWARD_SALAH_LEGACY.csv"),
                os.path.join(BASE, "Salah", "legacy", "SM_V23_EDWARD_SALAH_LEGACY.csv"),
                os.path.join(BASE, "Salah", "legacy", "SM_V24_EDWARD_SALAH_LEGACY.csv"))

    # Global
    process_set("Global",
                os.path.join(BASE, "Salah", "global"),
                os.path.join(BASE, "Salah", "global", "SM_V20_EDWARD_ONLY_GLOBAL.csv"),
                os.path.join(BASE, "Salah", "global", "SM_V22_EDWARD_SALAH_GLOBAL.csv"),
                os.path.join(BASE, "Salah", "global", "SM_V23_EDWARD_SALAH_GLOBAL.csv"),
                os.path.join(BASE, "Salah", "global", "SM_V24_EDWARD_SALAH_GLOBAL.csv"))

    print("\nDone!")


if __name__ == "__main__":
    main()
