import pandas as pd
import pulp


def optimize_day(prices, load, gen_ren, params):
    """
    Solve a single-day linear optimization problem for battery dispatch.
    Inputs:
        prices   - hourly electricity prices
        load     - hourly consumption profile
        gen_ren  - hourly renewable generation profile
        params   - dictionary of battery and grid parameters
    Returns:
        DataFrame with hourly optimal dispatch results
    """

    # Number of time steps (hours in the day)
    T = len(prices)
    hours = range(T)

    # Define linear optimization problem (minimize total cost)
    model = pulp.LpProblem("daily_battery_dispatch", pulp.LpMinimize)

    # Battery charge and discharge power variables (kW)
    P_ch = pulp.LpVariable.dicts("P_ch", hours, lowBound=0)
    P_dis = pulp.LpVariable.dicts("P_dis", hours, lowBound=0)

    # Battery state of charge (kWh), bounded by min/max SoC limits
    SoC = pulp.LpVariable.dicts(
        "SoC", hours,
        lowBound=params["soc_min"] * params["E_max"],
        upBound=params["soc_max"] * params["E_max"]
    )

    # Grid import and export power (kW)
    P_grid_buy = pulp.LpVariable.dicts("P_grid_buy", hours, lowBound=0)
    P_grid_sell = pulp.LpVariable.dicts("P_grid_sell", hours, lowBound=0)

    # Renewable energy allocation variables
    P_ren_load = pulp.LpVariable.dicts("P_ren_load", hours, lowBound=0)
    P_ren_ch = pulp.LpVariable.dicts("P_ren_ch", hours, lowBound=0)
    P_ren_grid = pulp.LpVariable.dicts("P_ren_grid", hours, lowBound=0)

    # Grid purchase price multiplier (supplier markup)
    BUY_FACTOR = 1.05

    # Objective: minimize cost of imports minus revenue from exports
    model += pulp.lpSum(
        BUY_FACTOR * prices[t] * P_grid_buy[t]
        - params["sell_price_factor"] * prices[t] * P_grid_sell[t]
        for t in hours
    )

    # Load must be supplied by renewable energy, battery discharge, or grid imports
    for t in hours:
        model += (
            load[t]
            == P_ren_load[t] + P_dis[t] + P_grid_buy[t]
        )

    # Battery cannot discharge more than remaining load after renewables
    for t in hours:
        model += P_dis[t] <= load[t] - P_ren_load[t]

    # Renewable generation must be allocated to load, battery, or grid export
    for t in hours:
        model += (
            gen_ren[t]
            == P_ren_load[t] + P_ren_ch[t] + P_ren_grid[t]
        )

    # Renewable allocation constraints
    for t in hours:
        model += P_ren_load[t] <= load[t]
        model += P_ren_ch[t] <= gen_ren[t] - P_ren_load[t]
        model += P_ren_grid[t] <= gen_ren[t] - P_ren_load[t] - P_ren_ch[t]

    # Battery state-of-charge dynamics
    for t in hours:
        if t == 0:
            # First hour uses initial SoC
            model += (
                SoC[t]
                == params["SoC_start"]
                + params["eta_ch"] * P_ch[t]
                - (1 / params["eta_dis"]) * P_dis[t]
            )
        else:
            # Subsequent hours depend on previous SoC
            model += (
                SoC[t]
                == SoC[t - 1]
                + params["eta_ch"] * P_ch[t]
                - (1 / params["eta_dis"]) * P_dis[t]
            )

    # Battery charge/discharge power limits
    for t in hours:
        model += P_ch[t] <= params["P_ch_max"]
        model += P_dis[t] <= params["P_dis_max"]

    # Battery cannot discharge more than stored energy
    # and cannot charge beyond remaining capacity
    for t in hours:
        model += P_dis[t] <= SoC[t]
        model += P_ch[t] <= params["E_max"] - SoC[t]

    # Battery can only be charged using renewable energy
    for t in hours:
        model += P_ch[t] == P_ren_ch[t]

    # Grid import/export power limits
    for t in hours:
        model += P_grid_buy[t] <= params["P_grid_max"]
        model += P_grid_sell[t] <= params["P_grid_max"]

    # Export cannot exceed renewable export plus battery discharge
    for t in hours:
        model += P_ren_grid[t] <= gen_ren[t]
        model += P_grid_sell[t] <= P_ren_grid[t] + P_dis[t]

    # End-of-day SoC must return to initial value (myopic daily optimization)
    model += SoC[T - 1] == params["SoC_start"]

    # Solve optimization problem using CBC solver
    model.solve(pulp.PULP_CBC_CMD(msg=0))

    # Collect results into a DataFrame
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
