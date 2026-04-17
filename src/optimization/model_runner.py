# src/optimization/model_runner.py

import pandas as pd
from .model_daily import optimize_day


def run_daily_optimization(market_df, load_series, params):
    """
    Miopinis optimizavimas per visas dienas.

    market_df: DataFrame su stulpeliais:
        - price_eur_mwh
        - gen_solar_mw
        - gen_wind_onshore_mw
        (arba jau sumuota gen_ren)

    load_series: vartotojo apkrova (Series su datetime index)
    params: baterijos ir tinklo parametrai
    """

    # Užtikrinam, kad indeksai sutampa
    df = market_df.copy()
    df["load"] = load_series

    # Dienų sąrašas
    days = sorted(df.index.normalize().unique())

    all_results = []

    for day in days:
        day_mask = df.index.normalize() == day
        df_day = df.loc[day_mask]

        prices = df_day["price_eur_mwh"].values
        load = df_day["load"].values
        gen_ren = df_day["gen_ren"].values

        # Paleidžiam vienos dienos optimizavimą
        res_day = optimize_day(prices, load, gen_ren, params)

        # Pridedam datą prie rezultatų
        res_day["timestamp"] = df_day.index.values

        all_results.append(res_day)

    # Sujungiame viską į vieną DataFrame
    final = pd.concat(all_results).set_index("timestamp")

    return final
