"""Generate V24 vs V25 comparison figures for 2025 drug data.
Includes both Score-based and raw TCSP curves side by side.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
V24_FILE = os.path.join(BASE, "Salah", "2025", "2025_V24_EDWARD_SALAH.csv")
V25_FILE = os.path.join(BASE, "Salah", "2025", "2025_V25_EDWARD_SALAH.csv")
OUT_DIR = os.path.join(BASE, "Salah", "2025")


def main():
    v24 = pd.read_csv(V24_FILE)
    v25 = pd.read_csv(V25_FILE)

    s24 = pd.to_numeric(v24["Edward Score V24"], errors="coerce")
    s25 = pd.to_numeric(v25["Edward Score V25"], errors="coerce")
    tcsp25 = pd.to_numeric(v25["TCSP V25"], errors="coerce")
    y_true = (v25["category"] == "Approved").astype(int)

    n = len(y_true)
    n_pos = y_true.sum()
    print(f"2025 dataset: N={n}, Approved={n_pos}, Failed={n - n_pos}")

    app_mask = y_true == 1
    fail_mask = y_true == 0
    print(f"V24 Score: Approved median={s24[app_mask].median():.0f}, Failed median={s24[fail_mask].median():.0f}, Gap={s24[fail_mask].median() - s24[app_mask].median():.0f}")
    print(f"V25 Score: Approved median={s25[app_mask].median():.0f}, Failed median={s25[fail_mask].median():.0f}, Gap={s25[fail_mask].median() - s25[app_mask].median():.0f}")
    print(f"V25 TCSP:  Approved median={tcsp25[app_mask].median():.3f}, Failed median={tcsp25[fail_mask].median():.3f}")

    # ── ROC (2-panel: Score + TCSP) ──────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor("white")

    # Panel 1: Score-based ROC
    for scores, label, color, lw, ls in [
        (s24, "V24 (Context-Aware)", "#B0B0B0", 1.5, "--"),
        (s25, "V25 (Multi-Agent)", "#9B59B6", 2.5, "-"),
    ]:
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
    ax1.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax1.grid(True, alpha=0.2)
    ax1.set_xlim([0, 1]); ax1.set_ylim([0, 1.02])

    # Panel 2: Raw TCSP ROC
    for scores, label, color, lw, ls, use_tcsp in [
        (s24, "V24 Score (inverted)", "#B0B0B0", 1.5, "--", False),
        (tcsp25, "V25 Raw TCSP", "#9B59B6", 2.5, "-", True),
    ]:
        valid = ~scores.isna()
        if use_tcsp:
            pred = scores[valid]  # higher TCSP = more likely approved
        else:
            pred = 101 - scores[valid]
        fpr, tpr, _ = roc_curve(y_true[valid], pred)
        roc_auc = auc(fpr, tpr)
        ax2.plot(fpr, tpr, color=color, lw=lw, ls=ls,
                 label=f"{label}  AUC: {roc_auc:.3f}")
    ax2.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax2.set_xlabel("False Positive Rate", fontsize=12)
    ax2.set_ylabel("True Positive Rate", fontsize=12)
    ax2.set_title("ROC — Raw TCSP", fontsize=13, fontweight="bold")
    ax2.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.2)
    ax2.set_xlim([0, 1]); ax2.set_ylim([0, 1.02])

    plt.suptitle(f"V24 vs V25 — 2025 Drug Data (N={n}, {n_pos} approved)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out = os.path.join(OUT_DIR, "2025_v24_vs_v25_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── PRC (2-panel: Score + TCSP) ──────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor("white")
    baseline = n_pos / n

    # Panel 1: Score-based PRC
    for scores, label, color, lw, ls in [
        (s24, "V24 (Context-Aware)", "#B0B0B0", 1.5, "--"),
        (s25, "V25 (Multi-Agent)", "#9B59B6", 2.5, "-"),
    ]:
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
    ax1.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax1.grid(True, alpha=0.2)
    ax1.set_xlim([0, 1]); ax1.set_ylim([0, 1.05])

    # Panel 2: Raw TCSP PRC
    for scores, label, color, lw, ls, use_tcsp in [
        (s24, "V24 Score (inverted)", "#B0B0B0", 1.5, "--", False),
        (tcsp25, "V25 Raw TCSP", "#9B59B6", 2.5, "-", True),
    ]:
        valid = ~scores.isna()
        if use_tcsp:
            pred = scores[valid]
        else:
            pred = 1 - scores[valid] / 100
        prec, rec, _ = precision_recall_curve(y_true[valid], pred)
        ap = average_precision_score(y_true[valid], pred)
        ax2.plot(rec, prec, color=color, lw=lw, ls=ls,
                 label=f"{label}  AP: {ap:.3f}")
    ax2.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1,
                label=f"Random ({baseline:.2f})")
    ax2.set_xlabel("Recall", fontsize=12)
    ax2.set_ylabel("Precision", fontsize=12)
    ax2.set_title("PRC — Raw TCSP", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax2.grid(True, alpha=0.2)
    ax2.set_xlim([0, 1]); ax2.set_ylim([0, 1.05])

    plt.suptitle(f"V24 vs V25 — 2025 Drug Data (N={n}, {n_pos} approved)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out = os.path.join(OUT_DIR, "2025_v24_vs_v25_prc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Calibration (3-panel: V24 Score, V25 Score, V25 Raw TCSP) ───────
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 7), sharey=True)
    score_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    score_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                    "50-60", "60-70", "70-80", "80-90", "90-100"]
    tcsp_bins = [0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 40]
    tcsp_labels = ["0-2", "2-4", "4-6", "6-8", "8-10",
                   "10-15", "15-20", "20-25", "25-30", "30-40"]

    outcome = v25["MedChem_D"].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )

    # Helper to plot a calibration panel
    def cal_panel(ax, values, bins, labels, title, xlabel):
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
                        fontsize=9, fontweight="bold")
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel("Proportion", fontsize=11)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="upper left", fontsize=9)
        ax.set_ylim(0, 1.15)

    cal_panel(ax1, s24, score_bins, score_labels,
              "V24 — Edward Score", "Edward Score V24 Bin")
    cal_panel(ax2, s25, score_bins, score_labels,
              "V25 — Edward Score", "Edward Score V25 Bin")
    cal_panel(ax3, tcsp25 * 100, tcsp_bins, tcsp_labels,
              "V25 — Raw TCSP (%)", "TCSP (%) Bin")

    plt.suptitle(f"Calibration: V24 vs V25 — 2025 Drug Data (N={n})",
                 fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out = os.path.join(OUT_DIR, "2025_v24_vs_v25_calibration.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Score drift scatter (V24 vs V25) ─────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 9))
    fig.patch.set_facecolor("white")
    colors = ["#2ECC71" if y == 1 else "#E74C3C" for y in y_true]
    ax.scatter(s24, s25, c=colors, s=80, edgecolors="black", linewidths=0.5, alpha=0.8)
    ax.plot([0, 100], [0, 100], color="black", lw=1, ls=":", alpha=0.5)
    ax.set_xlabel("Edward Score V24", fontsize=12)
    ax.set_ylabel("Edward Score V25", fontsize=12)
    ax.set_title(f"Score Drift: V24 → V25 — 2025 Drug Data (N={n})",
                 fontsize=13, fontweight="bold")
    ax.set_xlim([0, 100]); ax.set_ylim([0, 100])
    ax.grid(True, alpha=0.2)
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ECC71',
               markersize=10, markeredgecolor='black', label='Approved'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#E74C3C',
               markersize=10, markeredgecolor='black', label='Failed'),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=11)
    out = os.path.join(OUT_DIR, "2025_v24_vs_v25_score_drift.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── V25-only calibration (Score) ─────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("white")
    cal_panel(ax, s25, score_bins, score_labels,
              f"V25 Calibration — Edward Score — 2025 (N={n})",
              "Edward Score V25 Bin")
    out = os.path.join(OUT_DIR, "2025_v25_calibration.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── V25-only calibration (Raw TCSP) ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("white")
    cal_panel(ax, tcsp25 * 100, tcsp_bins, tcsp_labels,
              f"V25 Calibration — Raw TCSP (%) — 2025 (N={n})",
              "TCSP (%) Bin")
    out = os.path.join(OUT_DIR, "2025_v25_raw_tcsp_calibration.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Verdict distribution ─────────────────────────────────────────────
    print("\n--- V25 Verdict Distribution ---")
    for vtype, col in [("Salah", "Salah Verdict V25"), ("Toxi", "Toxi Verdict V25"), ("Pharma", "Pharma Verdict V25")]:
        if col in v25.columns:
            print(f"\n{vtype}:")
            for verdict in v25[col].unique():
                mask = v25[col] == verdict
                count = mask.sum()
                if count > 0:
                    scores = pd.to_numeric(v25.loc[mask, "Edward Score V25"], errors="coerce")
                    app = (v25.loc[mask, "category"] == "Approved").sum()
                    print(f"  {verdict}: {count} (Approved={app}, Failed={count-app}, median score={scores.median():.0f})")

    print("\nDone!")


if __name__ == "__main__":
    main()
