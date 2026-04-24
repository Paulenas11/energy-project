import pandas as pd
import pulp


class DispatchModel:
    """
    Day-ahead (24h) LP dispatch model.

    - Solves one day at a time
    - Includes battery SoC dynamics
    - Uses CBC solver
    """

    def __init__(self, P_pv, P_b, E_b, params):
        self.P_pv = P_pv
        self.P_b = P_b
        self.E_b = E_b
        self.params = params

    # --------------------------------------------------
    # Solve ONE DAY (24h LP)
    # --------------------------------------------------
    def solve_one_day(self, df_day, E0):

        T = len(df_day)
        model = pulp.LpProblem("day_dispatch", pulp.LpMinimize)

        # -----------------------
        # VARIABLES
        # -----------------------
        P_pv_use = pulp.LpVariable.dicts("P_pv_use", range(T), lowBound=0)
        P_ch = pulp.LpVariable.dicts("P_ch", range(T), lowBound=0, upBound=self.P_b)
        P_dis = pulp.LpVariable.dicts("P_dis", range(T), lowBound=0, upBound=self.P_b)

        P_grid_imp = pulp.LpVariable.dicts(
            "P_grid_imp", range(T), lowBound=0, upBound=self.params["P_grid_max"]
        )
        P_grid_exp = pulp.LpVariable.dicts(
            "P_grid_exp", range(T), lowBound=0, upBound=self.params["P_grid_max"]
        )

        E = pulp.LpVariable.dicts(
            "E",
            range(T),
            lowBound=self.params["SoC_min"] * self.E_b,
            upBound=self.params["SoC_max"] * self.E_b,
        )

        # -----------------------
        # OBJECTIVE
        # -----------------------
        model += pulp.lpSum([
            (df_day["price"].iloc[t] + self.params["X"]) * P_grid_imp[t]
            - (df_day["price"].iloc[t] - self.params["Y"]) * P_grid_exp[t]
            + self.params["c_b_var"] * (P_ch[t] + P_dis[t])
            for t in range(T)
        ])

        # -----------------------
        # CONSTRAINTS
        # -----------------------
        for t in range(T):

            D = df_day["load"].iloc[t]
            G = df_day["gen_pv"].iloc[t]

            # ---- Power balance ----
            model += (
                P_pv_use[t] + P_dis[t] + P_grid_imp[t]
                == D + P_ch[t] + P_grid_exp[t]
            )

            # ---- PV limit ----
            model += P_pv_use[t] <= G

            # ---- Green charging (tik iš pertekliaus) ----
            model += P_ch[t] <= G - P_pv_use[t]

            # ---- SoC dynamics ----
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

        # -----------------------
        # SOLVE
        # -----------------------
        model.solve(pulp.PULP_CBC_CMD(msg=0))

        # -----------------------
        # RESULTS
        # -----------------------
        records = []

        for t in range(T):
            records.append({
                "timestamp": df_day.index[t],
                "load": df_day["load"].iloc[t],
                "gen_pv": df_day["gen_pv"].iloc[t],
                "price": df_day["price"].iloc[t],

                "P_pv_use": P_pv_use[t].value(),
                "P_ch": P_ch[t].value(),
                "P_dis": P_dis[t].value(),
                "P_grid_imp": P_grid_imp[t].value(),
                "P_grid_exp": P_grid_exp[t].value(),
                "E": E[t].value(),
            })

        df_res = pd.DataFrame(records)
        df_res = df_res.set_index("timestamp")

        return df_res

    # --------------------------------------------------
    # RUN FULL PERIOD (day-by-day)
    # --------------------------------------------------
    def run(self, df, E0):

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")

        df = df.copy()
        df["date"] = df.index.date

        results = []

        for day, df_day in df.groupby("date"):

            # svarbu: užtikrinam teisingą tvarką
            df_day = df_day.sort_index()

            # solve
            df_res = self.solve_one_day(df_day, E0)

            # update SoC į kitą dieną
            E0 = df_res["E"].iloc[-1]

            results.append(df_res)

        final_df = pd.concat(results)
        final_df = final_df.sort_index()

        return final_df