"""Generate V23 vs V24 comparison figures for 2025 drug data."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
V23_FILE = os.path.join(BASE, "Salah", "2025", "2025_V23_EDWARD_SALAH.csv")
V24_FILE = os.path.join(BASE, "Salah", "2025", "2025_V24_EDWARD_SALAH.csv")
OUT_DIR = os.path.join(BASE, "Salah", "2025")


def main():
    v23 = pd.read_csv(V23_FILE)
    v24 = pd.read_csv(V24_FILE)

    s23 = pd.to_numeric(v23["Edward Score V23"], errors="coerce")
    s24 = pd.to_numeric(v24["Edward Score V24"], errors="coerce")
    # 2025 uses "Approved" (capital A)
    y_true = (v24["category"] == "Approved").astype(int)

    n = len(y_true)
    n_pos = y_true.sum()
    print(f"2025 dataset: N={n}, Approved={n_pos}, Failed={n - n_pos}")

    # Medians
    app_mask = y_true == 1
    fail_mask = y_true == 0
    print(f"V23: Approved median={s23[app_mask].median():.0f}, Failed median={s23[fail_mask].median():.0f}, Gap={s23[fail_mask].median() - s23[app_mask].median():.0f}")
    print(f"V24: Approved median={s24[app_mask].median():.0f}, Failed median={s24[fail_mask].median():.0f}, Gap={s24[fail_mask].median() - s24[app_mask].median():.0f}")

    # ── ROC ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")

    for scores, label, color, lw, ls in [
        (s23, "V23 (Calibrated Alerts)", "#B0B0B0", 1.5, "--"),
        (s24, "V24 (Context-Aware)", "#E74C3C", 2.5, "-"),
    ]:
        valid = ~scores.isna()
        pred = 101 - scores[valid]
        fpr, tpr, _ = roc_curve(y_true[valid], pred)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, lw=lw, ls=ls,
                label=f"{label}  AUC: {roc_auc:.3f}")

    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC: V23 vs V24 — 2025 Drug Data (N={n}, {n_pos} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])

    out = os.path.join(OUT_DIR, "2025_v23_vs_v24_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── PRC ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    baseline = n_pos / n

    for scores, label, color, lw, ls in [
        (s23, "V23 (Calibrated Alerts)", "#B0B0B0", 1.5, "--"),
        (s24, "V24 (Context-Aware)", "#E74C3C", 2.5, "-"),
    ]:
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
    ax.set_title(f"PRC: V23 vs V24 — 2025 Drug Data (N={n}, {n_pos} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])

    out = os.path.join(OUT_DIR, "2025_v23_vs_v24_prc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Calibration (2-panel: V23 vs V24) ─────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    bin_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                  "50-60", "60-70", "70-80", "80-90", "90-100"]

    outcome = v24["MedChem_D"].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )

    for ax, scores, title in [
        (ax1, s23, "V23 — Calibrated Alerts"),
        (ax2, s24, "V24 — Context-Aware"),
    ]:
        df_temp = pd.DataFrame({"score": scores, "outcome": outcome})
        df_temp["bin"] = pd.cut(df_temp["score"], bins=bins, labels=bin_labels, include_lowest=True)
        ct = pd.crosstab(df_temp["bin"], df_temp["outcome"])
        for c in ["Approved", "Liability"]:
            if c not in ct.columns:
                ct[c] = 0
        ct = ct[["Approved", "Liability"]]

        # Stacked proportion
        ct_norm = ct.div(ct.sum(axis=1), axis=0).fillna(0)
        ct_norm.plot(kind="bar", stacked=True, ax=ax,
                     color=["#B7E4C7", "#FF7F50"], edgecolor="black", width=0.8)

        # Add count labels
        for i, (idx, row) in enumerate(ct.iterrows()):
            total = row["Approved"] + row["Liability"]
            if total > 0:
                ax.text(i, 1.02, f"n={int(total)}", ha="center", va="bottom",
                        fontsize=9, fontweight="bold")

        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel("Edward Score Bin", fontsize=11)
        ax.set_ylabel("Proportion", fontsize=11)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="upper left", fontsize=9)
        ax.set_ylim(0, 1.15)

    plt.suptitle(f"Calibration: V23 vs V24 — 2025 Drug Data (N={n})",
                 fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    out = os.path.join(OUT_DIR, "2025_v23_vs_v24_calibration.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Score drift scatter (V23 vs V24) ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 9))
    fig.patch.set_facecolor("white")

    colors = ["#2ECC71" if y == 1 else "#E74C3C" for y in y_true]
    ax.scatter(s23, s24, c=colors, s=80, edgecolors="black", linewidths=0.5, alpha=0.8)
    ax.plot([0, 100], [0, 100], color="black", lw=1, ls=":", alpha=0.5)

    ax.set_xlabel("Edward Score V23", fontsize=12)
    ax.set_ylabel("Edward Score V24", fontsize=12)
    ax.set_title(f"Score Drift: V23 → V24 — 2025 Drug Data (N={n})",
                 fontsize=13, fontweight="bold")
    ax.set_xlim([0, 100]); ax.set_ylim([0, 100])
    ax.grid(True, alpha=0.2)

    # Custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ECC71',
               markersize=10, markeredgecolor='black', label='Approved'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#E74C3C',
               markersize=10, markeredgecolor='black', label='Failed'),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=11)

    out = os.path.join(OUT_DIR, "2025_v23_vs_v24_score_drift.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── V24-only calibration (single panel with counts) ───────────────────
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("white")

    df_temp = pd.DataFrame({"score": s24, "outcome": outcome})
    df_temp["bin"] = pd.cut(df_temp["score"], bins=bins, labels=bin_labels, include_lowest=True)
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

    ax.set_title(f"V24 Calibration — 2025 Drug Data (N={n})", fontsize=14, fontweight="bold")
    ax.set_xlabel("Edward Score V24 Bin", fontsize=12)
    ax.set_ylabel("Proportion", fontsize=12)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left", fontsize=10)
    ax.set_ylim(0, 1.15)

    # Print bin counts
    ct_display = ct.copy()
    ct_display["Total"] = ct_display["Approved"] + ct_display["Liability"]
    ct_display["Approved %"] = (ct_display["Approved"] / ct_display["Total"] * 100).round(1)
    print("\nV24 Bin counts:")
    print(ct_display.to_string())

    out = os.path.join(OUT_DIR, "2025_v24_calibration.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Salah Verdict comparison ──────────────────────────────────────────
    print("\n--- Salah Verdict Distribution ---")
    for ver, vdf, score_col in [("V23", v23, "Edward Score V23"), ("V24", v24, "Edward Score V24")]:
        verdict_col = f"Salah Verdict {ver}"
        if verdict_col in vdf.columns:
            print(f"\n{ver}:")
            for verdict in ["ELITE", "CAUTION", "TERMINATE"]:
                mask = vdf[verdict_col] == verdict
                count = mask.sum()
                if count > 0:
                    scores = pd.to_numeric(vdf.loc[mask, score_col], errors="coerce")
                    app = (vdf.loc[mask, "category"] == "Approved").sum()
                    print(f"  {verdict}: {count} (Approved={app}, Failed={count-app}, median score={scores.median():.0f})")

    print("\nDone!")


if __name__ == "__main__":
    main()
