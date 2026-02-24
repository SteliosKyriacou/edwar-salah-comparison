import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import os

# Files
EDWARD_V22 = "/home/node/.openclaw/workspace/Edward_test/EDWARD_V22_COORDINATED_MODERN.csv"
OUTPUT_BAR = "/home/node/.openclaw/workspace/Edward_test/edward_v22_coordinated_calibration.png"
OUTPUT_ROC = "/home/node/.openclaw/workspace/Edward_test/edward_v22_coordinated_roc.png"
OUTPUT_DRIVERS = "/home/node/.openclaw/workspace/Edward_test/edward_v22_coordinated_risk_drivers.png"

def generate_v22_visuals():
    # 1. Load Data
    df = pd.read_csv(EDWARD_V22)
    score_col = 'Edward Score V22'
    df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
    df = df.dropna(subset=[score_col])

    # --- A. Bins Chart ---
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100']
    df['Bin'] = pd.cut(df[score_col], bins=bins, labels=labels, include_lowest=True)
    
    def map_outcome(row):
        tag = str(row.get('MedChem_Descriptor_Tag', '')).strip().lower()
        if 'approved_control' in tag: return 'Approved Success'
        return 'Liability / Failure'

    df['Outcome_Category'] = df.apply(map_outcome, axis=1)
    pivot = pd.crosstab(df['Bin'], df['Outcome_Category'], normalize='index')
    
    plt.figure(figsize=(12, 7))
    pivot.plot(kind='bar', stacked=True, color=['#B7E4C7', '#FF7F50'], width=0.8, ax=plt.gca(), edgecolor='black', linewidth=0.5)
    plt.title('Edward V22 (Edward x Salah) Modern Era Calibration (N=270)', fontsize=14, fontweight='bold')
    plt.ylabel('Proportion')
    plt.xlabel('Edward Score (1=Elite, 100=Trash)')
    plt.xticks(rotation=0)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(OUTPUT_BAR, dpi=300)
    plt.close()

    # --- B. ROC Curve ---
    df['label'] = df['MedChem_Descriptor_Tag'].apply(lambda x: 1 if 'approved_control' in str(x).lower() else 0)
    y_scores = 101 - df[score_col]
    fpr, tpr, _ = roc_curve(df['label'], y_scores)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 8))
    plt.plot(fpr, tpr, color='#4A90E2', lw=3, label=f'Edward V22 (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='#D3D3D3', linestyle='--')
    plt.title(f'V22 Edward x Salah Master ROC (AUC: {roc_auc:.3f})', fontsize=14, fontweight='bold')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_ROC, dpi=300)
    plt.close()

    # --- C. Risk Drivers ---
    tag_col = 'MedChem_Descriptor_Tag'
    stats = df.groupby(tag_col)[score_col].median().sort_values()
    df['Label'] = df[tag_col].apply(lambda x: f"{x} (n={len(df[df[tag_col]==x])})")
    sorted_labels = [f"{tag} (n={len(df[df[tag_col]==tag])})" for tag in stats.index]
    
    plt.figure(figsize=(14, 22))
    sns.set_theme(style="whitegrid")
    ax = sns.boxplot(data=df, x=score_col, y='Label', order=sorted_labels, palette="RdYlGn_r", showfliers=False)
    sns.stripplot(data=df, x=score_col, y='Label', order=sorted_labels, color=".25", size=4, alpha=0.5, ax=ax, jitter=True)
    plt.title('V22 Master Risk Drivers vs. Edward Score (Edward x Salah)', fontsize=16, fontweight='bold')
    plt.xlabel('Edward Score (Cumulative Chem + Bio Risk)', fontsize=13)
    plt.ylabel('Modern Clinical Outcome', fontsize=13)
    plt.xlim(0, 105)
    plt.tight_layout()
    plt.savefig(OUTPUT_DRIVERS, dpi=300)
    plt.close()

if __name__ == "__main__":
    generate_v22_visuals()
