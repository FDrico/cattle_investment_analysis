import random
import matplotlib.pyplot as plt
import numpy as np
from params import params
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

class Animal:
    def __init__(self, age, ranch, mother=None, is_sellable=True):
        self.age = age
        self.ranch = ranch
        self.alive = True
        self.mortality_modifier = 1
        self.preg_chance = self.ranch.p['Monthly pregnancy probability']
        self.market_reduction = 1
        self.mother = mother
        self.is_orphan = False
        self.pending_cull = False
        self.splittable_with_land_owner = False
        self.is_sellable = is_sellable

    @property
    def is_recent_mother(self):
        return False
    
    def age_one_month(self):
        pass
    
    def process_mortality(self):
        pass

    def process_gestation(self):
        pass

    def process_reproduction(self):
        pass

    def process_cull(self):
        pass
    
    def die(self):
        self.alive = False
        # if the dead is a mother, the calf is likely to die until he is 7
        self.increase_child_mortality_due_to_orphanity()

        # if the dead is a calf, the mother needs to stop tracking the child
        if self.mother:
            self.mother.remove_child()

        # and the child has to stop tracking the mother
        self.mother = None

    def increase_child_mortality_due_to_orphanity(self):
        # applied only to mothers
        pass
    
    def _monthly_mortality(self):        
        if self.age < 12:
            # Winter mortality check (Jun, Jul, Aug)
            if self.ranch.is_winter:
                return self.ranch.p["offspring_mortality_rate"] * self.mortality_modifier * self.ranch.p['winter_mortality_increase']
            
            return self.ranch.p["offspring_mortality_rate"]*self.mortality_modifier
        
        life_months_base = self.ranch.p["life_expectancy"] * 12
        base_mortality = 1 / life_months_base / 5

        if self.age <= self.ranch.p["prime_age_end_months"]:
            return base_mortality*self.mortality_modifier
        else:
            age_over_prime = self.age - self.ranch.p["prime_age_end_months"]
            scaling_factor = 20
            increased_mortality = base_mortality * np.exp(age_over_prime / scaling_factor) * self.mortality_modifier
            return increased_mortality
        
    def affect_by_drought(self):
        self.preg_chance = self.ranch.p['drought_pregnancy_prob_reduction'] * self.ranch.p['Monthly pregnancy probability']
        self.mortality_modifier = self.ranch.p['drought_mortality_increase']
        self.market_reduction = self.ranch.p['drought_market_price_reduction']

    def disaffect_by_drought(self):
        self.preg_chance = self.ranch.p['Monthly pregnancy probability']
        self.mortality_modifier = 1
        self.market_reduction = 1

    def become_orphan(self):
        self.is_orphan = True
        self.splittable_with_land_owner = True
        self.mortality_modifier = self.mortality_modifier*self.ranch.p['orphan_mortality_increase']
        self.category = 'ternero_huerfano'

    def process_reproduction(self):
        pass
    
    def check_if_cull_due_to_age(self):
        pass

    @property
    def is_old_enough_to_be_sold(self):
        if self.age < self.ranch.p['min_age_to_sell']:
            return False
        return True
    
