import pandas as pd
import math


def capital_recovery_factor(r, L):
    """
    Compute the Capital Recovery Factor (CRF).

    CRF converts a one-time investment cost into an equivalent
    annualized cost over the asset lifetime.

    Parameters:
        r : Discount rate (decimal)
        L : Asset lifetime (years)

    Returns:
        Annualized cost multiplier (float)
    """
    if r == 0:
        return 1.0 / L
    return r * (1 + r) ** L / ((1 + r) ** L - 1)


class CostModel:
    """
    Compute Total Annualized Cost (TAC) for a PV + battery system
    based on dispatch results and economic parameters.
    """

    def __init__(self, P_pv, P_b, E_b, params):
        """
        Parameters:
            P_pv   : Installed PV inverter capacity (kW)
            P_b    : Battery charge/discharge power rating (kW)
            E_b    : Battery energy capacity (kWh)
            params : Dictionary of economic parameters:
                     - r          : discount rate
                     - L_pv       : PV lifetime (years)
                     - L_b_p      : battery power lifetime
                     - L_b_e      : battery energy lifetime
                     - C_pv       : PV cost per kW
                     - C_b_p      : battery power cost per kW
                     - C_b_e      : battery energy cost per kWh
                     - O_pv       : PV fixed OPEX per kW
                     - O_b        : battery fixed OPEX per kW
                     - X, Y       : grid import/export adders
                     - c_b_var    : variable battery cycling cost
        """

        self.P_pv = P_pv
        self.P_b = P_b
        self.E_b = E_b
        self.params = params

        # Precompute CRF multipliers for annualizing CAPEX
        self.CRF_pv = capital_recovery_factor(params["r"], params["L_pv"])
        self.CRF_b_p = capital_recovery_factor(params["r"], params["L_b_p"])
        self.CRF_b_e = capital_recovery_factor(params["r"], params["L_b_e"])

    def compute_TAC(self, dispatch_df):
        """
        Compute the Total Annualized Cost (TAC) of the system.

        TAC includes:
            - Annualized CAPEX (PV + battery)
            - Fixed OPEX
            - Grid import/export cost
            - Battery throughput (cycling) cost

        Parameters:
            dispatch_df : DataFrame with dispatch results
                          containing columns:
                          [price, P_grid_imp, P_grid_exp, P_ch, P_dis]

        Returns:
            Dictionary with cost breakdown.
        """

        # Annualized capital expenditure
        CAPEX_annual = (
            self.CRF_pv * self.params["C_pv"] * self.P_pv +
            self.CRF_b_p * self.params["C_b_p"] * self.P_b +
            self.CRF_b_e * self.params["C_b_e"] * self.E_b
        )

        # Fixed annual operating costs
        OPEX_fixed = (
            self.params["O_pv"] * self.P_pv +
            self.params["O_b"] * self.P_b
        )

        # Grid import/export cost
        # Import cost = (price + X) * P_grid_imp
        # Export revenue = (price - Y) * P_grid_exp
        cost_grid = (
            ((dispatch_df["price"] + self.params["X"]) * dispatch_df["P_grid_imp"])
            - ((dispatch_df["price"] - self.params["Y"]) * dispatch_df["P_grid_exp"])
        ).sum()

        # Battery variable cost (cycling cost)
        cost_battery_throughput = (
            self.params["c_b_var"] *
            (dispatch_df["P_ch"] + dispatch_df["P_dis"])
        ).sum()

        # Total annualized cost
        TAC_total = CAPEX_annual + OPEX_fixed + cost_grid + cost_battery_throughput

        return {
            "TAC_total": TAC_total,
            "CAPEX_annual": CAPEX_annual,
            "OPEX_fixed": OPEX_fixed,
            "cost_grid": cost_grid,
            "cost_battery_throughput": cost_battery_throughput
        }
