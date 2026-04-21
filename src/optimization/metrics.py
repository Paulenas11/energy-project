import pandas as pd

def compute_metrics(results):
    """
    Compute financial, energy, and battery performance metrics
    from the hourly optimization results dataframe.
    """

    # Work on a copy to avoid modifying the original results
    df = results.copy()

    # Calculate hourly cost of imported energy
    df["cost_buy"] = df["price"] * df["P_grid_buy"]

    # Calculate hourly revenue from exported energy
    df["revenue_sell"] = df["price"] * df["P_grid_sell"]

    # Aggregate financial metrics
    total_buy_cost = df["cost_buy"].sum()
    total_sell_revenue = df["revenue_sell"].sum()

    # Net cost = imports cost minus export revenue
    net_cost = total_buy_cost - total_sell_revenue

    # Total imported and exported energy over the period
    total_import = df["P_grid_buy"].sum()
    total_export = df["P_grid_sell"].sum()

    # Total battery charge and discharge energy
    total_charge = df["P_ch"].sum()
    total_discharge = df["P_dis"].sum()

    # Renewable energy usage breakdown
    total_ren_used = df["P_ren_load"].sum()      # renewable energy used directly for load
    total_ren_to_batt = df["P_ren_ch"].sum()     # renewable energy sent to battery
    total_ren_to_grid = df["P_ren_grid"].sum()   # renewable energy exported to grid

    # Battery state-of-charge statistics
    soc_min = df["SoC"].min()
    soc_max = df["SoC"].max()

    # Battery throughput = total energy cycled through the battery
    throughput = total_charge + total_discharge

    # Aggregate results by day, month, and year
    df_daily = df.resample("D").sum(numeric_only=True)
    df_monthly = df.resample("ME").sum(numeric_only=True)
    df_yearly = df.resample("YE").sum(numeric_only=True)

    # Return structured metrics for UI and reporting
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
