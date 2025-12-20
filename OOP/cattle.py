import random
import matplotlib.pyplot as plt
import numpy as np
from params import params
import matplotlib.lines as mlines

class Animal:
    def __init__(self, age, ranch, mother=None, is_sellable=True):
        self.age = age
        self.ranch = ranch
        self.alive = True
        self.mortality_modifier = 1
        self.preg_chance = params['Monthly pregnancy probability']
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
        self.preg_chance = params['drought_pregnancy_prob_reduction'] * params['Monthly pregnancy probability']
        self.mortality_modifier = params['drought_mortality_increase']
        self.market_reduction = params['drought_market_price_reduction']

    def disaffect_by_drought(self):
        self.preg_chance = params['Monthly pregnancy probability']
        self.mortality_modifier = 1
        self.market_reduction = 1

    def become_orphan(self):
        self.is_orphan = True
        self.splittable_with_land_owner = True
        self.mortality_modifier = self.mortality_modifier*params['orphan_mortality_increase']
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
                       'terneros_huerfanos': self.ranch.p['price_ternero_huerfano'],
                       'carne': self.ranch.p['price_carne_vaca']
                       }
        self.probabilities_of_being_sold = {'vacas_pregnant': self.ranch.p['probabilidad_venta_vaca_preniada'],
                       'vacas_con_ternero': self.ranch.p['probabilidad_venta_vaca_con_ternero'],
                       'vacas_fertiles': self.ranch.p['probabilidad_venta_vaca_invernada'],
                       'terneros': self.ranch.p['probabilidad_venta_ternero'],
                       'vaquillonas': self.ranch.p['probabilidad_venta_vaquillona'],
                       'terneros_huerfanos': self.ranch.p['probabilidad_venta_tenero_huerfano'],
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
            self.abort()
            return "abortion"
        
        if self.months_pregnant >= self.ranch.p['gestation length']:
            self.give_birth()
            return "birth"
        
        return None

    def process_reproduction(self):
        if not self.alive or self.is_pregnant or self.age < self.ranch.p['Minimum age for getting pregnant']: return None
        if self.months_since_last_birth < self.ranch.p['Min months between pregnancies']: return None
        if self.ranch.month_of_year not in [12, 1, 2]: return None
        if self.ranch.amount_toros <= 0: return None

        if random.random() < self.preg_chance:
            self.get_pregnant()
            return "pregnancy"                

        return None

    def become_vaquillona(self):
        # remove mortality modifier do to being an orphan child
        if self.is_orphan:
            self.mortality_modifier = self.mortality_modifier/params['orphan_mortality_increase']
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
        if self.ranch.month_of_year != params['cull_check_month']: return
        if self.is_pregnant: return
        if not self.is_old_enough_to_get_pregnant: return
        # Has not been pregnant for 12 months, not fertile
                
        self.category = 'carne'
        self.pending_cull = True
           
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
                       'carne': self.ranch.p['price_carne_toro']
                       }
        self.probabilities_of_being_sold = {'toros': self.ranch.p['probabilidad_venta_toro'],
                       'novillos': self.ranch.p['probabilidad_venta_novillo'],
                       'terneros': self.ranch.p['probabilidad_venta_ternero'],
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

    def age_one_month(self):
        self.age +=1 
        if self.age == self.ranch.p['min_age_to_sell']:
            self.become_novillo()
        if self.age == self.ranch.p['edad_minima_toro']:
            self.become_toro()
    
    def process_mortality(self):
        # Mortality logic encapsulated within the object
        if random.random() < self._monthly_mortality():
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
        self.special_events = ['births', 'pregnancy']
        self.event_types = ['deaths', 'sales', 'purchases']
        self.categories = ['vacas_fertiles', 'vacas_pregnant', 'terneros', 'toros', 'novillos', 'vaquillonas', 'vacas_con_ternero', 'carne']
        self.flow_series = [f"{item}" for item in ['cash', 'worth', 'valor_rebanio', 'sales', 'purchases', 'pregnancy']]
        self.month = params['starting_month']
        self.cash = params['initial_capital'] 
        self.bulls = []
        self.cows = []
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
        self.landowner_split = params['landowner_split']

        # Initial Cow setup, with pregnant cows
        for _ in range(params['initial_cows']):
            self.cows.append(Female(age=self.p['initial_cows_age'],
                                    ranch=self,
                                    mother=None,
                                    is_pregnant=True,
                                    months_pregnant=self.p['initial_cows_months_pregnant']))
        for _ in range(params['initial_toros']):
            self.bulls.append(Male(age=self.p['initial_cows_age'],
                                   ranch=self,
                                   mother=None,
                                   is_sellable=False)) # not mine to sell

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
                events['purchases_toros'] += 1
    

    def sell_animal(self, animal):
        mkt_mod = self.p['drought_market_price_reduction'] if self.in_drought else 1
        # young animals only

        if animal.category == 'toros':
            if self.amount_toros < self.p['min_bull_percentage']*self.amount_animals:
                return None, None, None

        if animal.is_old_enough_to_be_sold or animal.is_orphan: # TODO: check that when the mother dies, the child does NOT die.
            if random.random() < animal.probability_of_being_sold:
                split_with_landowner = self.landowner_split if animal.splittable_with_land_owner else 1
                net = animal.price * mkt_mod * split_with_landowner # Landowner split
                if animal.is_recent_mother:
                    self.cash += net - (net / 2) * self.landowner_split # pago por el tenero solamente (por eso /2).
                    animal.calf_id.die() # El ternero se vende con la madre por el precio de los dos
                animal.die()
                reason = 'market'
                return 'sold', net, reason
        
        # old animals
        elif animal.pending_cull:
            if random.random() < animal.probability_of_being_sold:
                net = animal.price * mkt_mod
                self.cash += net
                animal.die()
                reason = 'cull'
                return 'sold', net, reason

        return None, None, None
    
    @property
    def is_time_of_year_to_buy_pregnant_cows(self):
        return (6 <= self.month_of_year <= 9)

    def re_invest_earnings(self, events):
        # if drought, market price reduction
        mkt_mod = self.p['drought_market_price_reduction'] if self.in_drought else 1

        if self.is_time_of_year_to_buy_pregnant_cows:
            # Stochastic Age: 24 to 36 months
            random_age = random.randint(24, 36)
            # Stochastic Pregnancy: 3 to 6 months
            random_preg_month = random.randint(3, 6)
            while self.cash >= self.p['price_vaca_preniada'] * mkt_mod + self.p['buffer']:
                new_cow = Female(age=random_age,
                                        ranch=self,
                                        mother=None,
                                        is_pregnant=True,
                                        months_pregnant=random_preg_month)

                self.new_cow(new_cow)
                self.cash -= self.p['price_vaca_preniada'] * mkt_mod
                events[f'purchases_{new_cow.category}'] += 1
    
    def get_plot_category(self, animal):
        return animal.category

    def run_month(self):
        if self.p['drought_start'] == self.month:
            self.start_drought()
        
        elif self.p['drought_end'] == self.month:
            self.stop_drought()

        events = {f"{et}_{cat}": 0 for et in ['deaths', 'sales', 'purchases'] for cat in self.categories}
        events['births'] = 0
        events['pregnancy'] = 0


        # 1. Bull Acquisition Logic
        self.buy_bull_if_needed(events)

        # 2. Animal Lifecycle (The OOP heart)
        for animal in list(self.herd):
            if not animal.alive: continue
            cat = self.get_plot_category(animal)

            # aging
            animal.age_one_month()

            # gestation
            gestation_result = animal.process_gestation()
            if "birth" == gestation_result:
                events['births'] += 1
            
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


            # 3. Selling Logic (Rules-based)
            # Sell young and old stock
            sale_result = self.sell_animal(animal)
            if 'sold' == sale_result[0]:
                events[f'sales_{cat}'] += 1
                events[f'deaths_{cat}'] += 1
                self.cash += sale_result[1]

        # Vaccinate animals
        vaccine_cost = len([a for a in self.herd if a.alive]) * (self.p['cost_health_per_animal_per_year']/12)
        self.cash -= vaccine_cost

        # Re-investment (Buying pregnant cows)
        self.re_invest_earnings(events)

        # 5. Financial Summary
        
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
        #h_val = (len(fertile_cows)*self.p['price_vaca_invernada'] + \
        #         len(pregnant_cows)*self.p['price_vaca_preniada'] + \
        #         len(terneros)*self.p['price_ternero_macho'] + \
        #         len(toros)*self.p['price_toro'] + \
        #         len(novillos)*self.p['price_novillo'] + \
        #         len(vaquillonas)*self.p['price_vaquillona'])
        
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
        


    def plot(self):

        start_month = self.p['starting_month']
        m = np.arange(len(self.history['cash'])) + start_month
        fig, axes = plt.subplots(4, 1, figsize=(12, 24), sharex=True)
        plt.subplots_adjust(hspace=0.3)

        # Configuración de Marcadores
        marker_map = {
            'births': ('cyan', 'o', 'Nacimiento'),
            'deaths': ('red', 'x', 'Muerte'),
            'sales': ('gold', 's', 'Venta'),
            'purchases': ('purple', '^', 'Compra')
        }
        marker_proxies = [mlines.Line2D([], [], color=c, marker=m, linestyle='None', label=l) 
                        for _, (c, m, l) in marker_map.items()]

        def format_month(m):
            months_es = ['E','F','M','A','M','J','J','A','S','O','N','D']
            year = (m - 1) // 12 + 1
            month = (m - 1) % 12
            return f"{months_es[month]}{2025 + year - 1}"
        
        def overlay_markers(ax, x_axis, y_series, category_key, is_financial=False):
            for event_type, (color, marker, _) in marker_map.items():
                # Lógica para encontrar el key correcto en el historial
                if is_financial:
                    # En finanzas, mostramos si hubo CUALQUIER evento de ese tipo
                    combined_events = np.zeros(len(x_axis))
                    for cat in self.categories:
                        key = f"{event_type}_{cat}" if event_type != 'births' else 'births'
                        if key in self.history:
                            combined_events += np.array(self.history[key])
                    idx = np.where(combined_events > 0)[0]
                else:
                    # En stock, solo marcamos si el evento pertenece a esa categoría
                    key = f"{event_type}_{category_key}" if event_type != 'births' else 'births'
                    if event_type == 'births' and category_key != 'terneros': continue
                    
                    if key in self.history:
                        ev_data = np.array(self.history[key])
                        idx = np.where(ev_data > 0)[0]
                    else: idx = []

                if len(idx) > 0:
                    ax.scatter(x_axis[idx], np.array(y_series)[idx], 
                               color=color, marker=marker, s=45, zorder=10)

        # --- PANEL 0: FINANZAS ---
        ax = axes[0]
        ax.plot(m, self.history['worth'], label='Total Net Worth', color='blue', linewidth=2)
        ax.plot(m, self.history['cash'], label='Cumulative Cashflow', color='black', alpha=0.7, linestyle='--')
        ax.plot(m, self.history['valor_rebanio'], label='Total Herd Value', color='green', alpha=0.5)
        
        # Ponemos marcadores en la línea de Worth para muertes/nacimientos 
        # y en Cash para compras/ventas
        overlay_markers(ax, m, self.history['worth'], None, is_financial=True)
        ax.set_title("Desempeño Financiero (Net Worth, Cash & Herd Value)", fontsize=14)

        # --- PANEL 1: ADULTOS ---
        ax = axes[1]
        ax.plot(m, self.history['vacas_fertiles'], label='Vacas Fértiles', color='tab:blue')
        ax.plot(m, self.history['vacas_pregnant'], label='Vacas Preñadas', color='tab:red')
        ax.plot(m, self.history['toros'], label='Toros', color='brown', linewidth=2)
        
        overlay_markers(ax, m, self.history['vacas_fertiles'], 'vacas_fertiles')
        overlay_markers(ax, m, self.history['vacas_pregnant'], 'vacas_pregnant')
        overlay_markers(ax, m, self.history['toros'], 'toros')
        ax.set_title("Stock de Adultos (Vacas y Toros)", fontsize=14)

        # --- PANEL 2: JUVENILES ---
        ax = axes[2]
        ax.plot(m, self.history['vaquillonas'], label='Vaquillonas', color='tab:orange')
        ax.plot(m, self.history['novillos'], label='Novillos', color='darkgreen')
        
        overlay_markers(ax, m, self.history['vaquillonas'], 'vaquillonas')
        overlay_markers(ax, m, self.history['novillos'], 'novillos')
        ax.set_title("Stock de Juveniles (Reposición y Engorde)", fontsize=14)

        # --- PANEL 3: TERNEROS ---
        ax = axes[3]
        ax.plot(m, self.history['terneros'], label='Terneros (Cualquier sexo)', color='tab:cyan', linewidth=2)
        
        overlay_markers(ax, m, self.history['terneros'], 'terneros')
        ax.set_title("Stock de Terneros (Nacimientos)", fontsize=14)

        # Formateo General
        for i, ax in enumerate(axes):
            handles, labels = ax.get_legend_handles_labels()
            # Añadimos la leyenda de marcadores solo si no es el gráfico financiero para no saturar,
            # o en todos si prefieres consistencia:
            ax.legend(handles=handles + marker_proxies, loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
            
            # Resaltar sequía
            ax.axvspan(self.p['drought_start'], self.p['drought_end'], color='red', alpha=0.05, label='Sequía')
            ax.grid(True, alpha=0.2)
            ax.set_ylabel("Cantidad / Valor")
            ax.set_xticks(m[::3])
            ax.set_xticklabels([format_month(x) for x in m[::3]])


        axes[-1].set_xlabel(f"Meses (Inicio en {start_month})")
        plt.tight_layout()
        plt.show()

# Execution
from params import params

ranch = Ranch(params)
for _ in range(params['months_to_simulate']):
    ranch.run_month()

ranch.plot()