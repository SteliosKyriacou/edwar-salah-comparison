"""Generate V25 figures for the Global dataset (N=394).
Score-based and raw TCSP: ROC, PRC, Calibration.
"""

import pandas as pd
import re
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
GLOBAL_FILE = os.path.join(BASE, "Validation", "global", "SM_V25_GLOBAL.csv")
OUT_DIR = os.path.join(BASE, "Validation", "global")


def extract_year(val):
    if pd.isna(val):
        return None
    m = re.search(r'(\d{4})', str(val))
    return int(m.group(1)) if m else None


def plot_roc(s25, tcsp25, y_true, n, n_pos, title, out_path):
    """2-panel ROC: Score (left) + Raw TCSP (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor("white")

    valid = ~s25.isna()
    pred = 101 - s25[valid]
    fpr, tpr, _ = roc_curve(y_true[valid], pred)
    roc_auc = auc(fpr, tpr)
    ax1.plot(fpr, tpr, color="#9B59B6", lw=2.5,
             label=f"V25 MedChem Score  AUC: {roc_auc:.3f}")
    ax1.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax1.set_xlabel("False Positive Rate", fontsize=12)
    ax1.set_ylabel("True Positive Rate", fontsize=12)
    ax1.set_title("ROC — MedChem Score", fontsize=13, fontweight="bold")
    ax1.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax1.grid(True, alpha=0.2)
    ax1.set_xlim([0, 1]); ax1.set_ylim([0, 1.02])

    valid_t = ~tcsp25.isna()
    fpr_t, tpr_t, _ = roc_curve(y_true[valid_t], tcsp25[valid_t])
    auc_t = auc(fpr_t, tpr_t)
    ax2.plot(fpr_t, tpr_t, color="#FF8C00", lw=2.5,
             label=f"V25 Raw TCSP  AUC: {auc_t:.3f}")
    ax2.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax2.set_xlabel("False Positive Rate", fontsize=12)
    ax2.set_ylabel("True Positive Rate", fontsize=12)
    ax2.set_title("ROC — Raw TCSP", fontsize=13, fontweight="bold")
    ax2.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.2)
    ax2.set_xlim([0, 1]); ax2.set_ylim([0, 1.02])

    plt.suptitle(f"{title} (N={n}, {n_pos} approved)", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_prc(s25, tcsp25, y_true, n, n_pos, title, out_path):
    """2-panel PRC: Score (left) + Raw TCSP (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor("white")
    baseline = n_pos / n

    valid = ~s25.isna()
    pred = 1 - s25[valid] / 100
    prec, rec, _ = precision_recall_curve(y_true[valid], pred)
    ap = average_precision_score(y_true[valid], pred)
    ax1.plot(rec, prec, color="#9B59B6", lw=2.5,
             label=f"V25 MedChem Score  AP: {ap:.3f}")
    ax1.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
                label=f"Random ({baseline:.2f})")
    ax1.set_xlabel("Recall", fontsize=12)
    ax1.set_ylabel("Precision", fontsize=12)
    ax1.set_title("PRC — MedChem Score", fontsize=13, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax1.grid(True, alpha=0.2)
    ax1.set_xlim([0, 1]); ax1.set_ylim([0, 1.05])

    valid_t = ~tcsp25.isna()
    prec_t, rec_t, _ = precision_recall_curve(y_true[valid_t], tcsp25[valid_t])
    ap_t = average_precision_score(y_true[valid_t], tcsp25[valid_t])
    ax2.plot(rec_t, prec_t, color="#FF8C00", lw=2.5,
             label=f"V25 Raw TCSP  AP: {ap_t:.3f}")
    ax2.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
                label=f"Random ({baseline:.2f})")
    ax2.set_xlabel("Recall", fontsize=12)
    ax2.set_ylabel("Precision", fontsize=12)
    ax2.set_title("PRC — Raw TCSP", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.2)
    ax2.set_xlim([0, 1]); ax2.set_ylim([0, 1.05])

    plt.suptitle(f"{title} (N={n}, {n_pos} approved)", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_calibration(s25, tcsp25, y_true, outcome, n, title, out_path):
    """2-panel calibration: Score bins (left) + TCSP bins (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7), sharey=True)

    score_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    score_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                    "50-60", "60-70", "70-80", "80-90", "90-100"]
    tcsp_bins = [0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 40]
    tcsp_labels = ["0-2", "2-4", "4-6", "6-8", "8-10",
                   "10-15", "15-20", "20-25", "25-30", "30-40"]

    def cal_panel(ax, values, bins, labels, panel_title, xlabel):
        df_temp = pd.DataFrame({"val": values, "outcome": outcome})
        df_temp["bin"] = pd.cut(df_temp["val"], bins=bins, labels=labels, include_lowest=True)
        ct = pd.crosstab(df_temp["bin"], df_temp["outcome"])
        for c in ["Approved", "Liability"]:
            if c not in ct.columns:
                ct[c] = 0
        ct = ct[["Approved", "Liability"]]
        ct_norm = ct.div(ct.sum(axis=1), axis=0).fillna(0)
        ct_norm.plot(kind="bar", stacked=True, ax=ax,
                     color=["#B7E4C7", "#FF7F50"], edgecolor="black", width=0.8)
        for i, (idx, row) in enumerate(ct.iterrows()):
            total = row["Approved"] + row["Liability"]
            if total > 0:
                ax.text(i, 1.02, f"n={int(total)}", ha="center", va="bottom",
                        fontsize=8, fontweight="bold")
        ax.set_title(panel_title, fontsize=13, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel("Proportion", fontsize=11)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="upper left", fontsize=9)
        ax.set_ylim(0, 1.15)

    cal_panel(ax1, s25, score_bins, score_labels,
              "V25 — MedChem Score", "MedChem Score Bin")
    cal_panel(ax2, tcsp25 * 100, tcsp_bins, tcsp_labels,
              "V25 — Raw TCSP (%)", "TCSP (%) Bin")

    plt.suptitle(f"{title} (N={n})", fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")


def process_set(set_name, df, out_dir, cat_col="category", cat_val="approved",
                tag_col="MedChem_Descriptor_Tag"):
    print(f"\n{'='*60}")
    print(f"  {set_name}")
    print(f"{'='*60}")

    os.makedirs(out_dir, exist_ok=True)

    s25 = pd.to_numeric(df["MedChem Score V25"], errors="coerce")
    tcsp25 = pd.to_numeric(df["TCSP V25"], errors="coerce")
    y_true = (df[cat_col] == cat_val).astype(int)

    n = len(y_true)
    n_pos = y_true.sum()
    print(f"N={n}, Approved={n_pos}, Failed={n - n_pos}")

    app_mask = y_true == 1
    fail_mask = y_true == 0
    print(f"Score: Approved median={s25[app_mask].median():.0f}, Failed median={s25[fail_mask].median():.0f}")
    print(f"TCSP:  Approved median={tcsp25[app_mask].median():.3f}, Failed median={tcsp25[fail_mask].median():.3f}")

    plot_roc(s25, tcsp25, y_true, n, n_pos,
             f"ROC: V25 — {set_name}",
             os.path.join(out_dir, "v25_roc.png"))

    plot_prc(s25, tcsp25, y_true, n, n_pos,
             f"PRC: V25 — {set_name}",
             os.path.join(out_dir, "v25_prc.png"))

    outcome = df[tag_col].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )
    plot_calibration(s25, tcsp25, y_true, outcome, n,
                     f"Calibration: V25 — {set_name}",
                     os.path.join(out_dir, "v25_calibration.png"))


def main():
    df = pd.read_csv(GLOBAL_FILE)

    # Add year column for splitting
    df['year_clean'] = df['year-approved'].apply(extract_year).fillna(
        df['year_stopped'].apply(extract_year)
    )

    # Global (all)
    process_set("Global", df,
                os.path.join(OUT_DIR))

    # Modern (>=1999)
    modern = df[df['year_clean'] >= 1999].reset_index(drop=True)
    process_set("Modern", modern,
                os.path.join(BASE, "Validation", "modern"))

    # Legacy (<1999)
    legacy = df[df['year_clean'] < 1999].reset_index(drop=True)
    process_set("Legacy", legacy,
                os.path.join(BASE, "Validation", "legacy"))

    print("\nDone!")


if __name__ == "__main__":
    main()