class Female(Animal):
    def __init__(self, age, ranch, mother, is_pregnant=False, months_pregnant=0, is_sellable=True):
        super().__init__(age=age, ranch=ranch, mother=mother, is_sellable=is_sellable)
        self.is_pregnant = is_pregnant
        self.months_pregnant = months_pregnant
        self.months_since_last_birth = 99
        self.pending_cull = False
        self.calf_id = None # Tracks her current nursing calf
        if age > self.ranch.p['edad_maxima_ternero']:
            self.splittable_with_land_owner = False
        
        self.prices = {'vacas_pregnant': self.ranch.p['price_vaca_preniada'],
                       'vacas_con_ternero': self.ranch.p['price_vaca_ternero_al_pie'],
                       'vacas_fertiles': self.ranch.p['price_vaca_invernada'],
                       'terneros': self.ranch.p['price_ternero_hembra'],
                       'vaquillonas': self.ranch.p['price_vaquillona'],
                       'ternero_huerfano': self.ranch.p['price_ternero_huerfano'],
                       'carne': self.ranch.p['price_carne_vaca']
                       }
        self.probabilities_of_being_sold = {'vacas_pregnant': self.ranch.p['probabilidad_venta_vaca_preniada'],
                       'vacas_con_ternero': self.ranch.p['probabilidad_venta_vaca_con_ternero'],
                       'vacas_fertiles': self.ranch.p['probabilidad_venta_vaca_invernada'],
                       'terneros': self.ranch.p['probabilidad_venta_ternero'],
                       'vaquillonas': self.ranch.p['probabilidad_venta_vaquillona'],
                       'ternero_huerfano': self.ranch.p['probabilidad_venta_tenero_huerfano'],
                       'carne': self.ranch.p['probabilidad_venta_carne']
                       }

        if is_pregnant:
            self.category = 'vacas_pregnant'
        elif age > self.ranch.p['edad_maxima_ternero']:
            if self.months_since_last_birth < 99:
                if self.months_since_last_birth < self.ranch.p['edad_maxima_ternero'] and self.calf_id:
                    self.category = 'vacas_con_ternero'
                else:
                    self.category = 'vacas_fertiles'
            else:
                self.category = 'vaquillonas'
        else:
            self.category = 'terneros'

    @property
    def price(self):
        return self.prices[self.category]*self.market_reduction
    
    @property
    def probability_of_being_sold(self):
        if not self.is_sellable: return 0
        return self.probabilities_of_being_sold[self.category]

    def remove_child(self):
        self.calf_id = None
        self.category = 'vacas_fertiles'
    
    def increase_child_mortality_due_to_orphanity(self):
        if self.calf_id:
            self.calf_id.become_orphan()

    def age_one_month(self):
        self.age += 1
        self.months_since_last_birth += 1
        # The calf is now a grown cow, no need for parental tracking
        if self.age == self.ranch.p['edad_maxima_ternero']:
            self.become_vaquillona()
    
    def process_mortality(self):
        if not self.alive: return None

        # Mortality logic encapsulated within the object
        if random.random() < self._monthly_mortality():
            self.ranch._log_event(f"A {self.category} (age {self.age}) died of natural causes.")
            self.die()
            return "death"
    
    def process_culling(self):
        # Culling due to aging
        self.check_if_cull_due_to_age()
        return None
    
    def process_gestation(self):
        if not self.alive or not self.is_pregnant: return None
        
        self.months_pregnant += 1
        # Abortion
        if random.random() < self.ranch.p.get('prob_abortion', 0.005):
            self.ranch._log_event(f"Abortion of a cow with {self.months_pregnant} months of pregnancy.")
            self.abort()
            return "abortion"
        
        if self.months_pregnant >= self.ranch.p['gestation length']:
            self.ranch._log_event(f"A cow is giving birth.")
            self.give_birth()
            return "birth"
        
        return None

    def process_reproduction(self):
        if not self.alive or self.is_pregnant or self.age < self.ranch.p['Minimum age for getting pregnant']: return None
        if self.months_since_last_birth < self.ranch.p['Min months between pregnancies']: return None
        if self.ranch.month_of_year not in [12, 1, 2]: return None
        if self.ranch.amount_toros <= 0: return None

        if random.random() < self.preg_chance:
            self.ranch._log_event(f"A cow (age {self.age}) became pregnant.")
            self.get_pregnant()
            return "pregnancy"                

        return None

    def become_vaquillona(self):
        # remove mortality modifier do to being an orphan child
        if self.is_orphan:
            self.mortality_modifier = self.mortality_modifier/self.ranch.p['orphan_mortality_increase']
            self.is_orphan = False
        else:
            self.mother.remove_child()
            self.mother = None
        self.splittable_with_land_owner = True
        self.category = 'vaquillonas'

    def give_birth(self):
        self.is_pregnant = False
        self.months_pregnant = 0
        self.months_since_last_birth = 0
        self.category = 'vacas_con_ternero'
        # New calf
        if random.random() < self.ranch.p['probability_female']:
            self.calf_id = Female(age=0, ranch=self.ranch, mother=self)
            self.ranch.new_cow(self.calf_id)
        else: #TODO: consider different price for male calf !
            self.calf_id = Male(age=0, ranch=self.ranch, mother=self)
            self.ranch.new_bull(self.calf_id)

    def abort(self):
        self.is_pregnant = False
        self.months_pregnant = 0
        self.months_since_last_birth = 0
        self.category = 'vacas_fertiles'

    def get_pregnant(self):
        self.is_pregnant = True
        self.category = 'vacas_pregnant'
        self.months_pregnant = 0
        self.splittable_with_land_owner = False
        # note: the price does not change up to month 3
    
    

    def check_if_cull_due_to_age(self):
        if self.pending_cull: return# already decided
        if self.months_since_last_birth < 12: return
        if self.ranch.month_of_year != self.ranch.p['cull_check_month']: return
        if self.is_pregnant: return
        if not self.is_old_enough_to_get_pregnant: return
        # Has not been pregnant for 12 months, not fertile
                
        self.category = 'carne'
        self.pending_cull = True
        self.ranch._log_event(f"A cow (age {self.age}) marked for culling due to infertility.")
           
    @property
    def is_old_enough_to_be_sold(self):
        if self.age < 7:
            return False
        # The 6-month weaning rule
        if self.pending_cull and not self.is_old_enough_to_get_pregnant:
            return False
        return True
    
    @property
    def is_recent_mother(self):
        if self.calf_id:
            return True
        return False

    @property
    def is_old_enough_to_get_pregnant(self):
        if self.age >= self.ranch.p['Minimum age for getting pregnant']:
            return True
        return False
    

