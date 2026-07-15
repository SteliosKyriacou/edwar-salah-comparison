import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os
import numpy as np

BASE = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE, "V25_big.csv")
if not os.path.exists(DATA_FILE):
    DATA_FILE = os.path.join(BASE, "v25_results_Masterdoc_for_validated_drugs_to_use_2 20260616.csv")

def generate_individual_plots(df, model_name, score_col, truth_col, raw_score_col):
    """Generate ROC, PRC, Calibration, and Scatter for a single model."""
    valid = ~df[score_col].isna() & ~df[truth_col].isna() & ~df[raw_score_col].isna()
    if not valid.any():
        return
        
    y_true = df[truth_col][valid]
    scores = df[score_col][valid]
    raw_scores = df[raw_score_col][valid]
    
    n = len(y_true)
    n_pos = y_true.sum()
    baseline = n_pos / n if n > 0 else 0
    
    # ── ROC ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    
    fpr, tpr, _ = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, color="#9B59B6", lw=2.5, label=f"MedChem Score AUC: {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC — MedChem Score", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    
    out = os.path.join(BASE, f"{model_name}_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")
    
    # ── PRC ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    
    prec, rec, _ = precision_recall_curve(y_true, scores)
    ap = average_precision_score(y_true, scores)
    ax.plot(rec, prec, color="#9B59B6", lw=2.5, label=f"MedChem Score AP: {ap:.3f}")
    ax.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1, label=f"Random ({baseline:.2f})")
    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title(f"PRC — MedChem Score", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    
    out = os.path.join(BASE, f"{model_name}_prc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")
    
    # ── Calibration ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    
    score_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    score_labels = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"]
    
    df_temp = pd.DataFrame({"val": raw_scores, "outcome": df['outcome'][valid]})
    df_temp["bin"] = pd.cut(df_temp["val"], bins=score_bins, labels=score_labels, include_lowest=True)
    ct = pd.crosstab(df_temp["bin"], df_temp["outcome"])
    
    all_cats = ["Approved", "Market Failure", "Scientific Failure", "Other Failure"]
    all_colors = ["#B7E4C7", "orange", "red", "grey"]
    
    present_cats = [c for c in all_cats if c in df_temp["outcome"].unique()]
    for c in present_cats:
        if c not in ct.columns:
            ct[c] = 0
            
    ct = ct[present_cats]
    plot_colors = [all_colors[all_cats.index(c)] for c in present_cats]
    
    ct_norm = ct.div(ct.sum(axis=1), axis=0).fillna(0)
    ct_norm.plot(kind="bar", stacked=True, ax=ax, color=plot_colors, edgecolor="black", width=0.8)
    
    for i, (idx, row) in enumerate(ct.iterrows()):
        total = row.sum()
        if total > 0:
            ax.text(i, 1.02, f"n={int(total)}", ha="center", va="bottom", fontsize=9, fontweight="bold")
            
    ax.set_title(f"Calibration — {model_name}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Raw MedChem Score", fontsize=11)
    ax.set_ylabel("Proportion", fontsize=11)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(0, 1.15)
    
    out = os.path.join(BASE, f"{model_name}_calibration.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")
    
    # ── Scatter ────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    colors = ["#2ECC71" if y == 1 else "#E74C3C" for y in y_true]
    
    x_jitter = np.random.normal(0, 0.1, size=len(raw_scores)) + np.where(y_true == 1, 1, 0)
    
    ax.scatter(x_jitter, raw_scores, c=colors, s=80, edgecolors="black", linewidths=0.5, alpha=0.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Failed", "Approved"])
    ax.set_ylabel(f"Raw {model_name} Score", fontsize=12)
    ax.set_title(f"{model_name} Score Distribution", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.2)
    out = os.path.join(BASE, f"{model_name}_scatter.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")

def main():
    print(f"Loading {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    
    if "Status categorized" not in df.columns:
        print("Column 'Status categorized' not found!")
        return
        
    df['Status categorized'] = df['Status categorized'].astype(str).str.lower().str.strip()
    df = df[df['Status categorized'].isin(['approved', 'failed'])].copy()
    print(f"Filtered for approved/failed: N={len(df)}")
    
    df['y_true'] = (df['Status categorized'] == 'approved').astype(int)
    def map_outcome(row):
        if str(row['Status categorized']).lower().strip() == 'approved':
            return 'Approved'
        else:
            reason = str(row.get('failure reason', '')).lower().strip()
            if 'market failure' in reason:
                return 'Market Failure'
            elif 'scientific failure' in reason:
                return 'Scientific Failure'
            else:
                return 'Other Failure'
    df['outcome'] = df.apply(map_outcome, axis=1)
    
    score_col = "MedChem Score V25"
    if score_col not in df.columns:
        print(f"Score column {score_col} not found!")
        return
        
    df['Score_num'] = pd.to_numeric(df[score_col], errors='coerce')
    
    corr = df['Score_num'].corr(df['y_true'])
    print(f"Correlation of score with y_true: {corr:.3f}")
    if corr < 0:
        max_score = df['Score_num'].max()
        if max_score > 1.0:
            df['Model_Prob'] = 100 - df['Score_num']
        else:
            df['Model_Prob'] = 1.0 - df['Score_num']
    else:
        df['Model_Prob'] = df['Score_num']

    print(f"Valid scores: {df['Model_Prob'].notna().sum()}")
    generate_individual_plots(df, "Big-Ramil_V25", "Model_Prob", "y_true", "Score_num")

    # Generate Science-Only subset plots
    df_science = df[df['outcome'].isin(['Approved', 'Scientific Failure'])].copy()
    print(f"Valid scores (Science Only): {df_science['Model_Prob'].notna().sum()}")
    generate_individual_plots(df_science, "Big-Ramil_V25_ScienceOnly", "Model_Prob", "y_true", "Score_num")

if __name__ == "__main__":
    main()
