import random
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np
from parametros import parameters as params


@dataclass
class Cow:
    age: int                      # months
    pregnant: bool = False
    months_pregnant: int = 0
    months_since_last_birth: int = 999
    owned: bool = True
    alive: bool = True

class HerdSimulation:
    def __init__(self, params):
        self.p = params
        self.cows = []
        self.cashflow = []
        self.revenue_series = []
        self.cost_series = []
        self.net_worth_series = [] # Correct series name from last successful run
        
        self.initial_cash = -params["Initial cows"] * params["Purchase price per cow"]
        self.cumulative_cash = self.initial_cash 
        self.grown_cow_amount_series = [0]
        self.cow_amount_pregnant_series = [0]
        self.carf_amount_series = [0]
        self.total_cattle_series = [0]
        self.death_series = []
        self.sold_series = []
        self.births_series = []
        self.alquiler_series = []
        self.cows_purchased_series = []
        self.time = 0

        initial_herd_value = 0
        purchase_age = params["Minimum age for getting pregnant"] + params["Months into pregnancy"] + params["Amount of previous pregnancies"] * (params["Min months between pregnancies"] + params["Gestation length"])
        
        for _ in range(params["Initial cows"]):
            cow = Cow(
                age=purchase_age,
                pregnant=True,
                months_pregnant=params["Months into pregnancy"],
            )
            self.cows.append(cow)
            self.grown_cow_amount_series[0] += 1
            self.cow_amount_pregnant_series[0] += 1
            initial_herd_value += params["Purchase price per cow"] 
        
        # Initial Total Net Worth
        self.net_worth_series.append(self.cumulative_cash + initial_herd_value) 
        self.total_cattle_series[0] = self.grown_cow_amount_series[0] + self.carf_amount_series[0]

    def monthly_mortality(self, cow):
        if cow.age < 12:
            # Calves: High mortality rate
            return self.p["Offspring mortality rate"]
        
        life_months_base = self.p["Life expectancy"] * 12 # 12 years * 12 months = 144 months base
        base_mortality = 1 / life_months_base / 5 # Base mortality for prime years # /5 because the rate mortality is not that high!

        if cow.age <= self.p["Prime age end (months)"]:
            # Prime Age: Low, constant mortality
            return base_mortality
        else:
            # Aging Cows: Mortality increases exponentially past prime age
            age_over_prime = cow.age - self.p["Prime age end (months)"]
            
            # Simple exponential increase: base_mortality * exp(age_over_prime / scaling_factor)
            # The scaling factor (e.g., 20) controls how fast the risk climbs.
            scaling_factor = 20
            increased_mortality = base_mortality * np.exp(age_over_prime / scaling_factor)
            
            # Ensure mortality doesn't exceed 1 (or 100%) but should cap around a high number like 0.5 per month
            return min(increased_mortality, 0.5)

    def step(self):
        self.time +=1
        births = []
        deaths = 0
        revenue = 0
        costs = 0
        sold = 0
        sold_total = 0 # Track total cows/calves sold before rent deduction
        alquiler = 0
        purchased = 0
        calves_sold_this_month = 0

        cows_to_remove_after_step = []

        for cow in self.cows:
            if not cow.alive:
                continue

            cow.age += 1
            cow.months_since_last_birth += 1

            # Mortality
            if random.random() < self.monthly_mortality(cow):
                cow.alive = False
                deaths += 1
                continue

            # Pregnancy progression
            if cow.pregnant:
                cow.months_pregnant += 1
                if cow.months_pregnant >= self.p["Gestation length"]:
                    births.append(cow)
                    cow.pregnant = False
                    cow.months_pregnant = 0
                    cow.months_since_last_birth = 0

            # New pregnancy
            if (
                not cow.pregnant
                and cow.age >= self.p["Minimum age for getting pregnant"]
                and cow.months_since_last_birth >= self.p["Min months between pregnancies"]
                and random.random() < self.p["Monthly pregnancy probability"]
            ):
                cow.pregnant = True
                cow.months_pregnant = 0

            # Costs (applied to all owned, living cattle)
            if cow.owned:
                costs += self.p["Vaccines & registration per cow per year"] / 12

        # Handle births
        for mother in births:
            calf = Cow(age=0, owned=True)
            self.cows.append(calf)


        # Scheduled Purchase Logic
        if self.p["Scheduled purchase period (months)"] > 0 and \
           self.time % self.p["Scheduled purchase period (months)"] == 0:
            
            num_to_buy = self.p["Cows to buy per period"]
            purchased += num_to_buy
            costs += num_to_buy * self.p["Purchase price per cow"]

            for _ in range(num_to_buy):
                new_cow_age = params["Minimum age for getting pregnant"] + params["Months into pregnancy"] + params["Amount of previous pregnancies"] * (params["Min months between pregnancies"] + params["Gestation length"])

                new_cow = Cow(
                    age=new_cow_age,
                    pregnant=True,
                    months_pregnant=self.p["Months into pregnancy"],
                )
                self.cows.append(new_cow)


        # 5. Selling/Culling Logic
        if cow.owned and self.time >= self.p["Minimum time before selling anything (months)"]:
            
            is_calf = cow.age < 12
            is_grown_cow = cow.age >= 12
            current_sell_probability = self.p["Sell probability (monthly)"]
            
            # Check for culling age for grown cows
            if is_grown_cow and cow.age >= self.p["Cull age probability threshold (months)"]:
                current_sell_probability = self.p["High cull probability (monthly)"]
            
            # Check for calf management strategy based on "Min years before holding calves"
            if is_calf:
                if cow.age < self.p["Min calf sell age (months)"]:
                    current_sell_probability = 0.0 # Block sale if too young
                elif self.time < self.p["Min years before holding calves"] * 12:
                    current_sell_probability = self.p["High calves probability (monthly)"]
                else: # The calf is old enough to be sold, and we are in a period in which we may keep some calves.
                    current_sell_probability = self.p["Medium calves probability (monthly)"]
                
            # Execute Sale/Cull
            if current_sell_probability > 0.0 and random.random() < current_sell_probability:
                cow.alive = False
                cows_to_remove_after_step.append(cow)
                sold_total += 1
                
                if is_calf:
                    revenue += self.p["Offspring sale price"]
                    calves_sold_this_month += 1
                else:
                    revenue += self.p["Cull price per cow"]


        # 8. Alquiler/Rent Payment (Based on Calves Sold)
    
        # Deduct the value of the 'rent' calves from total revenue (they were counted in revenue above)
        revenue -= calves_sold_this_month * self.p["Offspring sale price"] * self.p["Land owner take on calf sell"]
            
        net = revenue - costs
        self.cumulative_cash += net

        
        owned_alive_cows = [c for c in self.cows if c.alive and c.owned]

        herd_value = 0
        carf_amount = 0
        cow_amount = 0

        for c in owned_alive_cows:
            if c.age < 12:
                carf_amount += 1
                herd_value += self.p["Offspring sale price"]
            else:
                cow_amount += 1
                herd_value += self.p["Purchase price per cow"]

        pregnant_cows = sum(1 for c in owned_alive_cows if c.pregnant)
        total_cattle = carf_amount + cow_amount


        # Calculate Total Net Worth
        net_worth = self.cumulative_cash + herd_value

        # --- Append Series ---
        self.cashflow.append(net)
        self.revenue_series.append(revenue)
        self.cost_series.append(costs)
        
        # Stock Series
        self.grown_cow_amount_series.append(cow_amount)
        self.carf_amount_series.append(carf_amount)
        self.total_cattle_series.append(total_cattle)
        self.cow_amount_pregnant_series.append(pregnant_cows)
        
        # Flow Series
        self.death_series.append(deaths)
        self.sold_series.append(sold)
        self.births_series.append(len(births))
        self.alquiler_series.append(alquiler)
        self.cows_purchased_series.append(purchased)
        
        # Net Worth Series
        self.net_worth_series.append(net_worth)

    def run(self):
        for _ in range(self.p["Simulation months"]):
            self.step()

        return {
            "final_cows_alive": sum(c.alive for c in self.cows),
            "cumulative_cash": self.cumulative_cash,
            "monthly_cashflow": self.cashflow,
        }