class Male(Animal):
    def __init__(self, age, ranch, mother, is_pregnant=False, months_pregnant=0, is_sellable=True):
        super().__init__(age=age, ranch=ranch, mother=mother, is_sellable=is_sellable)
        self.sex = 'M'
            
        self.prices = {'toros': self.ranch.p['price_toro'],
                       'novillos': self.ranch.p['price_novillo'],
                       'terneros': self.ranch.p['price_ternero_macho'],
                       'ternero_huerfano': self.ranch.p['price_ternero_huerfano'],
                       'carne': self.ranch.p['price_carne_toro']
                       }
        self.probabilities_of_being_sold = {'toros': self.ranch.p['probabilidad_venta_toro'],
                       'novillos': self.ranch.p['probabilidad_venta_novillo'],
                       'terneros': self.ranch.p['probabilidad_venta_ternero'],
                       'ternero_huerfano': self.ranch.p['probabilidad_venta_tenero_huerfano'],
                       'carne': self.ranch.p['probabilidad_venta_carne']
                       }
        
        if age >= self.ranch.p['edad_minima_toro']:
            self.category = 'toros'
        elif age <= self.ranch.p['edad_maxima_ternero']:
            self.category = 'terneros'
            self.splittable_with_land_owner = False
        else:
            self.category = 'novillos'
    
    @property
    def price(self):
        if not self.is_sellable: return 0
        return self.prices[self.category]*self.market_reduction
    
    @property
    def probability_of_being_sold(self):
        if not self.is_sellable: return 0
        return self.probabilities_of_being_sold[self.category]
    
    def check_if_cull_due_to_age(self):
        if self.age > self.ranch.p['edad_maxima_toro']:
            self.pending_cull = True
            self.category = 'carne'
            self.ranch._log_event(f"A bull (age {self.age}) marked for culling due to old age.")

    def age_one_month(self):
        self.age +=1 
        if self.age == self.ranch.p['min_age_to_sell']:
            self.become_novillo()
        if self.age == self.ranch.p['edad_minima_toro']:
            self.become_toro()
    
    def process_mortality(self):
        # Mortality logic encapsulated within the object
        if random.random() < self._monthly_mortality():
            self.ranch._log_event(f"A {self.category} (age {self.age}) died of natural causes.")
            self.die()
            return "death"
    
    def process_culling(self):
        # Culling due to aging
        self.check_if_cull_due_to_age()
        return None
    
    def become_novillo(self):
        self.category = 'novillos'
        self.splittable_with_land_owner = True

    def become_toro(self):
        self.category = 'toros'
        self.splittable_with_land_owner = False

    @property
    def is_toro(self):
        return (self.category == 'toros')
    
    @property
    def is_novillo(self):
        return (self.category == 'novillos')

