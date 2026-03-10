"""Generate V20 vs V22 vs V23 figures for Global set (modern + legacy)."""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(BASE, "Salah", "global")

V20_FILE = os.path.join(OUT_DIR, "SM_V20_EDWARD_ONLY_GLOBAL.csv")
V22_FILE = os.path.join(OUT_DIR, "SM_V22_EDWARD_SALAH_GLOBAL.csv")
V23_FILE = os.path.join(OUT_DIR, "SM_V23_EDWARD_SALAH_GLOBAL.csv")


def main():
    v20 = pd.read_csv(V20_FILE)
    v22 = pd.read_csv(V22_FILE)
    v23 = pd.read_csv(V23_FILE)

    s20 = pd.to_numeric(v20["Edward Score V20"], errors="coerce")
    s22 = pd.to_numeric(v22["Edward Score V22"], errors="coerce")
    s23 = pd.to_numeric(v23["Edward Score V23"], errors="coerce")
    y_true = (v22["category"] == "approved").astype(int)

    n = len(y_true)
    n_pos = y_true.sum()
    print(f"Global: N={n}, Approved={n_pos}, Failed={n - n_pos}")

    # ── ROC ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")

    for scores, label, color, lw, ls in [
        (s20, "V20 (Edward Only)", "#B0B0B0", 1.5, "--"),
        (s22, "V22 (Edward + Salah)", "#4A90E2", 2.0, "-"),
        (s23, "V23 (Calibrated Alerts)", "#2ECC71", 2.5, "-"),
    ]:
        pred = 101 - scores
        fpr, tpr, _ = roc_curve(y_true, pred)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, lw=lw, ls=ls,
                label=f"{label}  AUC: {roc_auc:.3f}")

    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC: V20 vs V22 vs V23 — Global (N={n}, {n_pos} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])

    out = os.path.join(OUT_DIR, "sm_v20_v22_v23_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── PRC ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    baseline = n_pos / n

    for scores, label, color, lw, ls in [
        (s20, "V20 (Edward Only)", "#B0B0B0", 1.5, "--"),
        (s22, "V22 (Edward + Salah)", "#4A90E2", 2.0, "-"),
        (s23, "V23 (Calibrated Alerts)", "#2ECC71", 2.5, "-"),
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
    ax.set_title(f"PRC: V20 vs V22 vs V23 — Global (N={n}, {n_pos} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])

    out = os.path.join(OUT_DIR, "sm_v20_v22_v23_prc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Calibration (3-panel) ──────────────────────────────────────────────
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(22, 7), sharey=True)
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    bin_labels = ["0-10", "10-20", "20-30", "30-40", "40-50",
                  "50-60", "60-70", "70-80", "80-90", "90-100"]

    outcome = v22["MedChem_Descriptor_Tag"].apply(
        lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability"
    )

    for ax, scores, title in [
        (ax1, s20, "V20 — Edward (No Biology)"),
        (ax2, s22, "V22 — Edward + Salah"),
        (ax3, s23, "V23 — Calibrated Alerts"),
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

    plt.suptitle(f"Calibration: V20 vs V22 vs V23 — Global (N={n})",
                 fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    out = os.path.join(OUT_DIR, "sm_v20_v22_v23_calibration.png")
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    # Also generate legacy-only figures
    LEGACY_DIR = os.path.join(BASE, "Salah", "legacy")
    v20l = pd.read_csv(os.path.join(LEGACY_DIR, "SM_V20_EDWARD_ONLY_LEGACY.csv"))
    v22l = pd.read_csv(os.path.join(LEGACY_DIR, "SM_V22_EDWARD_SALAH_LEGACY.csv"))
    v23l = pd.read_csv(os.path.join(LEGACY_DIR, "SM_V23_EDWARD_SALAH_LEGACY.csv"))

    s20l = pd.to_numeric(v20l["Edward Score V20"], errors="coerce")
    s22l = pd.to_numeric(v22l["Edward Score V22"], errors="coerce")
    s23l = pd.to_numeric(v23l["Edward Score V23"], errors="coerce")
    yl = (v22l["category"] == "approved").astype(int)
    nl = len(yl); npl = yl.sum()

    # Legacy ROC
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    for scores, label, color, lw, ls in [
        (s20l, "V20 (Edward Only)", "#B0B0B0", 1.5, "--"),
        (s22l, "V22 (Edward + Salah)", "#4A90E2", 2.0, "-"),
        (s23l, "V23 (Calibrated Alerts)", "#2ECC71", 2.5, "-"),
    ]:
        pred = 101 - scores
        fpr, tpr, _ = roc_curve(yl, pred)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, lw=lw, ls=ls,
                label=f"{label}  AUC: {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC: V20 vs V22 vs V23 — Legacy (N={nl}, {npl} approved)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    out = os.path.join(LEGACY_DIR, "sm_v20_v22_v23_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")

    print("\nDone!")


if __name__ == "__main__":
    main()
