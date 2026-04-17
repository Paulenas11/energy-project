# src/optimization/model_daily.py

import pandas as pd
import pulp


def optimize_day(prices, load, gen_ren, params):
    """
    Vienos dienos tiesinis optimizavimas (LP) su CBC sprendikliu.

    Tikslas:
        Minimizuoti elektros energijos sąnaudas:
            sum_t (price_t * P_grid_buy_t - sell_price_factor * price_t * P_grid_sell_t)

    Pagrindinės savybės:
        - Miopinis: optimizuojama tik viena diena, be žvilgsnio į rytojų.
        - Green charging only: baterija kraunama tik iš vietinės generacijos (gen_ren).
        - Baterijos dydis (E_max, P_ch_max, P_dis_max) yra duoti parametrai, ne sprendiniai.
    """

    T = len(prices)
    hours = range(T)

    # -----------------------------
    # Modelio objektas
    # -----------------------------
    model = pulp.LpProblem("daily_battery_dispatch", pulp.LpMinimize)

    # -----------------------------
    # Sprendimo kintamieji
    # -----------------------------
    P_ch = pulp.LpVariable.dicts("P_ch", hours, lowBound=0)
    P_dis = pulp.LpVariable.dicts("P_dis", hours, lowBound=0)

    SoC = pulp.LpVariable.dicts(
        "SoC", hours,
        lowBound=params["soc_min"] * params["E_max"],
        upBound=params["soc_max"] * params["E_max"]
    )

    P_grid_buy = pulp.LpVariable.dicts("P_grid_buy", hours, lowBound=0)
    P_grid_sell = pulp.LpVariable.dicts("P_grid_sell", hours, lowBound=0)

    P_ren_load = pulp.LpVariable.dicts("P_ren_load", hours, lowBound=0)
    P_ren_ch = pulp.LpVariable.dicts("P_ren_ch", hours, lowBound=0)
    P_ren_grid = pulp.LpVariable.dicts("P_ren_grid", hours, lowBound=0)

    # -----------------------------
    # Tikslinė funkcija
    # -----------------------------
    BUY_FACTOR = 1.05  # tiekėjo antkainis

    model += pulp.lpSum(
        BUY_FACTOR * prices[t] * P_grid_buy[t]
        - params["sell_price_factor"] * prices[t] * P_grid_sell[t]
        for t in hours
    )

    # -----------------------------
    # Apribojimai
    # -----------------------------

    # 1. Apkrovos balansas: vartotojo poreikis turi būti patenkintas
    # 1. Apkrovos balansas
    for t in hours:
        model += (
                load[t]
                == P_ren_load[t] + P_dis[t] + P_grid_buy[t]
        )

    # 1a. Baterija iškraunama tik vartotojo poreikiui (ne eksportui)
    for t in hours:
        model += P_dis[t] <= load[t] - P_ren_load[t]

    # 2. Generacijos skaidymas: vietinė generacija padalinama į load / battery / grid
    for t in hours:
        model += (
            gen_ren[t]
            == P_ren_load[t] + P_ren_ch[t] + P_ren_grid[t]
        )
    # 2a. Prioritetas: pirma vartojam iš generacijos, tada kraunam, tik tada parduodam
    for t in hours:
        # generacija negali dengti daugiau nei apkrova
        model += P_ren_load[t] <= load[t]

        # baterija kraunama tik iš perteklinės generacijos
        model += P_ren_ch[t] <= gen_ren[t] - P_ren_load[t]

        # į tinklą parduodam tik tai, kas liko po apkrovos ir baterijos
        model += P_ren_grid[t] <= gen_ren[t] - P_ren_load[t] - P_ren_ch[t]

    # 3. Baterijos dinamika
    for t in hours:
        if t == 0:
            model += (
                SoC[t]
                == params["SoC_start"]
                + params["eta_ch"] * P_ch[t]
                - (1 / params["eta_dis"]) * P_dis[t]
            )
        else:
            model += (
                SoC[t]
                == SoC[t - 1]
                + params["eta_ch"] * P_ch[t]
                - (1 / params["eta_dis"]) * P_dis[t]
            )

    # 4. Baterijos galios ribos
    for t in hours:
        model += P_ch[t] <= params["P_ch_max"]
        model += P_dis[t] <= params["P_dis_max"]

    # 4a. Baterijos energijos ribos (fizika)
    for t in hours:
        model += P_dis[t] <= SoC[t]                     # negali iškrauti daugiau nei turi
        model += P_ch[t] <= params["E_max"] - SoC[t]    # negali įkrauti virš talpos


    # 5. Green charging only: baterija kraunama tik iš vietinės generacijos
    for t in hours:
        model += P_ch[t] == P_ren_ch[t]

    # 6. Tinklo ribos
    for t in hours:
        model += P_grid_buy[t] <= params["P_grid_max"]
        model += P_grid_sell[t] <= params["P_grid_max"]

    # 7. Negalima parduoti daugiau nei turima energijos
    for t in hours:
        model += P_ren_grid[t] <= gen_ren[t]                 # vietinė generacija
        model += P_grid_sell[t] <= P_ren_grid[t] + P_dis[t]  # generacija + baterijos iškrovimas


    # 8. Dienos cikliškumas: dienos pabaigoje SoC grįžta į pradinę reikšmę
    model += SoC[T - 1] == params["SoC_start"]

    # -----------------------------
    # Sprendimas su CBC
    # -----------------------------
    model.solve(pulp.PULP_CBC_CMD(msg=0))

    # -----------------------------
    # Rezultatų surinkimas
    # -----------------------------
    results = pd.DataFrame({
        "price": prices,
        "load": load,
        "gen_ren": gen_ren,
        "P_ch": [P_ch[t].value() for t in hours],
        "P_dis": [P_dis[t].value() for t in hours],
        "SoC": [SoC[t].value() for t in hours],
        "P_grid_buy": [P_grid_buy[t].value() for t in hours],
        "P_grid_sell": [P_grid_sell[t].value() for t in hours],
        "P_ren_load": [P_ren_load[t].value() for t in hours],
        "P_ren_ch": [P_ren_ch[t].value() for t in hours],
        "P_ren_grid": [P_ren_grid[t].value() for t in hours],
    })

    return results
