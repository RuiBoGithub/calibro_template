import numpy as np
import pandas as pd

# -------------------------------------------------------------
# Normalise bounds
# -------------------------------------------------------------
def normalize_bound(b):
    if b is None:
        return None
    if isinstance(b, str) and b.upper() == "NA":
        return None
    return float(b)


# -------------------------------------------------------------
# Detect truncation (priority: user > automatic > none)
# -------------------------------------------------------------
def detect_truncation(mu, low, up, param_name, user_bounds=None, eps=1e-6):

    # 1. Use user-specified bounds if provided
    if user_bounds is not None and param_name in user_bounds:
        lo, hi = user_bounds[param_name]
        lo = normalize_bound(lo)
        hi = normalize_bound(hi)
        # User-specified truncation applied only to classification
        if lo is not None or hi is not None:
            return (lo if lo is not None else 0,
                    hi if hi is not None else None)

    # 2. Automatic detection
    if abs(up - 1.0) < eps:
        return (0, 1)
    if abs(low - 0.0) < eps:
        return (0, None)

    return None


# -------------------------------------------------------------
# Supporting computation
# -------------------------------------------------------------
def compute_sigma_from_CI(mu, low, up):
    dev = max(mu - low, up - mu)
    return dev / 1.96


def compute_beta_params(mu, var):
    m = mu
    v = var
    common = m*(1-m)/v - 1
    alpha = m * common
    beta  = (1-m) * common
    return alpha, beta


# -------------------------------------------------------------
# Classification: Truncated / Normal / Lognormal
# -------------------------------------------------------------
def classify_with_truncation(mu, low, up, param_name, user_bounds=None):

    # 1. Check truncation
    trunc = detect_truncation(mu, low, up, param_name, user_bounds=user_bounds)
    if trunc is not None:
        return "TruncatedNormal", trunc

    # 2. Symmetry check (Normal vs Lognormal)
    d_low = (mu - low) / mu
    d_up  = (up - mu) / mu
    asym_ratio = abs(d_up - d_low) / max(d_low, d_up, 1e-9)

    if asym_ratio < 0.25:
        return "Normal", None
    else:
        return "Lognormal", None


# -------------------------------------------------------------
# MAIN FUNCTION WITH ORIGINAL LOWER/UPPER INCLUDED
# -------------------------------------------------------------
def infer_distributions_with_trunc(df, user_bounds=None):
    rows = []

    for _, row in df.iterrows():
        param = row["PARAMETER"]
        mu = float(row["ESTIMATE"])
        low = float(row["LOWER"])
        up  = float(row["UPPER"])

        # --- apply user bounds by overwriting original limits (only if tighter) ---
        if user_bounds and param in user_bounds:
            lo_user, hi_user = user_bounds[param]
            lo_user = None if lo_user is None or str(lo_user).upper()=="NA" else float(lo_user)
            hi_user = None if hi_user is None or str(hi_user).upper()=="NA" else float(hi_user)

            if lo_user is not None:
                low = max(low, lo_user)
            if hi_user is not None:
                up = min(up, hi_user)

        # classification
        family, bounds = classify_with_truncation(
            mu, low, up, param_name=param, user_bounds=None
        )

        sigma = compute_sigma_from_CI(mu, low, up)
        cv = sigma / mu

        if family == "Normal":
            rows.append({
                "Parameter": param,
                "Distribution": "Normal",
                "Mean": mu,
                "Sigma": sigma,
                "CV": cv,
                "Lower": low,
                "Upper": up
            })

        elif family == "Lognormal":
            sigma_ln2 = np.log(1 + cv**2)
            sigma_ln = np.sqrt(sigma_ln2)
            mu_ln = np.log(mu) - 0.5*sigma_ln2

            rows.append({
                "Parameter": param,
                "Distribution": "Lognormal",
                "Mean": mu,
                "Mu_log": mu_ln,
                "Sigma_log": sigma_ln,
                "CV": cv,
                "Lower": low,
                "Upper": up
            })

        elif family == "TruncatedNormal":
            rows.append({
                "Parameter": param,
                "Distribution": "TruncatedNormal",
                "Mean": mu,
                "Sigma": sigma,
                "CV": cv,
                "Lower": low,
                "Upper": up
            })

    return pd.DataFrame(rows)