import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

# Modern (>=1999) files
V20_FILE = os.path.join(BASE, "SM_V20_EDWARD_ONLY.csv")
V22_FILE = os.path.join(BASE, "SM_V22_EDWARD_SALAH.csv")
# Legacy (<1999) files
V20_LEGACY = os.path.join(BASE, "SM_V20_EDWARD_ONLY_LEGACY.csv")
V22_LEGACY = os.path.join(BASE, "SM_V22_EDWARD_SALAH_LEGACY.csv")

FIGURES_DIR = os.path.join(BASE, "Salah")



def plot_roc(df, out_dir, label):
    plt.figure(figsize=(10, 8))

    fpr20, tpr20, _ = roc_curve(df['label'], 101 - df['Edward Score V20'])
    auc20 = auc(fpr20, tpr20)
    plt.plot(fpr20, tpr20, color='#D3D3D3', lw=2, ls='--',
             label=f'Edward (No Biology) AUC: {auc20:.3f}')

    fpr22, tpr22, _ = roc_curve(df['label'], 101 - df['Edward Score V22'])
    auc22 = auc(fpr22, tpr22)
    plt.plot(fpr22, tpr22, color='#4A90E2', lw=3,
             label=f'Edward + Salah (Coordinated) AUC: {auc22:.3f}')

    plt.plot([0, 1], [0, 1], color='black', lw=1, ls=':')
    plt.title(f'ROC: Edward vs Edward+Salah — {label} (N={len(df)})',
              fontsize=14, fontweight='bold')
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.legend(loc="lower right", fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'sm_edward_vs_edward_salah_roc.png'), dpi=300)
    plt.close()
    print(f"  ROC saved (Edward AUC: {auc20:.3f}, Edward+Salah AUC: {auc22:.3f})")


def plot_calibration(df, out_dir, label):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    bin_labels = ['0-10', '10-20', '20-30', '30-40', '40-50',
                  '50-60', '60-70', '70-80', '80-90', '90-100']

    df = df.copy()
    df['outcome'] = df['MedChem_Descriptor_Tag'].apply(
        lambda x: 'Approved' if 'approved_control' in str(x).lower() else 'Liability'
    )

    for ax, col, title in [
        (ax1, 'Edward Score V20', 'Edward (No Biology)'),
        (ax2, 'Edward Score V22', 'Edward + Salah (Coordinated)')
    ]:
        df['bin'] = pd.cut(df[col], bins=bins, labels=bin_labels, include_lowest=True)
        pivot = pd.crosstab(df['bin'], df['outcome'], normalize='index')
        for c in ['Approved', 'Liability']:
            if c not in pivot.columns:
                pivot[c] = 0
        pivot = pivot[['Approved', 'Liability']]
        pivot.plot(kind='bar', stacked=True, ax=ax,
                   color=['#B7E4C7', '#FF7F50'], edgecolor='black', width=0.8)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_xlabel('Edward Score Bin', fontsize=11)
        ax.set_ylabel('Proportion', fontsize=11)
        ax.tick_params(axis='x', rotation=45)
        ax.legend(loc='upper left')

    plt.suptitle(f'Calibration: The "Salah Effect" — {label} (N={len(df)})',
                 fontsize=15, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(os.path.join(out_dir, 'sm_edward_vs_edward_salah_calibration.png'), dpi=300)
    plt.close()
    print("  Calibration saved")


def plot_factors(df, out_dir, label):
    tag_col = 'MedChem_Descriptor_Tag'
    v20_medians = df.groupby(tag_col)['Edward Score V20'].median()
    v22_medians = df.groupby(tag_col)['Edward Score V22'].median()

    comp_df = pd.DataFrame({'Edward': v20_medians, 'Edward+Salah': v22_medians}).sort_values('Edward+Salah')
    comp_df['Delta'] = comp_df['Edward+Salah'] - comp_df['Edward']

    fig_height = max(8, len(comp_df) * 0.55)
    plt.figure(figsize=(12, fig_height))
    y_range = range(len(comp_df))

    plt.hlines(y=y_range, xmin=comp_df['Edward'], xmax=comp_df['Edward+Salah'],
               color='grey', alpha=0.5)
    plt.scatter(comp_df['Edward'], y_range, color='#B7E4C7',
                label='Edward (No Biology)', s=100, edgecolors='black', zorder=3)
    plt.scatter(comp_df['Edward+Salah'], y_range, color='#4A90E2',
                label='Edward + Salah', s=100, edgecolors='black', zorder=3)

    for i, (idx, row) in enumerate(comp_df.iterrows()):
        delta = row['Delta']
        if abs(delta) > 3:
            x_pos = max(row['Edward'], row['Edward+Salah']) + 2
            color = '#E74C3C' if delta > 0 else '#27AE60'
            plt.text(x_pos, i, f"{delta:+.0f}", va='center',
                     fontsize=9, fontweight='bold', color=color)

    plt.yticks(y_range, comp_df.index, fontsize=9)
    plt.title(f'Median Score Shift by Clinical Tag — "Salah Effect" — {label} (N={len(df)})',
              fontsize=14, fontweight='bold')
    plt.xlabel('Median Edward Score (Lower = Better)', fontsize=12)
    plt.legend(loc='lower right', fontsize=11)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'sm_edward_vs_edward_salah_factors.png'), dpi=300)
    plt.close()
    print("  Factors saved")