# ------------------ Run ------------------

sim = HerdSimulation(params)
sim.run()

# ------------------ Prepare Data for Plotting ------------------

# Cumulative Cashflow (starts at month 0 with initial cash)
initial_cash = sim.initial_cash 
cumulative_cashflow = np.cumsum([initial_cash] + sim.cashflow).tolist()

# The Net Worth calculation relies on the stock counters which are already
# initialized correctly in __init__ and updated in step.
net_worth_series = sim.net_worth_series

# Calculate the difference: Herd Value = Net Worth - Cumulative Cashflow
herd_value_series = np.subtract(net_worth_series, cumulative_cashflow).tolist()

# Define x-axis for stock variables (Month 0 to N)
x_values_stock = range(params["Simulation months"] + 1)


# ------------------ Plotting Group 1: Herd Composition ------------------
plt.style.use('ggplot')
fig1, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(x_values_stock, sim.grown_cow_amount_series, label="Grown Cows (Age > 12 months)", color='blue')
ax1.plot(x_values_stock, sim.carf_amount_series, label="Calves (Age < 12 months)", color='red')
ax1.plot(x_values_stock, sim.total_cattle_series, label="Total Cattle", color='black', linestyle='--')
ax1.plot(x_values_stock, sim.cow_amount_pregnant_series, label="Pregnant Cows", color='green', linestyle=':')

