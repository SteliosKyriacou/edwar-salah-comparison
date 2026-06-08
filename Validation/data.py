import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import os
import numpy as np

# 1. Load your dataset
csv_filename = 'Single Asset pharma - Sheet1 (1).csv'
df = pd.read_csv(csv_filename)

# Clean up pricing columns
df['Post-Price ($)'] = pd.to_numeric(df['Post-Price ($)'], errors='coerce')
df['Pre-Price ($)'] = pd.to_numeric(df['Pre-Price ($)'], errors='coerce')

# Create a folder to save all 60 plots
output_dir = "Annotated_Stock_Plots"
os.makedirs(output_dir, exist_ok=True)

print(f"Processing {len(df)} stocks...")

for idx, row in df.iterrows():
    ticker = str(row['Ticker']).strip()
    company = str(row['Company'])
    outcome = str(row['Outcome'])
    pre_price = row['Pre-Price ($)']
    post_price = row['Post-Price ($)']
    drug = str(row['Drug/Asset'])
    indication = str(row['Indication'])
    note = str(row['Note'])
    
    # Skip if ticker is missing
    if ticker.upper() == 'NAN' or not ticker:
        print(f"Skipping {company} - No ticker provided.")
        continue
        
    print(f"Fetching data for {ticker}...")
    
    try:
        # 2. Fetch Daily Historical Data
        stock = yf.Ticker(ticker)
        # Pulling max historical daily data
        hist = stock.history(period="max")
        
        if hist.empty:
            print(f"  -> No data found for {ticker} (may be delisted or private).")
            continue
            
        # 3. Create the Plot
        plt.figure(figsize=(12, 6))
        plt.plot(hist.index, hist['Close'], color='#1f77b4', linewidth=1.5)
        plt.title(f"{company} ({ticker}) - Daily Price History", fontsize=14, fontweight='bold')
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Close Price ($)", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)
        
        # 4. Determine Special Annotations (Acquisition / Death)
        special_note = ""
        if "acq" in outcome.lower() or "acq" in note.lower() or "buyout" in note.lower():
            special_note = f"\n--> ACQUIRED @ ${post_price}" if pd.notna(post_price) else "\n--> ACQUIRED"
        elif "fail" in outcome.lower() or "crl" in outcome.lower() or "death" in note.lower() or "bankrupt" in note.lower():
            special_note = "\n--> FAILURE / DEATH"

        # 5. Build Clinical Annotation Box
        ann_text = (
            f"Asset: {drug}\n"
            f"Indication: {indication}\n"
            f"Outcome: {outcome}\n"
            f"Event Impact: ${pre_price} -> ${post_price}\n"
            f"Note: {note if note.lower() != 'nan' else 'None'}"
            f"{special_note}"
        )
        
        # Place annotation box in the top left corner
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.85, edgecolor='gray')
        plt.text(0.02, 0.95, ann_text, transform=plt.gca().transAxes, fontsize=10,
                 verticalalignment='top', bbox=props, fontweight='medium')
        
        # 6. Save the Plot
        plt.tight_layout()
        safe_ticker = ticker.replace("^", "").replace(".", "-")
        plot_path = os.path.join(output_dir, f"{safe_ticker}_clinical_history.png")
        plt.savefig(plot_path, dpi=200)
        plt.close()
        print(f"  -> Saved {plot_path}")
        
    except Exception as e:
        print(f"  -> Error processing {ticker}: {e}")

print(f"\nAll available stock plots have been saved in the '{output_dir}' folder.")