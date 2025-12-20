import random
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np
from parametros import parameters


# --- 1. HerdSimulation Class (V4: Age-Dependent Cull Probability) ---

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

        # Initial cow setup
        initial_herd_value = 0
        for _ in range(params["Initial cows"]):
            cow = Cow(
                age=params["Minimum age for getting pregnant"] + params["Months into pregnancy"],
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

    def step(self):
        self.time +=1
        births = []
        deaths = 0
        revenue = 0
        costs = 0
        sold = 0
        alquiler = 0
        purchased = 0

        for cow in list(self.cows): 
            if not cow.alive:
                continue

            cow.age += 1
            cow.months_since_last_birth += 1
            
            # Mortality (Death)
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

            # Costs
            if cow.owned:
                costs += self.p["Vaccines & registration per cow per year"] / 12

        # Handle births
        for mother in births:
            calf_owned = random.random()*100 > self.p["Offspring given to land owner (%)"]
            calf = Cow(age=0, owned=calf_owned)
            self.cows.append(calf)

            if not calf_owned:
                calf.alive = False  # alquiler
                alquiler += 1

        # Scheduled Purchase Logic
        if self.p["Scheduled purchase period (months)"] > 0 and \
           self.time % self.p["Scheduled purchase period (months)"] == 0:
            
            num_to_buy = self.p["Cows to buy per period"]
            purchased += num_to_buy
            costs += num_to_buy * self.p["Purchase price per cow"]

            for _ in range(num_to_buy):
                new_cow = Cow(
                    age=self.p["Minimum age for getting pregnant"] + self.p["Months into pregnancy"],
                    pregnant=True,
                    months_pregnant=self.p["Months into pregnancy"],
                )
                self.cows.append(new_cow)


        # Selling logic (Age-Dependent Cull Probability)
        for cow in list(self.cows):
            if not cow.alive or not cow.owned:
                continue

            # Determine the effective selling probability based on age
            current_sell_probability = self.p["Sell probability (monthly)"]
            
            if cow.age >= self.p["Cull age probability threshold (months)"]:
                # High probability for older, culling-eligible cows
                current_sell_probability = self.p["High cull probability (monthly)"]

            if (
                cow.age >= self.p["Sell age (months)"]
                and self.time >= self.p["Minimum time before selling anything (months)"]
                and random.random() < current_sell_probability
            ):
                cow.alive = False
                sold += 1
                if cow.age < 12:
                    revenue += self.p["Offspring sale price"]
                else:
                    # Use the Cull Price for mature cows sold
                    revenue += self.p["Cull price per cow"]

        net = revenue - costs
        self.cumulative_cash += net

        # --- Recalculate Stock Counts and Herd Value ---
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
        
        net_worth = self.cumulative_cash + herd_value

        # --- Append Series ---
        self.cashflow.append(net)
        self.revenue_series.append(revenue)
        self.cost_series.append(costs)
        
        self.grown_cow_amount_series.append(cow_amount)
        self.carf_amount_series.append(carf_amount)
        self.total_cattle_series.append(total_cattle)
        self.cow_amount_pregnant_series.append(pregnant_cows)
        
        self.death_series.append(deaths)
        self.sold_series.append(sold)
        self.births_series.append(len(births))
        self.alquiler_series.append(alquiler)
        self.cows_purchased_series.append(purchased)
        
        self.net_worth_series.append(net_worth)

    def run(self):
        for _ in range(self.p["Simulation months"]):
            self.step()

        return self.net_worth_series[-1]


# ------------------ Monte Carlo Analysis Script (V4: Age-Dependent Cull & 55% Pregnancy) ------------------

def run_monte_carlo(base_params, n_simulations, volatility_pct):
    final_net_worths = []
    
    # Base prices subject to volatility
    base_purchase_price = base_params["Purchase price per cow"]
    base_offspring_sale_price = base_params["Offspring sale price"]
    base_cull_price = base_params["Cull price per cow"]
    
    print(f"--- Starting Monte Carlo Simulation: {n_simulations} runs (V4) ---")
    print(f"Monthly Pregnancy Probability (Target): {base_params['Monthly pregnancy probability'] * 100:.0f}%")
    print(f"Cull Age Probability Threshold: {base_params['Cull age probability threshold (months)'] // 12} years")
    print(f"Cull Probability for Old Cows: {base_params['High cull probability (monthly)'] * 100:.0f}%\n")


    for i in range(n_simulations):
        # Create a copy of parameters for this run
        current_params = base_params.copy()
        
        # Calculate random volatility factor (e.g., between 0.95 and 1.05)
        volatility_factor = 1 + random.uniform(-volatility_pct, volatility_pct)
        
        # Apply volatility to prices (one-time adjustment per simulation)
        current_params["Purchase price per cow"] = base_purchase_price * volatility_factor
        current_params["Offspring sale price"] = base_offspring_sale_price * volatility_factor
        current_params["Cull price per cow"] = base_cull_price * volatility_factor

        sim = HerdSimulation(current_params)
        final_net_worth = sim.run()
        final_net_worths.append(final_net_worth)
        
        if (i + 1) % 500 == 0:
            print(f"Completed {i+1}/{n_simulations} simulations...")

    # --- Analysis ---
    final_net_worths = np.array(final_net_worths)
    SUCCESS_THRESHOLD = 0
    success_count = np.sum(final_net_worths > SUCCESS_THRESHOLD)
    success_probability = success_count / n_simulations
    mean_net_worth = np.mean(final_net_worths)
    std_net_worth = np.std(final_net_worths)

    # --- Results Plotting ---
    plt.figure(figsize=(10, 6))
    plt.hist(final_net_worths, bins=50, color='gold', edgecolor='black', alpha=0.7, label='Final Net Worth')
    plt.axvline(SUCCESS_THRESHOLD, color='red', linestyle='--', linewidth=2, label='Success Threshold (Net Worth = 0)')
    plt.title(f'Monte Carlo Simulation: Distribution of Final Net Worth ({n_simulations} Runs - V4)')
    plt.xlabel(r'Final Total Net Worth ($\$$)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True)
    plt.savefig("Monte_Carlo_Net_Worth_Distribution_V4_High_Pregnancy.png")

    # --- Output Results ---
    print("\n--- Monte Carlo Results (V4: High Pregnancy & Probabilistic Cull) ---")
    print(f"Probability of Good Investment (Net Worth > $0): {success_probability * 100:.2f}%")
    print(f"Mean Final Net Worth: ${mean_net_worth:,.2f}")
    print(f"Standard Deviation: ${std_net_worth:,.2f}")
    print("----------------------------------------------------------------------")


# Run the Monte Carlo Simulation with Volatility and Probabilistic Cull
run_monte_carlo(
    base_params=parameters,
    n_simulations=5000,
    volatility_pct=0.05 # +/- 5% annual price volatility
)