def plot_score_drift(df, out_dir, label):
    plt.figure(figsize=(10, 10))

    categories = df['category'].unique()
    palette = {
        'approved': '#B7E4C7',
        'clinical_failure': '#FF7F50',
        'market_withdrawal': '#E74C3C',
        'restricted': '#FFC107',
    }

    for cat in sorted(categories):
        mask = df['category'] == cat
        if mask.sum() > 0:
            color = palette.get(cat, '#AAAAAA')
            plt.scatter(df.loc[mask, 'Edward Score V20'],
                        df.loc[mask, 'Edward Score V22'],
                        c=color, label=f'{cat} (n={mask.sum()})',
                        s=50, alpha=0.7, edgecolors='black', linewidths=0.5)

    plt.plot([0, 100], [0, 100], 'k--', alpha=0.3, label='No Change')
    plt.xlabel('Edward Score (No Biology)', fontsize=13)
    plt.ylabel('Edward + Salah Score (Coordinated)', fontsize=13)
    plt.title(f'Score Drift: Biological Penalty Map — {label} (N={len(df)})',
              fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=10)
    plt.xlim(0, 105)
    plt.ylim(0, 105)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'sm_edward_vs_edward_salah_score_drift.png'), dpi=300)
    plt.close()
    print("  Score Drift saved")


def load_modern_data():
    v20 = pd.read_csv(V20_FILE)
    v22 = pd.read_csv(V22_FILE)
    return _merge_v20_v22(v20, v22)


def load_legacy_data():
    v20 = pd.read_csv(V20_LEGACY)
    v22 = pd.read_csv(V22_LEGACY)
    return _merge_v20_v22(v20, v22)


def load_global_data():
    v20 = pd.concat([pd.read_csv(V20_FILE), pd.read_csv(V20_LEGACY)], ignore_index=True)
    v22 = pd.concat([pd.read_csv(V22_FILE), pd.read_csv(V22_LEGACY)], ignore_index=True)
    return _merge_v20_v22(v20, v22)


def _merge_v20_v22(v20, v22):
    v22_cols = [c for c in v22.columns if 'V22' in c or c in ('salah_verdict', 'biological_risk')]
    v22_specific = v22[v22_cols]
    df = pd.concat([v20.reset_index(drop=True), v22_specific.reset_index(drop=True)], axis=1)
    df['Edward Score V20'] = pd.to_numeric(df['Edward Score V20'], errors='coerce')
    df['Edward Score V22'] = pd.to_numeric(df['Edward Score V22'], errors='coerce')
    df = df.dropna(subset=['Edward Score V20', 'Edward Score V22'])
    df['label'] = df['MedChem_Descriptor_Tag'].apply(
        lambda x: 1 if 'approved_control' in str(x).lower() else 0
    )
    return df


def generate_figures(df, out_dir, label):
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n=== {label}: {len(df)} molecules ===")

    # Temporarily override FIGURES_DIR for plot functions
    plot_roc(df, out_dir, label)
    plot_calibration(df, out_dir, label)
    plot_factors(df, out_dir, label)
    plot_score_drift(df, out_dir, label)

    print(f"  All figures saved to {out_dir}/")


def main():
    # 1. Modern (>=1999) — already exists but regenerate
    modern_dir = os.path.join(FIGURES_DIR, "modern")
    df_modern = load_modern_data()
    generate_figures(df_modern, modern_dir, "Modern (>=1999)")

    # 2. Legacy (<1999)
    legacy_dir = os.path.join(FIGURES_DIR, "legacy")
    df_legacy = load_legacy_data()
    generate_figures(df_legacy, legacy_dir, "Legacy (<1999)")

    # 3. Global (all)
    global_dir = os.path.join(FIGURES_DIR, "global")
    df_global = load_global_data()
    generate_figures(df_global, global_dir, "Global (All Molecules)")


if __name__ == "__main__":
    main()
