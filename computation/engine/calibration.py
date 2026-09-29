"""Modulo de Calibracao Numerica de Modelos Cineticos sobre Dados Empiricos (L5)."""

import math
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import curve_fit

from domain import Observation


def michaelis_menten_func(atp_uM: np.ndarray, v_max: float, k_m: float) -> np.ndarray:
    return (v_max * atp_uM) / (k_m + atp_uM)


def calibrate_kif5b_from_observations(
    observations: List[Observation],
    step_size_nm: float = 8.2,
) -> Dict[str, any]:
    """Calibra V_max e K_m sobre uma lista de observacoes usando regressao ponderada nao-linear."""
    atp_list = []
    vel_list = []
    unc_list = []

    for obs in observations:
        mea = obs.measurements[0]
        atp = float(mea.conditions["atp_concentration_uM"])
        v = float(mea.quantity.value)
        unc = float(mea.quantity.uncertainty) if mea.quantity.uncertainty else 0.02
        atp_list.append(atp)
        vel_list.append(v)
        unc_list.append(unc)

    x_data = np.array(atp_list, dtype=np.float64)
    y_data = np.array(vel_list, dtype=np.float64)
    sigma_data = np.array(unc_list, dtype=np.float64)

    # Chute inicial
    p0 = [0.8, 100.0]
    bounds = ([0.0, 0.0], [5.0, 1000.0])

    popt, pcov = curve_fit(
        michaelis_menten_func,
        x_data,
        y_data,
        p0=p0,
        sigma=sigma_data,
        absolute_sigma=True,
        bounds=bounds,
    )

    v_max_fit, km_fit = popt
    perr = np.sqrt(np.diag(pcov))
    v_max_err, km_err = perr

    # Converte V_max para k_cat via tamanho de passo (d_step = 8.2 nm = 0.0082 um)
    step_size_um = step_size_nm / 1000.0
    k_cat_fit = v_max_fit / step_size_um
    k_cat_err = v_max_err / step_size_um

    # Calculo de residuos e qualidade do ajuste
    y_pred = michaelis_menten_func(x_data, v_max_fit, km_fit)
    residuals = y_data - y_pred
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_data - np.mean(y_data))**2)
    r_squared = 1.0 - (ss_res / ss_tot)
    chi2_red = np.sum((residuals / sigma_data)**2) / (len(x_data) - len(popt))

    return {
        "v_max_um_s": float(v_max_fit),
        "v_max_err_um_s": float(v_max_err),
        "k_cat_per_s": float(k_cat_fit),
        "k_cat_err_per_s": float(k_cat_err),
        "k_m_uM": float(km_fit),
        "k_m_err_uM": float(km_err),
        "step_size_nm": step_size_nm,
        "r_squared": float(r_squared),
        "chi2_reduced": float(chi2_red),
        "residuals": [float(r) for r in residuals],
        "atp_inputs": [float(x) for x in x_data],
        "fitted_velocities": [float(y) for y in y_pred],
    }
