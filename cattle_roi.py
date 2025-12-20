import random
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np
from parametros import parameters as params
from matplotlib.lines import Line2D


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
        self.net_worth_series = []
        
        # Granular flow tracking
        self.grown_cow_deaths_series = []
        self.calf_deaths_series = []
        self.grown_cow_sales_series = []
        self.calf_sales_series = []
        
        self.initial_cash = -params["Initial cows"] * params["Purchase price per cow"]
        self.cumulative_cash = 0
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

        # Initial cow setup
        initial_herd_value = 0
        purchase_age = params["Minimum age for getting pregnant"] + params["Months into pregnancy"]
        
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
        
        self.net_worth_series.append(self.cumulative_cash + initial_herd_value) 
        self.total_cattle_series[0] = self.grown_cow_amount_series[0] + self.carf_amount_series[0]

    def monthly_mortality(self, cow):
        if cow.age < 12:
            return self.p["Offspring mortality rate"]
        
        life_months_base = self.p["Life expectancy"] * 12
        base_mortality = 1 / life_months_base

        if cow.age <= self.p["Prime age end (months)"]:
            return base_mortality
        else:
            age_over_prime = cow.age - self.p["Prime age end (months)"]
            scaling_factor = 20
            increased_mortality = base_mortality * np.exp(age_over_prime / scaling_factor)
            return min(increased_mortality, 0.5)

    def get_sell_probability(self, cow):
        sell_prob = 0
        is_calf = cow.age < 12
        is_old = cow.age >= self.p["Cull age probability threshold (months)"]
        
        # Scenario 1: High probability sales after the holding period (calves)
        if is_calf and self.time >= self.p["Minimum time before selling anything (months)"] and cow.age >= self.p["Min calf sell age (months)"]:
            
            if self.time < 3 * 12:
                sell_prob = self.p["High calves probability (monthly)"]
            else:
                sell_prob = self.p["Medium calves probability (monthly)"]

        # Scenario 2: High cull probability for old cows
        elif is_old:
            sell_prob = self.p["High cull probability (monthly)"]
        
        # Scenario 3: Default low probability for others (or default sell age)
        elif self.time >= self.p["Minimum time before selling anything (months)"]:
             sell_prob = self.p["Sell probability (monthly)"] 

        return sell_prob

    def step(self):
        self.time +=1
        births = []
        deaths = 0
        calf_deaths = 0
        grown_cow_deaths = 0
        revenue = 0
        costs = 0
        sold = 0
        calf_sales = 0
        grown_cow_sales = 0
        alquiler = 0
        
        start_of_month_cash = self.cumulative_cash 

        # PHASE 1: Age, Mortality, Pregnancy, and Costs (excluding purchases)
        for cow in list(self.cows):
            if not cow.alive:
                continue

            cow.age += 1
            cow.months_since_last_birth += 1
            
            is_calf = cow.age < 12

            # Mortality
            if random.random() < self.monthly_mortality(cow):
                cow.alive = False
                deaths += 1
                if is_calf: 
                    calf_deaths += 1
                else:
                    grown_cow_deaths += 1
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

            # Maintenance Costs
            if cow.owned:
                costs += self.p["Vaccines & registration per cow per year"] / 12


        # PHASE 2: Sales/Culling 
        for cow in list(self.cows):
            sell_prob = self.get_sell_probability(cow)
            
            if (
                cow.alive
                and cow.owned
                and random.random() < sell_prob
            ):
                cow.alive = False
                sold += 1
                
                is_calf_on_sale = cow.age < 12
                
                if is_calf_on_sale: 
                    calf_sales += 1
                    revenue += self.p["Offspring sale price"]
                else: 
                    grown_cow_sales += 1
                    if cow.age >= self.p["Cull age probability threshold (months)"]:
                        revenue += self.p["Cull price per cow"]
                    else:
                        revenue += self.p["Purchase price per cow"]

        # PHASE 3: Births 
        for mother in births:
            calf = Cow(age=0, owned=True)
            self.cows.append(calf)
        
        # Apply Net Cash Flow BEFORE Reinvestment
        net_before_reinvestment = revenue - costs
        self.cumulative_cash += net_before_reinvestment
        
        # --- REINVESTMENT LOGIC (STRICT 100% REINVESTMENT) ---
        purchase_price = self.p["Purchase price per cow"]
        buffer = self.p["Reinvestment minimum cash buffer"]
        purchase_cost_incurred = 0
        purchased = 0
        
        while self.cumulative_cash >= (purchase_price + buffer):
            num_to_buy = 1
            purchased += num_to_buy
            
            new_cow = Cow(
                age=self.p["Minimum age for getting pregnant"] + self.p["Months into pregnancy"],
                pregnant=True,
                months_pregnant=self.p["Months into pregnancy"],
            )
            self.cows.append(new_cow)
            
            self.cumulative_cash -= purchase_price
            purchase_cost_incurred += purchase_price
            
        total_costs_in_series = costs + purchase_cost_incurred
        total_revenue_in_series = revenue
        final_net_cashflow = self.cumulative_cash - start_of_month_cash


        # PHASE 4: Final Stock Recalculation and Series Append
        
        self.cows = [c for c in self.cows if c.alive] 
        owned_alive_cows = [c for c in self.cows if c.owned]

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
        net_worth = self.cumulative_cash + herd_value

        # --- Append Series (Using granular and updated flow values) ---
        self.cashflow.append(final_net_cashflow)
        self.revenue_series.append(total_revenue_in_series) 
        self.cost_series.append(total_costs_in_series) 
        
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
        
        # NEW Granular Flow Series
        self.calf_deaths_series.append(calf_deaths)
        self.grown_cow_deaths_series.append(grown_cow_deaths)
        self.calf_sales_series.append(calf_sales)
        self.grown_cow_sales_series.append(grown_cow_sales)
        
        # Net Worth Series
        self.net_worth_series.append(net_worth)

    def run(self):
        for _ in range(self.p["Simulation months"]):
            self.step()

        return self.net_worth_series[-1]

