import pandas as pd
import pulp


class DispatchModel:
    """
    Day-ahead battery and PV dispatch optimization model.
    Solves each day independently (myopic optimization).
    """

    def __init__(self, P_pv=None, P_b=None, E_b=None, params=None):
        """
        Parameters:
            P_pv   : PV inverter power limit (kW)
            P_b    : Battery charge/discharge power limit (kW)
            E_b    : Battery energy capacity (kWh)
            params : Dictionary of model parameters (efficiencies, grid limits, costs, etc.)
        """
        self.P_pv = P_pv
        self.P_b = P_b
        self.E_b = E_b
        self.params = params

    def solve_one_day(self, df_day, E0):
        """
        Solve the dispatch problem for a single day.

        Inputs:
            df_day : DataFrame with columns [load, gen_pv, price]
            E0     : Initial battery state of charge (kWh)

        Returns:
            DataFrame with dispatch results for the day.
        """

        T = len(df_day)
        model = pulp.LpProblem("day_dispatch", pulp.LpMinimize)

        # Decision variables ----------------------------------------------------

        # PV directly serving load
        P_pv_load = pulp.LpVariable.dicts("P_pv_load", range(T), lowBound=0)

        # Battery charge/discharge power
        P_ch = pulp.LpVariable.dicts("P_ch", range(T), lowBound=0, upBound=self.P_b)
        P_dis = pulp.LpVariable.dicts("P_dis", range(T), lowBound=0, upBound=self.P_b)

        # Grid import/export
        P_grid_imp = pulp.LpVariable.dicts(
            "P_grid_imp", range(T), lowBound=0, upBound=self.params["P_grid_max"]
        )
        P_grid_exp = pulp.LpVariable.dicts(
            "P_grid_exp", range(T), lowBound=0, upBound=self.params["P_grid_max"]
        )

        # PV curtailment and load shedding (penalized heavily)
        P_curt = pulp.LpVariable.dicts("P_curt", range(T), lowBound=0)
        P_shed = pulp.LpVariable.dicts("P_shed", range(T), lowBound=0)

        # Battery state of charge
        E = pulp.LpVariable.dicts(
            "E",
            range(T),
            lowBound=self.params["SoC_min"] * self.E_b,
            upBound=self.params["SoC_max"] * self.E_b,
        )

        # Value of Lost Load (penalty for unmet demand)
        VOLL = self.params.get("VOLL", 10000)

        # Objective function ----------------------------------------------------
        # Minimize total cost: imports, exports (negative revenue), battery cycling cost, load shedding penalty.
        model += pulp.lpSum([
            (df_day["price"].iloc[t] + self.params["X"]) * P_grid_imp[t]
            - (df_day["price"].iloc[t] - self.params["Y"]) * P_grid_exp[t]
            + self.params["c_b_var"] * (P_ch[t] + P_dis[t])
            + VOLL * P_shed[t]
            for t in range(T)
        ])

        # Constraints -----------------------------------------------------------

        for t in range(T):
            D = df_day["load"].iloc[t]
            G = df_day["gen_pv"].iloc[t]

            # PV-to-load is fixed as min(load, PV)
            pv_to_load_fixed = min(D, G)
            model += P_pv_load[t] == pv_to_load_fixed

            # Load balance: load must be served by PV, battery discharge, grid import, or shedding
            model += (
                P_pv_load[t] + P_dis[t] + P_grid_imp[t] + P_shed[t]
                == D
            )

            # PV balance: PV goes to load, battery charging, export, or curtailment
            model += (
                P_pv_load[t] + P_ch[t] + P_grid_exp[t] + P_curt[t]
                == G
            )

            # Battery power limits
            model += P_ch[t] <= self.P_b
            model += P_dis[t] <= self.P_b

            # Battery state of charge dynamics
            if t == 0:
                model += (
                    E[t]
                    == E0
                    + self.params["eta_c"] * P_ch[t]
                    - (1 / self.params["eta_d"]) * P_dis[t]
                )
            else:
                model += (
                    E[t]
                    == E[t - 1]
                    + self.params["eta_c"] * P_ch[t]
                    - (1 / self.params["eta_d"]) * P_dis[t]
                )

        # Terminal SoC requirement (optional)
        E_terminal_min = self.params.get("E_terminal_min", None)
        if E_terminal_min is not None:
            model += E[T - 1] >= E_terminal_min

        # Solve ----------------------------------------------------------------
        model.solve(pulp.PULP_CBC_CMD(msg=0))

        if pulp.LpStatus[model.status] != "Optimal":
            raise ValueError(f"Solver failed: {pulp.LpStatus[model.status]}")

        # Extract results -------------------------------------------------------
        records = []

        for t in range(T):
            records.append({
                "timestamp": df_day.index[t],
                "load": df_day["load"].iloc[t],
                "gen_pv": df_day["gen_pv"].iloc[t],
                "price": df_day["price"].iloc[t],

                "P_pv_use": P_pv_load[t].value(),
                "P_ch": P_ch[t].value(),
                "P_dis": P_dis[t].value(),
                "P_grid_imp": P_grid_imp[t].value(),
                "P_grid_exp": P_grid_exp[t].value(),
                "E": E[t].value(),
            })

        return pd.DataFrame(records).set_index("timestamp")

    def run(self, df, E0):
        """
        Run the dispatch model for an entire multi-day dataset.
        Each day is optimized independently (myopic approach).
        The final SoC of each day becomes the initial SoC of the next day.
        """

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")

        df = df.copy()
        df["date"] = df.index.date

        results = []

        for _, df_day in df.groupby("date"):
            df_day = df_day.sort_index()
            df_res = self.solve_one_day(df_day, E0)

            # Carry over end-of-day SoC to next day
            E0 = df_res["E"].iloc[-1]

            results.append(df_res)

        return pd.concat(results).sort_index()
