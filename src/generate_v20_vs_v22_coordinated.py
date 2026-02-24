import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import os

# Files
EDWARD_V22 = "/home/node/.openclaw/workspace/Edward_test/EDWARD_V22_COORDINATED_MODERN.csv"
OUTPUT_COMP_BAR = "/home/node/.openclaw/workspace/Edward_test/edward_v20_vs_v22_modern_calibration.png"
OUTPUT_COMP_ROC = "/home/node/.openclaw/workspace/Edward_test/edward_v20_vs_v22_modern_roc.png"
OUTPUT_FACTORS = "/home/node/.openclaw/workspace/Edward_test/edward_v20_vs_v22_factors_comparison.png"

def generate_coordinated_comparisons():
    # 1. Load Data (Modern N=270 only)
    df = pd.read_csv(EDWARD_V22)
    
    v20_col = 'Edward Score V20'
    v22_col = 'Edward Score V22'
    df[v20_col] = pd.to_numeric(df[v20_col], errors='coerce')
    df[v22_col] = pd.to_numeric(df[v22_col], errors='coerce')
    df = df.dropna(subset=[v20_col, v22_col])
    
    df['label'] = df['MedChem_Descriptor_Tag'].apply(lambda x: 1 if 'approved_control' in str(x).lower() else 0)

    # --- A. ROC Comparison ---
    plt.figure(figsize=(10, 8))
    fpr20, tpr20, _ = roc_curve(df['label'], 101 - df[v20_col])
    auc20 = auc(fpr20, tpr20)
    plt.plot(fpr20, tpr20, color='#D3D3D3', lw=2, ls='--', label=f'V20 (Pure Chem) AUC: {auc20:.3f}')
    
    fpr22, tpr22, _ = roc_curve(df['label'], 101 - df[v22_col])
    auc22 = auc(fpr22, tpr22)
    plt.plot(fpr22, tpr22, color='#4A90E2', lw=3, label=f'V22 (Chem + Bio) AUC: {auc22:.3f}')
    
    plt.plot([0,1],[0,1], color='black', lw=1, ls=':')
    plt.title('Intelligence Spike: V20 vs V22 (Modern Era N=270)', fontsize=14, fontweight='bold')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.savefig(OUTPUT_COMP_ROC, dpi=300)
    plt.close()

    # --- B. Side-by-Side Calibration Bins (Global Modern) ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = ['0-10','10-20','20-30','30-40','40-50','50-60','60-70','70-80','80-90','90-100']
    
    def get_pivot(col):
        df['B'] = pd.cut(df[col], bins=bins, labels=labels, include_lowest=True)
        def map_cat(row):
            return 'Approved' if 'approved_control' in str(row['MedChem_Descriptor_Tag']).lower() else 'Liability'
        df['C'] = df.apply(map_cat, axis=1)
        return pd.crosstab(df['B'], df['C'], normalize='index')

    p1 = get_pivot(v20_col)
    p1.plot(kind='bar', stacked=True, ax=ax1, color=['#B7E4C7', '#FF7F50'], edgecolor='black', width=0.8)
    ax1.set_title('V20 (Pure Chem) Calibration', fontsize=12)
    
    p2 = get_pivot(v22_col)
    p2.plot(kind='bar', stacked=True, ax=ax2, color=['#B7E4C7', '#FF7F50'], edgecolor='black', width=0.8)
    ax2.set_title('V22 (Coordinated) Calibration', fontsize=12)
    
    plt.suptitle('Calibration Shift: The "Salah Effect" on the Modern Dataset', fontsize=15, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(OUTPUT_COMP_BAR, dpi=300)
    plt.close()

    # --- C. Factors Plot (Median Score Comparison by Tag) ---
    tag_col = 'MedChem_Descriptor_Tag'
    v20_means = df.groupby(tag_col)[v20_col].median()
    v22_means = df.groupby(tag_col)[v22_col].median()
    
    comp_df = pd.DataFrame({'V20': v20_means, 'V22': v22_means}).sort_values('V22')
    comp_df['Delta'] = comp_df['V22'] - comp_df['V20']
    
    plt.figure(figsize=(12, 18))
    y_range = range(len(comp_df))
    plt.hlines(y=y_range, xmin=comp_df['V20'], xmax=comp_df['V22'], color='grey', alpha=0.5)
    plt.scatter(comp_df['V20'], y_range, color='#B7E4C7', label='V20 (Pure Chem)', s=100, edgecolors='black')
    plt.scatter(comp_df['V22'], y_range, color='#4A90E2', label='V22 (Coordinated)', s=100, edgecolors='black')
    
    for i, delta in enumerate(comp_df['Delta']):
        if abs(delta) > 5:
            plt.text(max(comp_df['V20'][i], comp_df['V22'][i]) + 2, i, f"+{int(delta)}", va='center', fontsize=9, fontweight='bold', color='#E74C3C')

    plt.yticks(y_range, comp_df.index)
    plt.title('The "Biology Insight" Factor: Median Score Shift by Clinical Tag\n(Modern Era N=270)', fontsize=15, fontweight='bold')
    plt.xlabel('Median Edward Score (Lower is better)')
    plt.legend()
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_FACTORS, dpi=300)
    plt.close()

if __name__ == "__main__":
    generate_coordinated_comparisons()
