parameters = {
    # Initial Conditions
    "Initial cows": 15, # cantidad de vacas que compro
    "Months into pregnancy": 5, # Tiempo de gestación de las vacas
    "Amount of previous pregnancies": 2, # Cantidad de embarazos previos
    "Purchase price per cow": 1300, # Precio de compra
    "Cull price per cow": 1000, # Precio de cull (vaca vieja)
    
    # Reproduction
    "Gestation length": 9,
    "Min months between pregnancies": 3,
    "Minimum age for getting pregnant": 18, # Vacas necesitan tener 18 meses de edad antes de embarazarse
    "Monthly pregnancy probability": 0.50, # probabilidad de que una vaca se embarace en un mes, después de los 3 meses.

    # Finance/Transactions
    "Offspring sale price": 550, # Precio de venta de una cria
    "Vaccines & registration per cow per year": 20, # USD
    "Land owner take on calf sell": 0.5, # victor se queda con la mitad de la venta de terneros
    "Reinvestment minimum cash buffer": 200, # Don't buy a cow unless cash > (Price + Buffer)

    # Buy/sell options
    "Sell probability (monthly)": 0.05/12, # Espero vender sólo un 5% de las vacas en general
    "Cull age probability threshold (months)": 12 * 8, # A los 8 años empiezo a vender la vaca para carne. Ya no va a tener crias!
    "High cull probability (monthly)": 0.4, # Alta probabilidad de venta de vacas viejas: me las quiero sacar de encima
    "High calves probability (monthly)": 0.7, # Alta probabilidad de venta de terneros: No puedo mantenerlos por ahora
    "Medium calves probability (monthly)": 0.6, # Media probabilidad de venta de terneros, después del periodo de crecimiento del negocio
    "Min calf sell age (months)": 7,
    "Min years before holding calves": 3,

    "Minimum time before selling anything (months)": 0, # Los primeros 3 años, no se vende nada.

    # Mortality/Simulation
    "Offspring mortality rate": 0.08/12, # Según CONICET, se muere un ~8% de las crias en el primer año.
    "Life expectancy": 14, # edad aproximada de vida de una vaca
    "Prime age end (months)": 12*9, # A los 9 años ya no están para tener crias, y tienen alta probabilidad de morir
    "Simulation months": 12 * 3, # Run for 7 years
}

# 30 vacas, enero del 23. 2 terneros de 30 se murieron, quedaron 28. Vendió los 14 terneros y compró vaquillonas para entorar.
## las 30 vacas volvieron a parir. 
## De esas 30, tuvo que vender 1 que se enfermó. Se fue como conserva. Papera. 
# compró 23 vaquillonas con la plata de los terneros.
# para hacerlas madre, tenés que esperar 1 año y 8 meses
# en ponerse en celo. Minimo año y medio.
# luego compró 8 con 5 meses de gestación. 
# Son vacas que parieron 3 o 4 veces.
## No son más baratas. Es más seguro: La vaca nueva es más riesgosa. Es más probable que se muera el ternero.
# 60 vacas


# buscar la tabla de hacienda. Vacas de conserva, vacas de manufactura, vaca carnicera, vaca gorda. Hay una tabla.
# terneros, vaquillonas, novillos. Varían en los kgs.

# compró 8 vacas con 5 meses a pagar en 30 y 60 días.
# En otro remate, quiso comprar 6 vacas con terneros. Ahí espera hasta marzo y lo vende: "lo que pise", la saca a 950mil pesos/animal.
# En 3 meses vende el ternero, le saca plata, y le queda la vaca más barata.
# El tipo que te lo vende puede que no tenga pastura o necesite plata. Por eso le conviene.
# Vaquillona de 1º aparición con 3 meses de gestación.

# Solés ir vendiendo las vacas de conserva.
# las vacas más grnades tienen más probabilidad de parir.

# a victor se le murieron 4 vacas: tiene 48+55+11. 3 porque no pudieron parir: se les trabó el ternero.
# otra vaca parió y como el ternero era tan grande que se descaderó.
# el ternero se lo puso a una vaquillona que había perdido a su hijo. Entonces le pusieron el huérfano.

# A pablo se le murieron 4 d elas 29.

# gastos de sanidad: 2mil, 2 veces por año. Cesarea: 290mil pesos.
# 20usd.

# si compraba las 6 vacas con los terneros, podía pagarlos a 60 días.
# si pagaba 5% más, las pagabas a 120 días.

# 30 vacas, 19000 dolares
# hoy las 30 vacas valen 2millones de pesos servidas

# terneros tienen que estar 6 o 7 meses para venderlos.
# Pero a los 2 meses ya podés volver a servir. Eso siempre funciona?
## si no quedó preñada se vende como vaca seca.

# cada mes y medio está en celo.

# lista hubo aumento.
# 20 días

# un campo minimo te pide por hectarea 75kg/hectarea/año.
# 150ha para alquiler, 47millones/año. Puede meter 160 vacas.

# La cuenta se hace entre el ternero mas caro y la vaca más barata.
# hay un promedio de la feria de cañuelas de alquiler de arrendamiento.

# vaquillona para entorar, peso prom 350kg -> 1.310.000 pesos.
# vaquillona para entorar, peso prom 350kg -> 1.420.000 pesos.
## por remate.



# Octubre a Marzo: Parición - Lactancia - Servicio (mejores pastos)
# 

# Etapas:
# 1. Cría (baja rentabilidad)
#   1. Reproducción
#   2. Gestación
#   3. Cuidados del parto
#   4. Lactancia
# 2. Recría
# 3. Invernada / engorde
# 4. Etapa industrial (consumo directo de carne)