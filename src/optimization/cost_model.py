import pandas as pd
import math


def capital_recovery_factor(r, L):
    """
    Compute Capital Recovery Factor (CRF) for discount rate r and lifetime L (years).
    CRF = r * (1 + r)^L / ((1 + r)^L - 1)
    """
    if r == 0:
        return 1.0 / L
    return r * (1 + r) ** L / ((1 + r) ** L - 1)


class CostModel:
    """
    Cost model for computing Total Annualized Cost (TAC)
    using:
        - fixed system sizes (P_pv, P_b, E_b)
        - economic parameters
        - dispatch results from DispatchModel
    """

    def __init__(self, P_pv, P_b, E_b, params):
        """
        Initialize cost model with fixed system sizes.

        Parameters:
            P_pv (float): PV installed capacity [kW]
            P_b  (float): Battery power capacity [kW]
            E_b  (float): Battery energy capacity [kWh]

            params (dict):
                C_pv, C_b_p, C_b_e   - CAPEX
                O_pv, O_b            - fixed OPEX
                r                    - discount rate
                L_pv, L_b_p, L_b_e   - lifetimes
                X, Y                 - buy/sell adjustments
                c_b_var              - battery throughput cost
        """
        self.P_pv = P_pv
        self.P_b = P_b
        self.E_b = E_b
        self.params = params

        # Precompute CRFs
        self.CRF_pv = capital_recovery_factor(params["r"], params["L_pv"])
        self.CRF_b_p = capital_recovery_factor(params["r"], params["L_b_p"])
        self.CRF_b_e = capital_recovery_factor(params["r"], params["L_b_e"])

    def compute_TAC(self, dispatch_df):
        """
        Compute Total Annualized Cost (TAC) using dispatch results.

        Inputs:
            dispatch_df - DataFrame returned by DispatchModel.run()

        Returns:
            dict with:
                - TAC_total
                - CAPEX_annual
                - OPEX_fixed
                - cost_grid
                - cost_battery_throughput
        """

        # ----- 1. Annualized CAPEX -----
        CAPEX_annual = (
            self.CRF_pv * self.params["C_pv"] * self.P_pv +
            self.CRF_b_p * self.params["C_b_p"] * self.P_b +
            self.CRF_b_e * self.params["C_b_e"] * self.E_b
        )

        # ----- 2. Fixed OPEX -----
        OPEX_fixed = (
            self.params["O_pv"] * self.P_pv +
            self.params["O_b"] * self.P_b
        )

        # ----- 3. Grid costs (import/export) -----
        cost_grid = (
            ((dispatch_df["price"] + self.params["X"]) * dispatch_df["P_grid_imp"])
            - ((dispatch_df["price"] - self.params["Y"]) * dispatch_df["P_grid_exp"])
        ).sum()

        # ----- 4. Battery throughput cost -----
        cost_battery_throughput = (
            self.params["c_b_var"] *
            (dispatch_df["P_ch"] + dispatch_df["P_dis"])
        ).sum()

        # ----- 5. Total TAC -----
        TAC_total = CAPEX_annual + OPEX_fixed + cost_grid + cost_battery_throughput

        return {
            "TAC_total": TAC_total,
            "CAPEX_annual": CAPEX_annual,
            "OPEX_fixed": OPEX_fixed,
            "cost_grid": cost_grid,
            "cost_battery_throughput": cost_battery_throughput
        }