ax1.set_title("Herd Composition Over Time", fontsize=16)
ax1.set_xlabel("Month", fontsize=12)
ax1.set_ylabel("Number of Animals", fontsize=12)
ax1.legend(loc='upper left')
ax1.grid(True)
plt.tight_layout()
plt.savefig("herd_composition_plot.png")


# ------------------ Plotting Group 1: HERD COMPOSITION (WITH MARKERS) ------------------
plt.style.use('ggplot')
fig1, ax1 = plt.subplots(figsize=(10, 6))

# Plot the lines
line_grown, = ax1.plot(x_values_stock, sim.grown_cow_amount_series, label="Grown Cows (Age > 12 months)", color='blue')
line_calf, = ax1.plot(x_values_stock, sim.carf_amount_series, label="Calves (Age < 12 months)", color='red')
line_total, = ax1.plot(x_values_stock, sim.total_cattle_series, label="Total Cattle", color='black', linestyle='--')
line_pregnant, = ax1.plot(x_values_stock, sim.cow_amount_pregnant_series, label="Pregnant Cows", color='green', linestyle=':')

# --- Apply Markers to Lines ---

months = params["Simulation months"]
# X-values for stock series (Month 0 to N)
x_values_stock = range(months + 1)
# X-values for flow series (Month 1 to N)
x_values_flow = range(1, months + 1)

# Identify months where key events occurred (starting from month 1)
deaths_months = [i + 1 for i, count in enumerate(sim.death_series) if count > 0]
sold_months = [i + 1 for i, count in enumerate(sim.sold_series) if count > 0]
purchased_months = [i + 1 for i, count in enumerate(sim.cows_purchased_series) if count > 0]
birth_months = [i + 1 for i, count in enumerate(sim.births_series) if count > 0]

# --- Marker Placement Helper Function ---
def plot_markers(ax, month, stock_value, count, marker_type, color, annotation_prefix, x_offset, y_offset, zorder=5):
    """Plots a marker and annotation at the given stock value."""
    ax.scatter(month, stock_value, marker=marker_type, s=50 + 20*count, color=color, zorder=zorder)
    ax.annotate(f'{annotation_prefix}{count}', (month, stock_value), 
                textcoords="offset points", 
                xytext=(x_offset, y_offset), 
                ha='center', fontsize=8, color=color)

# 1. Deaths (affecting all stock lines)
for month in deaths_months:
    count = sim.death_series[month - 1]
    
    # Mark Total Cattle line (most visible)
    y_val_total = sim.total_cattle_series[month]
    plot_markers(ax1, month, y_val_total, count, 'D', 'red', 'D', -15, 5)

# 2. Sales (mostly grown cows, but can be calves too)
for month in sold_months:
    count = sim.sold_series[month - 1]
    
    # Mark Total Cattle line
    y_val_total = sim.total_cattle_series[month]
    plot_markers(ax1, month, y_val_total, count, 's', 'orange', 'S', 0, 15)
    
