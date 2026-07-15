import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv("V25_big.csv")

# Filter out empty or missing routes
if "administration route" in df.columns:
    df["administration route"] = df["administration route"].fillna("")
    valid_routes = df[df["administration route"] != ""]["administration route"]
    
    # Get value counts
    counts = valid_routes.value_counts()
    
    # Set premium aesthetic style
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create an elegant barplot using seaborn
    sns.barplot(x=counts.index, y=counts.values, palette="viridis", ax=ax, edgecolor="none")
    
    # Styling
    ax.set_title("Administration Routes (Classified So Far)", fontsize=16, fontweight="bold", pad=20, color="white")
    ax.set_ylabel("Number of Drugs", fontsize=12, color="lightgray")
    ax.set_xlabel("Route of Administration", fontsize=12, color="lightgray")
    ax.tick_params(axis="x", rotation=45, colors="white", labelsize=11)
    ax.tick_params(axis="y", colors="white", labelsize=11)
    
    # Remove borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("gray")
    ax.spines["bottom"].set_color("gray")
    
    # Add data labels on top of bars
    for i, v in enumerate(counts.values):
        ax.text(i, v + (counts.max()*0.02), str(v), color="white", ha="center", fontweight="bold", fontsize=10)
        
    plt.tight_layout()
    plt.savefig("route_counts.png", dpi=300, transparent=False)
    print("Saved bar chart to route_counts.png!")
else:
    print("Column 'administration route' not found yet.")