class Ranch:
    def __init__(self, params):
        self.p = params
        self.special_events = ['births', 'pregnancy', 'abortion']
        self.event_types = ['deaths', 'sales', 'purchases']
        self.categories = ['vacas_fertiles', 'vacas_pregnant', 'terneros', 'toros', 'novillos', 'vaquillonas', 'vacas_con_ternero', 'carne', 'ternero_huerfano']
        self.flow_series = [f"{item}" for item in ['cash', 'worth', 'valor_rebanio', 'sales', 'purchases', 'pregnancy']]
        self.month = params['starting_month']
        self.cash = params['initial_capital'] 
        self.bulls = []
        self.cows = []
        self.log = []
        self.history = {}

        for et in self.event_types:
            for cat in self.categories:
                self.history[f"{et}_{cat}"] = []
        for item in self.flow_series:
            self.history[item] = []
        for cat in self.categories:
            self.history[f"{cat}"] = []
        for special_event in self.special_events:
            self.history[f"{special_event}"] = []
        
        self.in_drought = False
        self.landowner_split = self.p['landowner_split']

        # Initial Cow setup, with pregnant cows
        for _ in range(self.p['initial_cows']):
            cow = Female(age=self.p['initial_cows_age'], ranch=self, mother=None)
            self._initialize_pregnancy(cow)
            self.cows.append(cow)
            
        for _ in range(self.p['initial_toros']):
            self.bulls.append(Male(age=self.p['initial_cows_age'],
                                   ranch=self,
                                   mother=None,
                                   is_sellable=False)) # not mine to sell

    def _format_month_for_log(self, m):
        months_es = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
        start_year = self.p.get('starting_year', 2025)
        # The year calculation needs to account for the starting month not being January
        total_months_from_origin = m - 1 
        year = start_year + (total_months_from_origin // 12)
        month_idx = total_months_from_origin % 12
        return f"{months_es[month_idx]}-{year}"

    def _log_event(self, event_text):
        date_str = self._format_month_for_log(self.month)
        log_entry = f"{date_str} - Month {self.month} - {event_text}"
        self.log.append(log_entry)

    def _initialize_pregnancy(self, cow):
        # Guarantee pregnancy as the cow is bought as "pregnant" (palpation confirmed)
        cow.get_pregnant()
        
        current_moy = self.month_of_year
        mating_months = [12, 1, 2]
        
        # Calculate possible months pregnant based on fixed mating season
        possible_months = [(current_moy - m) % 12 for m in mating_months]
        
        # Filter for valid pregnancy months (must be > 0 and < gestation length)
        valid_months = [m for m in possible_months if 0 < m < self.p['gestation length']]
        
        if valid_months:
            cow.months_pregnant = random.choice(valid_months)

    def start_drought(self):
        self.in_drought = True
        for animal in self.herd:
            animal.affect_by_drought()

    def stop_drought(self):
        self.in_drought = False
        for animal in self.herd:
            animal.disaffect_by_drought()
        
    def new_cow(self, cow):
        if self.in_drought: cow.affect_by_drought()
        self.cows.append(cow)
    
    def new_bull(self, bull):
        if self.in_drought: bull.affect_by_drought()
        self.bulls.append(bull)

    @property
    def month_of_year(self):
        return ((self.month - 1) % 12) + 1
    
    @property
    def is_winter(self):
        # Assuming Southern Hemisphere winter (June, July, August)
        return self.month_of_year in [6, 7, 8]

    @property
    def herd(self):
        return self.cows + self.bulls
    
    @property
    def amount_toros(self):
        return len([a for a in self.bulls if (a.alive and a.is_toro)])
    
    @property
    def amount_animals(self):
        return len([a for a in self.herd if a.alive])
    
    @property
    def amount_grown_animals(self):
        return len([a.age >= 18 for a in self.herd if a.alive])

    def buy_bull_if_needed(self, events):
        if self.month < self.p['bull_buy_month']: return
        
        if self.amount_toros < self.p['min_bull_percentage']*self.amount_animals: # we need a bull
            # if in drought, reduce price
            mkt_mod = self.p['drought_market_price_reduction'] if self.in_drought else 1
            
            if self.cash >= self.p['price_toro']:
                new_bull = Male(age=self.p['bull_buy_age'],
                                ranch=self,
                                mother=None
                                )
                self.bulls.append(new_bull)
                self.cash -= self.p['price_toro']*mkt_mod
                self._log_event(f"Purchasing a new bull (age {self.p['bull_buy_age']}).")
                events['purchases_toros'] += 1
    
    def check_sale_eligibility(self, animal):
        # young animals only
        mkt_mod = self.p['drought_market_price_reduction'] if self.in_drought else 1

        if animal.category == 'toros':
            if self.amount_toros < self.p['min_bull_percentage']*self.amount_animals:
                return False

        if animal.is_old_enough_to_be_sold or animal.is_orphan: # TODO: check that when the mother dies, the child does NOT die.
            return True
        
        # old animals
        elif animal.pending_cull:
                return True

        return False

    def process_batch_sales(self, candidates, events):
        mkt_mod = self.p['drought_market_price_reduction'] if self.in_drought else 1
        # Liquidity modifier: during drought, it's harder to find buyers
        liquidity_mod = self.p.get('drought_sales_chance_reduction', 0.5) if self.in_drought else 1
        
        for category, animals in candidates.items():
            # Shuffle to ensure random selection for batches
            random.shuffle(animals)
            
            # Determine probability of selling this category (using the first animal as reference)
            # If no animals, loop won't start anyway.
            base_prob = animals[0].probability_of_being_sold if animals else 0
            sale_probability = base_prob * liquidity_mod
            
            # Use category-specific minimum batch size if available, else default
            min_batch_size = self.p.get(f'batch_size_min_{category}', self.p['batch_size_min'])

            while len(animals) >= min_batch_size:
                # Determine batch size (between min and max, or whatever is left if less than max)
                batch_size = random.randint(min_batch_size, self.p['batch_size_max'])
                if batch_size > len(animals):
                    batch_size = len(animals)
                
                # Market Opportunity Check: Roll for the batch, not the individual
                if random.random() > sale_probability:
                    # Failed to find a buyer for this batch
                    if self.in_drought and base_prob > 0.1: # Only log significant failures (e.g. steers, not random cows)
                        self._log_event(f"Failed to find a buyer for a batch of {category} (Drought Liquidity).")
                    break

                self._log_event(f"Selling a batch of {batch_size} {category}.")
                # Extract batch
                batch = animals[:batch_size]
                animals = animals[batch_size:]
                
                # Calculate Financials
                batch_gross_value = 0
                
                for animal in batch:
                    split_with_landowner = self.landowner_split if animal.splittable_with_land_owner else 1
                    price = animal.price * mkt_mod * split_with_landowner
                    
                    # Special logic for cow with calf
                    if animal.is_recent_mother:
                        # Logic from original code: adjust for calf split
                        price = price - (price / 2) * self.landowner_split
                        animal.calf_id.die()
                        
                    batch_gross_value += price
                    animal.die()
                    events[f'sales_{category}'] += 1
                    events[f'deaths_{category}'] += 1

                # Apply Transaction Costs
                batch_net_value = batch_gross_value * (1 - self.p['auction_fee']) - self.p['logistics_cost']
                self.cash += batch_net_value
    
    @property
    def is_time_of_year_to_buy_pregnant_cows(self):
        return (6 <= self.month_of_year <= 9)

    def re_invest_earnings(self, events):
        # if drought, market price reduction
        mkt_mod = self.p['drought_market_price_reduction'] if self.in_drought else 1

        if self.is_time_of_year_to_buy_pregnant_cows:
            # Stochastic Age: 24 to 36 months
            random_age = random.randint(24, 36)          
            # Buy in batches
            while True:
                batch_size = random.randint(self.p['batch_size_min'], self.p['batch_size_max'])
                unit_price = self.p['price_vaca_preniada'] * mkt_mod
                
                total_cost = (unit_price * batch_size) * (1 + self.p['auction_fee']) + self.p['logistics_cost']
                
                if self.cash >= total_cost + self.p['buffer']:
                    self._log_event(f"Purchasing a batch of {batch_size} pregnant cows.")
                    for _ in range(batch_size):
                        new_cow = Female(age=random_age,
                                                ranch=self,
                                                mother=None)
                        self._initialize_pregnancy(new_cow)
                        self.new_cow(new_cow)
                        events[f'purchases_{new_cow.category}'] += 1
                    
                    self.cash -= total_cost
                else:
                    break
    
    def get_plot_category(self, animal):
        return animal.category

    def run_month(self):
        if self.p['drought_start'] == self.month:
            self.start_drought()
        
        elif self.p['drought_end'] == self.month:
            self.stop_drought()

        if self.month_of_year == 12: # Start of mating season
            ready_to_mate = [
                a for a in self.cows if a.alive and 
                not a.is_pregnant and 
                a.age >= self.p['Minimum age for getting pregnant'] and 
                a.months_since_last_birth >= self.p['Min months between pregnancies']
            ]
            self._log_event(f"Mating season started: {len(ready_to_mate)} cows are eligible for mating.")

        events = {f"{et}_{cat}": 0 for et in ['deaths', 'sales', 'purchases'] for cat in self.categories}
        events['births'] = 0
        events['pregnancy'] = 0
        events['abortion'] = 0


        # Bull Acquisition Logic
        self.buy_bull_if_needed(events)

        sales_candidates = {} # Dictionary to hold lists of animals per category

        # Animal Lifecycle
        for animal in list(self.herd):
            if not animal.alive: continue
            cat = self.get_plot_category(animal)

            # aging
            animal.age_one_month()

            # gestation
            gestation_result = animal.process_gestation()
            if "birth" == gestation_result:
                events['births'] += 1
            elif "abortion" == gestation_result:
                events['abortion'] += 1
            
            # Reproduction
            rep_result = animal.process_reproduction()
            if "pregnancy" == rep_result:
                events['pregnancy'] += 1

            # mortality
            mortality_result = animal.process_mortality()
            if "death" == mortality_result:
                events[f'deaths_{cat}'] += 1

            # culling
            animal.process_culling()

            # Check for sale eligibility (but don't sell yet)
            if animal.alive and self.check_sale_eligibility(animal):
                if cat not in sales_candidates:
                    sales_candidates[cat] = []
                sales_candidates[cat].append(animal)

        # Process sales in batches
        self.process_batch_sales(sales_candidates, events)
        
        # Vaccinate animals
        vaccine_cost = len([a for a in self.herd if a.alive]) * (self.p['cost_health_per_animal_per_year']/12)
        self.cash -= vaccine_cost

        # Re-investment
        self.re_invest_earnings(events)

        if self.month_of_year == 2: # End of mating season
            pregnant_cows = len([a for a in self.cows if a.alive and a.is_pregnant])
            fertile_cows = len([a for a in self.cows if a.alive and not a.is_pregnant and a.is_old_enough_to_get_pregnant])
            self._log_event(f"Mating season finished. Current state: {pregnant_cows} pregnant, {fertile_cows} fertile (empty).")

        # Financial Summary
        
        self._record_history(events)
        self.month += 1

    def _record_history(self, events):
        fertile_cows = [a for a in self.cows if (a.alive and a.is_old_enough_to_get_pregnant and not a.is_pregnant)]
        pregnant_cows = [a for a in self.cows if (a.alive and a.is_pregnant)]
        terneros = [a for a in self.herd if (a.alive and not a.is_old_enough_to_be_sold)]
        toros = [a for a in self.bulls if a.alive and a.is_toro]
        vaquillonas = [a for a in self.cows if (a.alive and not a.is_old_enough_to_get_pregnant and a.is_old_enough_to_be_sold)]
        novillos = [a for a in self.bulls if a.alive and a.is_novillo]

        cl = [a for a in self.herd if a.alive and a.age < 12]
        
        h_val = sum([a.price for a in self.herd])
        
        self.history['cash'].append(self.cash)
        self.history['worth'].append(self.cash + h_val)
        self.history['valor_rebanio'].append(h_val)

        self.history['vacas_fertiles'].append(len(fertile_cows))
        self.history['vacas_pregnant'].append(len(pregnant_cows))
        self.history['terneros'].append(len(terneros))
        self.history['toros'].append(len(toros))
        self.history['novillos'].append(len(novillos))
        self.history['vaquillonas'].append(len(vaquillonas))

        for evkey, evvalue in events.items():
            self.history[evkey].append(evvalue)
        
    def write_log(self, filename="simulation_log.txt"):
        """Writes the simulation event log to a text file."""
        with open(filename, "w") as f:
            for entry in self.log:
                f.write(entry + "\n")


    def plot(self):

        start_month = self.p['starting_month']
        m = np.arange(len(self.history['cash'])) + start_month
        fig, axes = plt.subplots(4, 1, figsize=(15, 20), sharex=True)
        plt.subplots_adjust(hspace=0.5)
        secondary_axes = {}

        # Configuración de Marcadores
        marker_map = {
            'births': ('cyan', 'o', 'Nacimiento'),
            'deaths': ('red', 'x', 'Muerte'),
            'sales': ('gold', 's', 'Venta'),
            'purchases': ('purple', '^', 'Compra'),
            'abortion': ('black', 'v', 'Aborto')
        }
        marker_proxies = [mlines.Line2D([], [], color=c, marker=m, linestyle='None', label=l) 
                        for _, (c, m, l) in marker_map.items()]

        # Add Legend entries for Stages and Purchases
        marker_proxies.append(mpatches.Patch(facecolor='pink', alpha=0.2, label='Servicio (Mating)'))
        marker_proxies.append(mpatches.Patch(facecolor='lightgreen', alpha=0.2, label='Parición (Calving)'))
        marker_proxies.append(mlines.Line2D([], [], color='purple', linestyle='--', label='Compra (Batch)'))

        def format_month(m):
            months_es = ['E','F','M','A','M','J','J','A','S','O','N','D']
            year = (m - 1) // 12 + 1
            month = (m - 1) % 12
            year_str = str(2025 + year - 1)[-2:]
            return f"{months_es[month]}{year_str}"
        
        def overlay_markers(ax, x_axis, y_series, category_input, is_financial=False):
            # Normalize input to list to handle single categories or aggregates (like Total Adults)
            categories = [category_input] if isinstance(category_input, str) else category_input

            for event_type, (color, marker, _) in marker_map.items():
                counts = np.zeros(len(x_axis))
                
                if is_financial:
                    if event_type in ['births', 'pregnancy', 'abortion']:
                        if event_type in self.history:
                            counts = np.array(self.history[event_type])
                    else:
                        for cat in self.categories:
                            key = f"{event_type}_{cat}"
                            if key in self.history:
                                counts += np.array(self.history[key])
                else:
                    if event_type == 'births':
                        if any(c in ['terneros', 'vacas_pregnant', 'vacas_fertiles'] for c in categories):
                            counts = np.array(self.history['births'])
                    elif event_type == 'abortion':
                        if any(c == 'vacas_pregnant' for c in categories):
                            counts = np.array(self.history['abortion'])
                    elif event_type not in ['pregnancy']:
                        for cat in categories:
                            key = f"{event_type}_{cat}"
                            if key in self.history:
                                counts += np.array(self.history[key])
                            
                            # Aggregate vacas_con_ternero events into vacas_fertiles as they are plotted together
                            if cat == 'vacas_fertiles':
                                key_extra = f"{event_type}_vacas_con_ternero"
                                if key_extra in self.history:
                                    counts += np.array(self.history[key_extra])

                idx = np.where(counts > 0)[0]
                if len(idx) > 0:
                    ax.scatter(x_axis[idx], np.array(y_series)[idx], 
                               color=color, marker=marker, s=45, zorder=10)
                    for i in idx:
                        ax.text(x_axis[i], np.array(y_series)[i], str(int(counts[i])), 
                                color=color, fontsize=9, fontweight='bold', ha='right', va='bottom')

        # Helper to highlight stages and buying events
        def highlight_stages_and_buys(ax):
            # 1. Stages (Mating & Calving)
            for x_val in m:
                moy = ((x_val - 1) % 12) + 1
                if moy in [12, 1, 2]: # Mating Season
                    ax.axvspan(x_val - 0.5, x_val + 0.5, color='pink', alpha=0.2, lw=0, zorder=0)
                elif moy in [9, 10, 11]: # Calving Season (approx 9 months later)
                    ax.axvspan(x_val - 0.5, x_val + 0.5, color='lightgreen', alpha=0.2, lw=0, zorder=0)
            
            # 2. Buying Events (Vertical Lines)
            purchases_in_month = np.zeros_like(m)
            for cat in self.categories:
                key = f"purchases_{cat}"
                if key in self.history:
                    purchases_in_month += np.array(self.history[key])
            
            purchase_indices = np.where(purchases_in_month > 0)[0]
            for idx in purchase_indices:
                ax.axvline(x=m[idx], color='purple', linestyle='--', alpha=0.6, linewidth=1.5, zorder=1)


        # --- PANEL 0: FINANZAS ---
        ax = axes[0]
        ax.plot(m, self.history['worth'], label='Total Net Worth', color='blue', linewidth=2)
        ax.plot(m, self.history['valor_rebanio'], label='Total Herd Value', color='green', alpha=0.5)
        
        ax0_right = ax.twinx()
        secondary_axes[0] = ax0_right
        ax0_right.plot(m, self.history['cash'], label='Cumulative Cashflow', color='black', alpha=0.7, linestyle='--')
        ax0_right.set_ylabel("Cashflow ($)")
        
        # Ponemos marcadores en la línea de Worth para muertes/nacimientos 
        # y en Cash para compras/ventas
        overlay_markers(ax, m, self.history['worth'], None, is_financial=True)
        highlight_stages_and_buys(ax)
        ax.set_title("Desempeño Financiero (Net Worth, Cash & Herd Value)", fontsize=14)

        # --- PANEL 1: ADULTOS ---
        ax = axes[1]
        ax.plot(m, self.history['vacas_fertiles'], label='Vacas Fértiles', color='tab:blue')
        ax.plot(m, self.history['vacas_pregnant'], label='Vacas Preñadas', color='tab:red')
        ax.plot(m, self.history['toros'], label='Toros', color='brown', linewidth=2)
        
        # Calculate and plot Total Adults
        total_adults = np.array(self.history['vacas_fertiles']) + np.array(self.history['vacas_pregnant']) + np.array(self.history['toros'])
        ax.plot(m, total_adults, label='Total Adultos', color='black', linestyle=':', linewidth=2, alpha=0.7)
        overlay_markers(ax, m, total_adults, ['vacas_fertiles', 'vacas_pregnant', 'toros'])
        
        # Right Axis: Total Herd (Grown or not)
        ax1_right = ax.twinx()
        secondary_axes[1] = ax1_right
        total_herd = (np.array(self.history['vacas_fertiles']) + np.array(self.history['vacas_pregnant']) + 
                      np.array(self.history['toros']) + np.array(self.history['vaquillonas']) + 
                      np.array(self.history['novillos']) + np.array(self.history['terneros']))
        ax1_right.plot(m, total_herd, label='Total Hacienda (All)', color='gray', linestyle='--', alpha=0.3)
        ax1_right.set_ylabel("Total Hacienda")

        overlay_markers(ax, m, self.history['vacas_fertiles'], 'vacas_fertiles')
        overlay_markers(ax, m, self.history['vacas_pregnant'], 'vacas_pregnant')
        overlay_markers(ax, m, self.history['toros'], 'toros')
        highlight_stages_and_buys(ax)
        ax.set_title("Stock de Adultos (Vacas y Toros)", fontsize=14)

        # --- PANEL 2: JUVENILES ---
        ax = axes[2]
        ax.plot(m, self.history['vaquillonas'], label='Vaquillonas', color='tab:orange')
        ax.plot(m, self.history['novillos'], label='Novillos', color='darkgreen')
        
        total_juveniles = np.array(self.history['vaquillonas']) + np.array(self.history['novillos'])
        ax.plot(m, total_juveniles, label='Total Juveniles', color='black', linestyle=':', linewidth=2)
        
        overlay_markers(ax, m, self.history['vaquillonas'], 'vaquillonas')
        overlay_markers(ax, m, self.history['novillos'], 'novillos')
        highlight_stages_and_buys(ax)
        ax.set_title("Stock de Juveniles (Reposición y Engorde)", fontsize=14)

        # --- PANEL 3: TERNEROS ---
        ax = axes[3]
        ax.plot(m, self.history['terneros'], label='Terneros (Cualquier sexo)', color='tab:cyan', linewidth=2)
        
        overlay_markers(ax, m, self.history['terneros'], 'terneros')
        highlight_stages_and_buys(ax)
        ax.set_title("Stock de Terneros (Nacimientos)", fontsize=14)

        # Formateo General
        for i, ax in enumerate(axes):
            handles, labels = ax.get_legend_handles_labels()
            
            if i in secondary_axes:
                h2, l2 = secondary_axes[i].get_legend_handles_labels()
                handles += h2
                labels += l2

            # Añadimos la leyenda de marcadores solo si no es el gráfico financiero para no saturar,
            # o en todos si prefieres consistencia:
            ax.legend(handles=handles + marker_proxies, loc='upper left', bbox_to_anchor=(1.15, 1), fontsize='small')
            
            # Resaltar sequía
            ax.axvspan(self.p['drought_start'], self.p['drought_end'], color='red', alpha=0.05, label='Sequía')
            ax.grid(True, alpha=0.2)
            ax.set_ylabel("Cantidad / Valor")
            ax.set_xticks(m[::3])
            ax.set_xticklabels([format_month(x) for x in m[::3]])


        axes[-1].set_xlabel(f"Meses (Inicio en {start_month})")
        #plt.tight_layout(rect=[0, 0, 0.82, 1])
        plt.tight_layout()
        plt.savefig("cattle_roi_plot.png", dpi=400)

# Execution
from params import params

ranch = Ranch(params)
for _ in range(params['months_to_simulate']):
    ranch.run_month()

ranch.plot()
ranch.write_log()