# 3. Purchases (grown cows only in this model)
for month in purchased_months:
    count = sim.cows_purchased_series[month - 1]
    
    # Mark Grown Cows line
    y_val_grown = sim.cow_amount_pregnant_series[month]
    plot_markers(ax1, month, y_val_grown, count, 'P', 'blue', 'P', 15, 5)

# 4. Births
for month in birth_months:
    count = sim.births_series[month - 1]
    
    # Mark Grown Cows line
    y_val_grown = sim.carf_amount_series[month]
    plot_markers(ax1, month, y_val_grown, count, 'P', 'green', 'P', 15, 5)

ax1.set_title("Herd Composition Over Time with Events", fontsize=16)
ax1.set_xlabel("Month", fontsize=12)
ax1.set_ylabel("Number of Animals", fontsize=12)

# Create custom legend handles for markers
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='blue', lw=2, label='Grown Cows'),
    Line2D([0], [0], color='red', lw=2, label='Calves'),
    Line2D([0], [0], color='black', lw=2, linestyle='--', label='Total Cattle'),
    Line2D([0], [0], color='green', lw=2, linestyle=':', label='Pregnant Cows'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor='red', markersize=8, label='Death Event'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='orange', markersize=8, label='Sale Event'),
    Line2D([0], [0], marker='P', color='w', markerfacecolor='blue', markersize=8, label='Purchase Event'),
    Line2D([0], [0], marker='P', color='w', markerfacecolor='green', markersize=8, label='Birth Event')
]
ax1.legend(handles=legend_elements, loc='upper right', ncol=2, title="Legend and Events")

ax1.grid(True)
plt.tight_layout()
plt.savefig("herd_composition_plot_with_markers.png")

# ------------------ Plotting Group 2: Financial Comparison ------------------
fig2, ax_left = plt.subplots(figsize=(10, 6))
ax_right = ax_left.twinx()

# Plot 1: Cumulative Cashflow (Left Axis)
ax_left.plot(x_values_stock, cumulative_cashflow, label="Cumulative Cashflow", color='darkorange', linewidth=2)
ax_left.set_ylabel(r"Cumulative Cashflow ($\$$)", fontsize=12, color='darkorange')
ax_left.tick_params(axis='y', labelcolor='darkorange')

# Plot 2: Total Net Worth (Right Axis)
ax_right.plot(x_values_stock, net_worth_series, label="Total Net Worth", color='blue', linewidth=2)
ax_right.set_ylabel(r"Total Net Worth ($\$$)", fontsize=12, color='blue')
ax_right.tick_params(axis='y', labelcolor='blue')

# Plot 3: Herd Value (Difference) (Right Axis)
ax_right.plot(x_values_stock, herd_value_series, label="Herd Value (Net Worth - Cashflow)", color='green', linestyle='--')

# Title and Labels
ax_left.set_title("Total Net Worth vs. Cumulative Cashflow", fontsize=16)
ax_left.set_xlabel("Month", fontsize=12)

# Combine legends
lines = ax_left.get_lines() + ax_right.get_lines()
labels = [l.get_label() for l in lines]
ax_left.legend(lines, labels, loc='upper left')

ax_left.grid(True)
plt.tight_layout()
plt.savefig("financial_comparison_plot.png")


# Cumulative Cashflow (starts at month 0 with initial cash)
initial_cash = sim.initial_cash
cumulative_cashflow = np.cumsum([initial_cash] + sim.cashflow).tolist()

# Define the series for plotting and their properties
all_series = [
    (sim.grown_cow_amount_series, "Grown Cow Amount (stock)", "Number of Cows"),
    (sim.carf_amount_series, "Calf Amount (stock)", "Number of Calves"),
    (sim.total_cattle_series, "Total Cattle (stock)", "Number of Cattle"),
    (sim.cow_amount_pregnant_series, "Pregnant Cow Amount (stock)", "Number of Pregnant Cows"),
    (sim.net_worth_series, "Total Net Worth (stock)", r"Currency ($\$$)"),
    (cumulative_cashflow, "Cumulative Cashflow (stock)", r"Currency ($\$$)"),
    (sim.births_series, "Monthly Births (flow)", r"Number of Births"),
    (sim.death_series, "Monthly Deaths (flow)", r"Number of Deaths"),
    (sim.sold_series, "Monthly Sold (flow)", r"Number of Sold Cows"),
    (sim.cows_purchased_series, "Cows Purchased (flow)", r"Number of Cows"),
    (sim.revenue_series, "Monthly Revenue (flow)", r"Currency ($\$$)"),
    (sim.cost_series, "Monthly Costs (flow)", r"Currency ($\$$)"),
    (sim.cashflow, "Monthly Cashflow (flow)", r"Currency ($\$$)"),
    (sim.alquiler_series, "Alquiler (flow)", r"Alquiler (calves)"),
]

