# src/optimization/metrics.py

import pandas as pd


def compute_metrics(results):
    """
    Skaičiuoja finansines ir energetines metrikas iš valandinio optimizavimo rezultato.
    """

    df = results.copy()

    # -----------------------------
    # Finansai
    # -----------------------------
    df["cost_buy"] = df["price"] * df["P_grid_buy"]
    df["revenue_sell"] = df["price"] * df["P_grid_sell"]

    total_buy_cost = df["cost_buy"].sum()
    total_sell_revenue = df["revenue_sell"].sum()
    net_cost = total_buy_cost - total_sell_revenue

    # -----------------------------
    # Energija
    # -----------------------------
    total_import = df["P_grid_buy"].sum()
    total_export = df["P_grid_sell"].sum()

    total_charge = df["P_ch"].sum()
    total_discharge = df["P_dis"].sum()

    total_ren_used = df["P_ren_load"].sum()
    total_ren_to_batt = df["P_ren_ch"].sum()
    total_ren_to_grid = df["P_ren_grid"].sum()

    # -----------------------------
    # Baterija
    # -----------------------------
    soc_min = df["SoC"].min()
    soc_max = df["SoC"].max()

    # paprastas throughput
    throughput = total_charge + total_discharge

    # -----------------------------
    # Agregacijos
    # -----------------------------
    df_daily = df.resample("D").sum(numeric_only=True)
    df_monthly = df.resample("ME").sum(numeric_only=True)
    df_yearly = df.resample("YE").sum(numeric_only=True)

    return {
        "financial": {
            "total_buy_cost": total_buy_cost,
            "total_sell_revenue": total_sell_revenue,
            "net_cost": net_cost,
        },
        "energy": {
            "total_import": total_import,
            "total_export": total_export,
            "total_charge": total_charge,
            "total_discharge": total_discharge,
            "total_ren_used": total_ren_used,
            "total_ren_to_batt": total_ren_to_batt,
            "total_ren_to_grid": total_ren_to_grid,
        },
        "battery": {
            "soc_min": soc_min,
            "soc_max": soc_max,
            "throughput": throughput,
        },
        "aggregations": {
            "daily": df_daily,
            "monthly": df_monthly,
            "yearly": df_yearly,
        }
    }
