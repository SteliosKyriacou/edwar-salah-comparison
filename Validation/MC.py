import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. Simulation Parameters & Base Rates
# ==========================================
# Hardcode historical returns
mean_success_return = 2.3156
mean_failure_return = -0.8088

# Base rates (The 90% Failure Environment)
prob_success = 0.10
prob_failure = 0.90

# Fund Settings
np.random.seed(42)
num_simulations = 1000
years = 10
initial_aum = 100_000_000
events_per_year = 100
accuracy = 0.80

# Liquidity Constraints
max_investible_capital = 735_000_000 # The 5% SEC Liquidity limit
max_position_size = max_investible_capital / events_per_year
risk_free_rate = 0.05

# ==========================================
# 2. Run 10-Year Monte Carlo
# ==========================================
aum_trajectories = np.zeros((num_simulations, years + 1))
aum_trajectories[:, 0] = initial_aum

for sim in range(num_simulations):
    current_aum = initial_aum
    for year in range(1, years + 1):
        if current_aum <= 0:
            aum_trajectories[sim, year] = 0
            continue
        
        # Deployment Math
        desired_position = current_aum / events_per_year
        actual_position = min(desired_position, max_position_size)
        deployed_capital = actual_position * events_per_year
        undeployed_capital = max(0, current_aum - deployed_capital)
        
        trading_profit = 0
        
        # Simulate all 100 bets for the year
        for event in range(events_per_year):
            actual_outcome = 'Success' if np.random.rand() < prob_success else 'Failure'
            is_correct = np.random.rand() < accuracy
            
            if actual_outcome == 'Success':
                if is_correct: 
                    trading_profit += actual_position * mean_success_return
                else: 
                    trading_profit += actual_position * (-mean_success_return)
            else:
                if is_correct: 
                    trading_profit += actual_position * (-mean_failure_return)
                else: 
                    trading_profit += actual_position * mean_failure_return

        # Cash Drag Math
        cash_interest = undeployed_capital * risk_free_rate
        current_aum += (trading_profit + cash_interest)
        
        if current_aum <= 0: current_aum = 0
                 
        aum_trajectories[sim, year] = current_aum

# ==========================================
# 3. Data Processing for Plots
# ==========================================
# Calculate Final AUMs
final_aums = aum_trajectories[:, -1]
mean_final_aum = np.mean(final_aums)

# Calculate Year-over-Year Percentage Returns
yearly_returns = np.zeros((num_simulations, years))
for year in range(1, years + 1):
    prev_aum = aum_trajectories[:, year-1]
    mask = prev_aum > 0
    yearly_returns[mask, year-1] = (aum_trajectories[mask, year] - prev_aum[mask]) / prev_aum[mask]

mean_yearly_returns = np.mean(yearly_returns, axis=0) * 100

# ==========================================
# 4. Generate Visualizations (4 Separate Figures)
# ==========================================

# --- PLOT 1: AUM Trajectories & Distribution ---
fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
for i in range(100): # Plot first 100 lines for visibility
    ax1.plot(range(years + 1), aum_trajectories[i] / 1e6, color='blue', alpha=0.1)
ax1.plot(range(years + 1), np.mean(aum_trajectories, axis=0) / 1e6, color='red', linewidth=2, label='Mean AUM')
ax1.set_title('AUM Trajectories (10 Years)')
ax1.set_xlabel('Year')
ax1.set_ylabel('AUM (Millions USD)')
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend()

ax2.hist(final_aums / 1e6, bins=30, color='purple', alpha=0.7, edgecolor='black')
ax2.axvline(mean_final_aum / 1e6, color='red', linestyle='dashed', linewidth=2, label=f'Mean: ${mean_final_aum/1e6:,.0f}M')
ax2.set_title('Distribution of Year 10 AUM')
ax2.set_xlabel('Final AUM (Millions USD)')
ax2.set_ylabel('Frequency')
ax2.grid(axis='y', linestyle='--', alpha=0.5)
ax2.legend()
plt.tight_layout()
fig1.savefig('1_aum_trajectories.png')