num_plots = len(all_series)

plt.style.use('ggplot')
fig, axes = plt.subplots(nrows=num_plots, ncols=1, figsize=(10, 3 * num_plots), sharex=False)

# Identify months where key events occurred (starting from month 1)
# Flow series are 1-indexed (Month 1 to N). Stock series are 0-indexed (Month 0 to N).
# To plot a marker at month t, we use index t for stock series (y-value is at the end of month t).
deaths_months = [i + 1 for i, count in enumerate(sim.death_series) if count > 0]
sold_months = [i + 1 for i, count in enumerate(sim.sold_series) if count > 0]
purchased_months = [i + 1 for i, count in enumerate(sim.cows_purchased_series) if count > 0]


for i, ax in enumerate(axes):
    data, title, ylabel = all_series[i]
    
    # Determine x-axis values
    is_stock_series = title.endswith("(stock)")
    if is_stock_series:
        x_values = range(sim.p["Simulation months"] + 1) # Month 0 to N
    else:
        x_values = range(1, sim.p["Simulation months"] + 1) # Month 1 to N

    ax.plot(x_values, data, label=title)
    
    # --- Marker Logic: Only apply markers to Stock Series ---
    if is_stock_series:
        
        # Plot deaths markers 'D'
        for month in deaths_months:
            # y-value is the stock level at the END of the month the event occurred
            y_val = data[month] 
            count = sim.death_series[month - 1] # Count from the flow series
            
            # Using Total Cattle Stock for simplicity, but markers can go on any stock plot.
            # Adjust y-position slightly to avoid overlap if needed.
            ax.scatter(month, y_val, marker='D', s=50 + 20*count, color='red', zorder=5, 
                       label=f'Death ({count} cows)' if month == deaths_months[0] else None)
            # Annotate the marker with the count
            ax.annotate(f'{count}', (month, y_val), textcoords="offset points", xytext=(-5, 5), ha='right', fontsize=8, color='red')

        # Plot sold markers 'S'
        for month in sold_months:
            y_val = data[month]
            count = sim.sold_series[month - 1]
            ax.scatter(month, y_val, marker='s', s=50 + 20*count, color='orange', zorder=5, 
                       label=f'Sold ({count} cows)' if month == sold_months[0] else None)
            ax.annotate(f'{count}', (month, y_val), textcoords="offset points", xytext=(5, 5), ha='left', fontsize=8, color='orange')
            
        # Plot purchased markers 'P'
        for month in purchased_months:
            y_val = data[month]
            count = sim.cows_purchased_series[month - 1]
            ax.scatter(month, y_val, marker='P', s=50 + 20*count, color='blue', zorder=5, 
                       label=f'Purchase ({count} cows)' if month == purchased_months[0] else None)
            ax.annotate(f'{count}', (month, y_val), textcoords="offset points", xytext=(5, -15), ha='left', fontsize=8, color='blue')


    ax.set_title(title, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True)
    ax.tick_params(axis='x', rotation=45)

# Add a combined legend to the first plot to explain the markers
# We need to collect handles/labels carefully, but for this specific request, 
# we'll rely on the marker annotations and colors for clarity.

# Set the x-label for the very last subplot only
axes[-1].set_xlabel("Month", fontsize=12)

plt.tight_layout()
plt.savefig("herd_simulation_series_with_event_markers.png")

print("The plotting code has been updated to include event markers on the stock charts:")
print("- 'D' (Red square) for **Deaths**")
print("- 'S' (Orange square) for **Sales**")
print("- 'P' (Blue square) for **Purchases**")
print("The size of the marker and the annotation indicate the number of cows involved in that event.")