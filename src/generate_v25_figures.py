"""Generate V20 vs V22 vs V23 vs V24 vs V25 figures for all sets.
Includes both Score-based and raw TCSP curves.
"""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")


def plot_roc_dual(score_datasets, tcsp_dataset, y_true, title, out_path):
    """2-panel ROC: Score-based (left) + Raw TCSP overlay (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor("white")

    # Panel 1: Score-based ROC (all versions)
    for scores, _, label, color, lw, ls in score_datasets:
        valid = ~scores.isna()
        pred = 101 - scores[valid]
        fpr, tpr, _ = roc_curve(y_true[valid], pred)
        roc_auc = auc(fpr, tpr)
        ax1.plot(fpr, tpr, color=color, lw=lw, ls=ls,
                 label=f"{label}  AUC: {roc_auc:.3f}")
    ax1.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax1.set_xlabel("False Positive Rate", fontsize=12)
    ax1.set_ylabel("True Positive Rate", fontsize=12)
    ax1.set_title("ROC — Edward Score", fontsize=13, fontweight="bold")
    ax1.legend(loc="lower right", fontsize=9, framealpha=0.9)
    ax1.grid(True, alpha=0.2)
    ax1.set_xlim([0, 1]); ax1.set_ylim([0, 1.02])

    # Panel 2: V24 Score vs V25 Score vs V25 Raw TCSP
    if tcsp_dataset is not None:
        tcsp_scores, _, tcsp_label, tcsp_color = tcsp_dataset
        # V24 score for reference
        s24 = score_datasets[-2]  # V24 is second to last
        valid24 = ~s24[0].isna()
        pred24 = 101 - s24[0][valid24]
        fpr24, tpr24, _ = roc_curve(y_true[valid24], pred24)
        auc24 = auc(fpr24, tpr24)
        ax2.plot(fpr24, tpr24, color=s24[3], lw=1.5, ls="--",
                 label=f"V24 Score  AUC: {auc24:.3f}")
        # V25 score
        s25 = score_datasets[-1]  # V25 is last
        valid25 = ~s25[0].isna()
        pred25 = 101 - s25[0][valid25]
        fpr25, tpr25, _ = roc_curve(y_true[valid25], pred25)
        auc25 = auc(fpr25, tpr25)
        ax2.plot(fpr25, tpr25, color=s25[3], lw=2.0, ls="-",
                 label=f"V25 Score  AUC: {auc25:.3f}")
        # Raw TCSP
        valid_tcsp = ~tcsp_scores.isna()
        fpr_t, tpr_t, _ = roc_curve(y_true[valid_tcsp], tcsp_scores[valid_tcsp])
        auc_t = auc(fpr_t, tpr_t)
        ax2.plot(fpr_t, tpr_t, color=tcsp_color, lw=2.5, ls="-.",
                 label=f"{tcsp_label}  AUC: {auc_t:.3f}")
    ax2.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax2.set_xlabel("False Positive Rate", fontsize=12)
    ax2.set_ylabel("True Positive Rate", fontsize=12)
    ax2.set_title("ROC — V24 vs V25 Score vs Raw TCSP", fontsize=13, fontweight="bold")
    ax2.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.2)
    ax2.set_xlim([0, 1]); ax2.set_ylim([0, 1.02])

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_prc_dual(score_datasets, tcsp_dataset, y_true, title, out_path):
    """2-panel PRC: Score-based (left) + Raw TCSP overlay (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor("white")
    n = len(y_true)
    baseline = y_true.sum() / n

    # Panel 1: Score-based PRC (all versions)
    for scores, _, label, color, lw, ls in score_datasets:
        valid = ~scores.isna()
        pred = 1 - scores[valid] / 100
        prec, rec, _ = precision_recall_curve(y_true[valid], pred)
        ap = average_precision_score(y_true[valid], pred)
        ax1.plot(rec, prec, color=color, lw=lw, ls=ls,
                 label=f"{label}  AP: {ap:.3f}")
    ax1.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
                label=f"Random ({baseline:.2f})")
    ax1.set_xlabel("Recall", fontsize=12)
    ax1.set_ylabel("Precision", fontsize=12)
    ax1.set_title("PRC — Edward Score", fontsize=13, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax1.grid(True, alpha=0.2)
    ax1.set_xlim([0, 1]); ax1.set_ylim([0, 1.05])

    # Panel 2: V24 Score vs V25 Score vs V25 Raw TCSP
    if tcsp_dataset is not None:
        tcsp_scores, _, tcsp_label, tcsp_color = tcsp_dataset
        s24 = score_datasets[-2]
        valid24 = ~s24[0].isna()
        pred24 = 1 - s24[0][valid24] / 100
        prec24, rec24, _ = precision_recall_curve(y_true[valid24], pred24)
        ap24 = average_precision_score(y_true[valid24], pred24)
        ax2.plot(rec24, prec24, color=s24[3], lw=1.5, ls="--",
                 label=f"V24 Score  AP: {ap24:.3f}")

        s25 = score_datasets[-1]
        valid25 = ~s25[0].isna()
        pred25 = 1 - s25[0][valid25] / 100
        prec25, rec25, _ = precision_recall_curve(y_true[valid25], pred25)
        ap25 = average_precision_score(y_true[valid25], pred25)
        ax2.plot(rec25, prec25, color=s25[3], lw=2.0, ls="-",
                 label=f"V25 Score  AP: {ap25:.3f}")

        valid_tcsp = ~tcsp_scores.isna()
        prec_t, rec_t, _ = precision_recall_curve(y_true[valid_tcsp], tcsp_scores[valid_tcsp])
        ap_t = average_precision_score(y_true[valid_tcsp], tcsp_scores[valid_tcsp])
        ax2.plot(rec_t, prec_t, color=tcsp_color, lw=2.5, ls="-.",
                 label=f"{tcsp_label}  AP: {ap_t:.3f}")
    ax2.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
                label=f"Random ({baseline:.2f})")
    ax2.set_xlabel("Recall", fontsize=12)
    ax2.set_ylabel("Precision", fontsize=12)
    ax2.set_title("PRC — V24 vs V25 Score vs Raw TCSP", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.2)
    ax2.set_xlim([0, 1]); ax2.set_ylim([0, 1.05])

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_calibration(score_list, y_true, outcome, title, out_path):
    n_panels = len(score_list)
    fig, axes = plt.subplots(1, n_panels, figsize=(6 * n_panels, 7), sharey=True)
    if n_panels == 1:
        axes = [axes]

    for ax, (scores, panel_title, bins, bin_labels, xlabel) in zip(axes, score_list):
        df_temp = pd.DataFrame({"score": scores, "outcome": outcome})
        df_temp["bin"] = pd.cut(df_temp["score"], bins=bins, labels=bin_labels, include_lowest=True)
        pivot = pd.crosstab(df_temp["bin"], df_temp["outcome"], normalize="index")
        for c in ["Approved", "Liability"]:
            if c not in pivot.columns:
                pivot[c] = 0
        pivot = pivot[["Approved", "Liability"]]
        pivot.plot(kind="bar", stacked=True, ax=ax,
                   color=["#B7E4C7", "#FF7F50"], edgecolor="black", width=0.8)
        ax.set_title(panel_title, fontsize=12, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel("Proportion", fontsize=10)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="upper left", fontsize=8)

    n = len(y_true)
    plt.suptitle(f"{title} (N={n})", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def process_set(set_name, dir_path, v20_file, v22_file, v23_file, v24_file, v25_file,
                cat_col="category", cat_val="approved", tag_col="MedChem_Descriptor_Tag"):
    print(f"\n{'='*60}")
    print(f"  {set_name}")
    print(f"{'='*60}")

    v20 = pd.read_csv(v20_file)
    v22 = pd.read_csv(v22_file)
    v23 = pd.read_csv(v23_file)
    v24 = pd.read_csv(v24_file)
    v25 = pd.read_csv(v25_file)

    s20 = pd.to_numeric(v20["Edward Score V20"], errors="coerce")
    s22 = pd.to_numeric(v22["Edward Score V22"], errors="coerce")
    s23 = pd.to_numeric(v23["Edward Score V23"], errors="coerce")
    s24 = pd.to_numeric(v24["Edward Score V24"], errors="coerce")
    s25 = pd.to_numeric(v25["Edward Score V25"], errors="coerce")
    tcsp25 = pd.to_numeric(v25["TCSP V25"], errors="coerce")
    y_true = (v22[cat_col] == cat_val).astype(int)

    n = len(y_true)
    n_pos = y_true.sum()
    print(f"N={n}, Approved={n_pos}, Failed={n - n_pos}")

    score_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    score_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                    "50-60", "60-70", "70-80", "80-90", "90-100"]
    tcsp_bins = [0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 40]
    tcsp_labels = ["0-2", "2-4", "4-6", "6-8", "8-10",
                   "10-15", "15-20", "20-25", "25-30", "30-40"]

    versions = [
        (s20, y_true, "V20 (Edward Only)", "#B0B0B0", 1.0, "--"),
        (s22, y_true, "V22 (Edward + Salah)", "#4A90E2", 1.0, "--"),
        (s23, y_true, "V23 (Calibrated)", "#2ECC71", 1.5, "--"),
        (s24, y_true, "V24 (Context-Aware)", "#E74C3C", 2.0, "-"),
        (s25, y_true, "V25 (Multi-Agent)", "#9B59B6", 2.5, "-"),
    ]

    tcsp_ds = (tcsp25, y_true, "V25 Raw TCSP", "#FF8C00")

    # ROC (2-panel)
    plot_roc_dual(versions, tcsp_ds, y_true,
                  f"ROC: V20→V25 — {set_name} (N={n}, {n_pos} approved)",
                  os.path.join(dir_path, "sm_v20_v22_v23_v24_v25_roc.png"))

    # PRC (2-panel)
    plot_prc_dual(versions, tcsp_ds, y_true,
                  f"PRC: V20→V25 — {set_name} (N={n}, {n_pos} approved)",
                  os.path.join(dir_path, "sm_v20_v22_v23_v24_v25_prc.png"))

    # Calibration (6-panel: V20-V25 score + V25 raw TCSP)
    outcome = v22[tag_col].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )
    plot_calibration(
        [
            (s20, "V20", score_bins, score_labels, "Score Bin"),
            (s22, "V22", score_bins, score_labels, "Score Bin"),
            (s23, "V23", score_bins, score_labels, "Score Bin"),
            (s24, "V24", score_bins, score_labels, "Score Bin"),
            (s25, "V25", score_bins, score_labels, "Score Bin"),
            (tcsp25 * 100, "V25 Raw TCSP", tcsp_bins, tcsp_labels, "TCSP (%) Bin"),
        ],
        y_true, outcome,
        f"Calibration: V20→V25 — {set_name}",
        os.path.join(dir_path, "sm_v20_v22_v23_v24_v25_calibration.png"))


