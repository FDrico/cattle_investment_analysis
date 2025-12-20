params = {
    'starting_month': 2, # enero
    'initial_capital': 0, 
    'initial_cows': 4, 
    'initial_toros': 2,
    'initial_cows_months_pregnant': 1,
    'initial_cows_age': 24,
    'buffer': 500,
    'bull_buy_month': 36, # won't buy bull up until this amount of months
    'bull_buy_age': 24,
    
    'price_vaca_invernada': 1200,
    'price_vaca_ternero_al_pie': 1800,
    'price_vaca_preniada': 1400,
    'price_novillo': 700,
    'price_vaquillona': 700,
    'price_ternero_macho': 500,
    'price_ternero_hembra': 550,
    'price_ternero_huerfano': 700,
    'price_toro': 3000,
    'price_carne_vaca': 950,
    'price_carne_toro': 1400,

    'edad_minima_venta': 7,
    'edad_maxima_ternero': 7,
    'edad_minima_toro': 2*12,
    'landowner_split': 0.5,
    'edad_maxima_toro': 6*12,
    
    'baseline_sale_prob': 0.01, # i won't go around selling my cows in general
    'probabilidad_venta_ternero': 0.01, # i won't go around selling my calves in general
    'probabilidad_venta_tenero_huerfano': 0.40, # i want to sell it asap as it will die anyway
    'probabilidad_venta_novillo': 0.60, 
    'probabilidad_venta_vaquillona': 0.60,
    'probabilidad_venta_vaca_invernada': 0.01,
    'probabilidad_venta_vaca_preniada': 0.005,
    'probabilidad_venta_toro': 0.60,
    'probabilidad_venta_carne': 0.60, # to sell as meat
    'probabilidad_venta_vaca_con_ternero': 0.01,

    'cull_check_month': 4, # april
    'min_age_to_sell': 7,

    'drought_start': 48, # dought!
    'drought_end': 60,
    'drought_pregnancy_prob_reduction': 0.2, #20% of the chances of getting pregnant than if not in a drought
    'drought_mortality_increase': 2, #twice as many deaths than if not in a drought
    'orphan_mortality_increase': 2, #twice as many deaths than if not in a drought
    'drought_market_price_reduction': 0.7,

    'base_mortality': 0.002,
    'offspring_mortality_rate': 0.08/12, # Según CONICET, se muere un ~8% de las crias en el primer año.
    "life expectancy": 14, # edad aproximada de vida de una vaca,
    "prime_age_end_months": 12*9, # A los 9 años ya no están para tener crias, y tienen alta probabilidad de morir
    'prob_abortion': 0.01,

    'gestation length': 9,
    'Min months between pregnancies': 3,
    'Minimum age for getting pregnant': 18, # Vacas necesitan tener 18 meses de edad antes de embarazarse
    'Monthly pregnancy probability': 0.55, # probabilidad de que una vaca se embarace en un mes, luego de los 3 meses.
    'min_bull_percentage': 0.04,
    'probability_female': 0.5,

    'cost_health_per_animal_per_year': 20,
    'life_expectancy': 14*12,

    'months_to_simulate': 12*7
}