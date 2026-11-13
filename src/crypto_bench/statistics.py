import pandas as pd
def descriptive(df):
    if df.empty: return pd.DataFrame()
    out = df.groupby(["category", "algorithm", "operation", "payload_size_bytes"], dropna=False)["execution_time_ms"].agg(["count","mean","std","min","max"]).reset_index()
    from scipy.stats import t
    out["ci95_low"] = out["mean"] - t.ppf(.975, out["count"] - 1) * out["std"].fillna(0) / out["count"] ** .5
    out["ci95_high"] = out["mean"] + t.ppf(.975, out["count"] - 1) * out["std"].fillna(0) / out["count"] ** .5
    return out
def anova(df, alpha=.05):
    from scipy.stats import f_oneway
    rows = []
    for (cat, op, size), group in df.groupby(["category", "operation", "payload_size_bytes"], dropna=False):
        samples = [x["execution_time_ms"].to_numpy() for _, x in group.groupby("algorithm") if len(x) >= 2]
        names = [name for name, x in group.groupby("algorithm") if len(x) >= 2]
        if len(samples) >= 2:
            stat, p = f_oneway(*samples)
            rows.append({"category": cat, "operation": op, "payload_size_bytes": size,
                         "algorithms": ", ".join(names), "f_statistic": stat,
                         "p_value": p, "alpha": alpha, "significant": p < alpha})
    return pd.DataFrame(rows)