# ------------------ Run ------------------
sim = HerdSimulation(params)
sim.run()

# ------------------ Plotting Function Implementation ------------------

# Prepare Data for Plotting
months = params["Simulation months"]
x_values_stock = range(months + 1)
x_values_flow = range(1, months + 1)

cumulative_cashflow = np.cumsum([sim.initial_cash] + sim.cashflow).tolist()
net_worth_series = sim.net_worth_series

# --- Marker Placement Helper Function ---
def plot_markers_with_annotation(ax, month, stock_value, count, marker_type, color, event_prefix, x_offset, y_offset, zorder=5):
    """Plots a marker and annotation (e.g., 'D2') at the given stock value."""
    if count > 0:
        ax.scatter(month, stock_value, marker=marker_type, s=50 + 20*count, color=color, zorder=zorder)
        annotation_text = f'{event_prefix}{count}' 
        ax.annotate(annotation_text, (month, stock_value), 
                    textcoords="offset points", 
                    xytext=(x_offset, y_offset), 
                    ha='center', fontsize=8, color=color, weight='bold')

def plot_figures(sim, params, use_markers):
    
    plt.style.use('ggplot')
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(20, 20), sharex=True)
    
    # ==============================================================================
    # SUBPLOT 1: Herd Composition (Stock Tracking and Granular Events)
    # ==============================================================================
    ax1.set_title(f"Herd Composition Over Time (Offspring Mortality: {params['Offspring mortality rate']*100:.2f}%)", fontsize=16)

    # Plot the lines
    grown_cows_line, = ax1.plot(x_values_stock, sim.grown_cow_amount_series, label="Grown Cows (Age $\\geq$ 12 months)", color='blue', linewidth=2)
    calves_line, = ax1.plot(x_values_stock, sim.carf_amount_series, label="Calves (Age $<$ 12 months)", color='red', linewidth=2)
    total_line, = ax1.plot(x_values_stock, sim.total_cattle_series, label="Total Cattle", color='black', linestyle='--', linewidth=1)
    pregnant_line, = ax1.plot(x_values_stock, sim.cow_amount_pregnant_series, label="Pregnant Cows", color='green', linestyle=':', linewidth=1)
    
    if use_markers:
        # 1. Purchases (P) (on Grown Cows line)
        for month in x_values_flow:
            count = sim.cows_purchased_series[month - 1]
            y_val_grown = sim.grown_cow_amount_series[month]
            plot_markers_with_annotation(ax1, month, y_val_grown, count, 'P', 'blue', 'P', -15, -15)

        # 2. Sales (S) (GRANULAR)
        for month in x_values_flow:
            # Calves Sales (on Calves line)
            count_calf = sim.calf_sales_series[month - 1] 
            if count_calf > 0: 
                y_val_calf = sim.carf_amount_series[month]
                plot_markers_with_annotation(ax1, month, y_val_calf, count_calf, 's', 'orange', 'SC', 0, 15) 
                
            # Grown Cow Sales (on Grown Cows line)
            count_grown = sim.grown_cow_sales_series[month - 1] 
            if count_grown > 0: 
                y_val_grown = sim.grown_cow_amount_series[month]
                plot_markers_with_annotation(ax1, month, y_val_grown, count_grown, 's', 'darkgoldenrod', 'SG', 0, 15)

        # 3. Deaths (D) (GRANULAR)
        for month in x_values_flow:
            # Calf Deaths (on Calves line)
            count_calf = sim.calf_deaths_series[month - 1]
            if count_calf > 0:
                y_val_calf = sim.carf_amount_series[month] 
                plot_markers_with_annotation(ax1, month, y_val_calf, count_calf, 'D', 'red', 'DC', 15, -15)
                
            # Grown Cow Deaths (on Grown Cows line)
            count_grown = sim.grown_cow_deaths_series[month - 1]
            if count_grown > 0:
                y_val_grown = sim.grown_cow_amount_series[month] 
                plot_markers_with_annotation(ax1, month, y_val_grown, count_grown, 'D', 'darkred', 'DG', 15, -15)

        # 4. Births (B) (on Calves line)
        for month in x_values_flow:
            count = sim.births_series[month - 1]
            y_val_calf = sim.carf_amount_series[month]
            plot_markers_with_annotation(ax1, month, y_val_calf, count, '^', 'green', 'B', -5, -5)
                
        # 5. Alquiler (A) (on Calves line)
        for month in x_values_flow:
            count = sim.alquiler_series[month - 1]
            if count > 0:
                y_val_calf = sim.carf_amount_series[month]
                plot_markers_with_annotation(ax1, month, y_val_calf, count, 'x', 'purple', 'A', 15, 15)

        # Create Dummy Plots for Marker Legend (Stock Plot)
        legend_handles = ax1.get_lines() 
        legend_labels = [l.get_label() for l in legend_handles]
        
        GRANULAR_MARKERS = [
            ('P', 'blue', 'New Cow Purchase (P)'),
            ('s', 'orange', 'Sale Calf (SC)'),
            ('s', 'darkgoldenrod', 'Sale Grown Cow (SG)'),
            ('D', 'red', 'Death Calf (DC)'),
            ('D', 'darkred', 'Death Grown Cow (DG)'),
            ('^', 'green', 'Births (B)'),
            ('x', 'purple', 'Alquiler/Rent (A)')
        ]

        for marker, color, label in GRANULAR_MARKERS:
            dummy_scatter = ax1.scatter([], [], marker=marker, s=50, color=color, label=label)
            legend_handles.append(dummy_scatter)
            legend_labels.append(label)

        final_handles = []
        final_labels = []
        seen_labels = set()
        for h, l in zip(legend_handles, legend_labels):
            if l not in seen_labels:
                final_handles.append(h)
                final_labels.append(l)
                seen_labels.add(l)
        
        ax1.legend(final_handles, final_labels, loc='upper left', ncol=2, fontsize=8)

    else:
        ax1.legend(loc='upper left', ncol=2, fontsize=8)


    ax1.set_ylabel("Number of Animals", fontsize=12)
    ax1.grid(True)


    # ==============================================================================
    # SUBPLOT 2: Financial Comparison (Stock and Events)
    # ==============================================================================
    ax2.set_title(f"Financial Over Time (Strict 100% Reinvestment, Buffer: $\$$500)", fontsize=16)

    # Plot Cashflow (Left Axis)
    cashflow_line, = ax2.plot(x_values_stock, cumulative_cashflow, label="Cumulative Cashflow", color='darkorange', linewidth=2)
    ax2.set_ylabel(r"Cumulative Cashflow ($\$$)", fontsize=12, color='darkorange')
    ax2.tick_params(axis='y', labelcolor='darkorange')

    # Right Axis for Net Worth
    ax_right = ax2.twinx()
    networth_line, = ax_right.plot(x_values_stock, net_worth_series, label="Total Net Worth", color='blue', linewidth=2)
    ax_right.set_ylabel(r"Total Net Worth ($\$$)", fontsize=12, color='blue')
    ax_right.tick_params(axis='y', labelcolor='blue')

    if use_markers:
        # 1. Total Sales (S) (using total sales on Cashflow line)
        for month in x_values_flow:
            count = sim.sold_series[month - 1] 
            y_val = cumulative_cashflow[month]
            plot_markers_with_annotation(ax2, month, y_val, count, 's', 'orange', 'S', 10, 5) 
            
        # 2. Purchases (P)
        for month in x_values_flow:
            count = sim.cows_purchased_series[month - 1]
            y_val = cumulative_cashflow[month]
            plot_markers_with_annotation(ax2, month, y_val, count, 'P', 'blue', 'P', -10, 5) 


        # Create Dummy Plots for Marker Legend (Financial Plot)
        financial_lines = [cashflow_line, networth_line]
        financial_labels = [l.get_label() for l in financial_lines]
        
        financial_markers = [
            ax2.scatter([], [], marker='s', s=50, color='orange', label='Total Sales (S)'),
            ax2.scatter([], [], marker='P', s=50, color='blue', label='Purchases (P)')
        ]
        financial_lines.extend(financial_markers)
        financial_labels.extend([l.get_label() for l in financial_markers])

        ax2.legend(financial_lines, financial_labels, loc='upper left', fontsize=8)

    else:
        lines = ax2.get_lines() + ax_right.get_lines()
        labels = [l.get_label() for l in lines]
        ax2.legend(lines, labels, loc='upper left', fontsize=8)

    ax2.set_xlabel("Month", fontsize=12)
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig("combined_herd_financial_plots_strict_reinvestment_granular.png")

# --- Execute Plotting ---
plot_figures(sim, params, True)