# --- PLOT 2: Invested Capital vs Cash Drag ---
mean_aum_trajectory = np.mean(aum_trajectories, axis=0)
deployed_arr = np.minimum(mean_aum_trajectory, max_investible_capital)
bank_arr = np.maximum(0, mean_aum_trajectory - deployed_arr)

fig2, ax3 = plt.subplots(figsize=(10, 6))
ax3.bar(range(years + 1), deployed_arr / 1e6, label='Deployed Capital (Generating Alpha)', color='#2ca02c')
ax3.bar(range(years + 1), bank_arr / 1e6, bottom=deployed_arr / 1e6, label='Un-Deployed Capital (Earning 5%)', color='#7f7f7f', alpha=0.6)
ax3.plot(range(years + 1), mean_aum_trajectory / 1e6, marker='o', color='red', label='Total AUM', linewidth=2)
ax3.set_title('Capital Allocation (The $735M Ceiling)')
ax3.set_xlabel('Year')
ax3.set_ylabel('Capital (Millions USD)')
ax3.set_xticks(range(years + 1))
ax3.legend()
ax3.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
fig2.savefig('2_capital_allocation.png')

# --- PLOT 3: Year 1 vs Year 10 Return Histograms ---
fig3, axes = plt.subplots(1, 2, figsize=(14, 6))
axes[0].hist(yearly_returns[:, 0] * 100, bins=30, color='green', alpha=0.7, edgecolor='black')
axes[0].axvline(mean_yearly_returns[0], color='red', linestyle='dashed', linewidth=2, label=f"Mean: {mean_yearly_returns[0]:.2f}%")
axes[0].set_title('Year 1 Returns (100% Deployed)')
axes[0].set_xlabel('Yearly Return (%)')
axes[0].legend()
axes[0].grid(axis='y', linestyle='--', alpha=0.5)

axes[1].hist(yearly_returns[:, 9] * 100, bins=30, color='orange', alpha=0.7, edgecolor='black')
axes[1].axvline(mean_yearly_returns[9], color='red', linestyle='dashed', linewidth=2, label=f"Mean: {mean_yearly_returns[9]:.2f}%")
axes[1].set_title('Year 10 Returns (Heavy Cash Drag)')
axes[1].set_xlabel('Yearly Return (%)')
axes[1].legend()
axes[1].grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
fig3.savefig('3_return_histograms.png')

# --- PLOT 4: Average Yearly Returns Over Time (The "Yield Decay" Curve) ---
fig4, ax4 = plt.subplots(figsize=(10, 6))

# Plotting the decay of yield
ax4.plot(range(1, years + 1), mean_yearly_returns, marker='s', markersize=8, color='firebrick', linewidth=3)

# Formatting the visual
ax4.set_title('The Yield Decay Curve: Annual Percentage Returns over 10 Years', fontsize=14, fontweight='bold')
ax4.set_xlabel('Trading Year', fontsize=12)
ax4.set_ylabel('Average Yearly Return (%)', fontsize=12)
ax4.set_xticks(range(1, years + 1))
ax4.set_ylim(0, 70)
ax4.grid(True, linestyle='--', alpha=0.6)

# Adding data labels to the points for clarity
for i, txt in enumerate(mean_yearly_returns):
    ax4.annotate(f"{txt:.1f}%", (range(1, years + 1)[i], mean_yearly_returns[i] + 2), 
                 ha='center', fontsize=10, fontweight='bold')

# Adding a shaded region to show where the "Cash Drag" kicks in
ax4.axvspan(5.5, 10.5, color='gray', alpha=0.1, label='Cash Drag Dominance Phase')
ax4.legend(loc='lower left')

plt.tight_layout()
fig4.savefig('4_yield_decay_curve.png')

plt.show()