def main():
    process_set("Modern",
                os.path.join(BASE, "Salah", "modern"),
                os.path.join(BASE, "Salah", "modern", "SM_V20_EDWARD_ONLY.csv"),
                os.path.join(BASE, "Salah", "modern", "SM_V22_EDWARD_SALAH.csv"),
                os.path.join(BASE, "Salah", "modern", "SM_V23_EDWARD_SALAH.csv"),
                os.path.join(BASE, "Salah", "modern", "SM_V24_EDWARD_SALAH.csv"),
                os.path.join(BASE, "Salah", "modern", "SM_V25_EDWARD_SALAH.csv"))

    process_set("Legacy",
                os.path.join(BASE, "Salah", "legacy"),
                os.path.join(BASE, "Salah", "legacy", "SM_V20_EDWARD_ONLY_LEGACY.csv"),
                os.path.join(BASE, "Salah", "legacy", "SM_V22_EDWARD_SALAH_LEGACY.csv"),
                os.path.join(BASE, "Salah", "legacy", "SM_V23_EDWARD_SALAH_LEGACY.csv"),
                os.path.join(BASE, "Salah", "legacy", "SM_V24_EDWARD_SALAH_LEGACY.csv"),
                os.path.join(BASE, "Salah", "legacy", "SM_V25_EDWARD_SALAH_LEGACY.csv"))

    process_set("Global",
                os.path.join(BASE, "Salah", "global"),
                os.path.join(BASE, "Salah", "global", "SM_V20_EDWARD_ONLY_GLOBAL.csv"),
                os.path.join(BASE, "Salah", "global", "SM_V22_EDWARD_SALAH_GLOBAL.csv"),
                os.path.join(BASE, "Salah", "global", "SM_V23_EDWARD_SALAH_GLOBAL.csv"),
                os.path.join(BASE, "Salah", "global", "SM_V24_EDWARD_SALAH_GLOBAL.csv"),
                os.path.join(BASE, "Salah", "global", "SM_V25_EDWARD_SALAH_GLOBAL.csv"))

    print("\nDone!")


if __name__ == "__main__":
    main()
