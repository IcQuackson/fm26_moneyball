from __future__ import annotations

import pandas as pd
import streamlit as st


def render_diagnostics(payload: dict) -> None:
    st.subheader("Diagnostics")
    diagnostics = payload["diagnostics"]
    results = payload["results"]
    traces = payload["traces"]

    st.markdown("**Role Sizes**")
    role_sizes = diagnostics["role_sizes"]
    if isinstance(role_sizes.index, pd.MultiIndex):
        role_sizes = role_sizes.rename("count").reset_index()
        role_sizes["cohort"] = role_sizes["Division__raw"] + " | " + role_sizes["broad_role"]
        st.dataframe(role_sizes[["cohort", "count"]], use_container_width=True)
    else:
        st.bar_chart(role_sizes)

    st.markdown("**Missingness**")
    missingness = diagnostics["load_meta"]["missingness"].rename("missing_share").to_frame()
    st.dataframe(missingness, use_container_width=True)

    explained_rows = []
    for cohort_key, artifact in diagnostics["role_artifacts"].items():
        division, role = cohort_key.split("::", 1)
        for family, meta in artifact["family"].items():
            explained_rows.append(
                {
                    "division": division,
                    "role": role,
                    "component": family,
                    "explained_variance": meta.get("explained_variance"),
                }
            )
        explained_rows.append(
            {
                "division": division,
                "role": role,
                "component": "overall_performance",
                "explained_variance": artifact["performance"].get("explained_variance"),
            }
        )
    if explained_rows:
        explained_df = pd.DataFrame(explained_rows)
        st.markdown("**PCA Explained Variance**")
        st.dataframe(explained_df, use_container_width=True)

    st.markdown("**Dropped Primitive Columns**")
    dropped_rows = []
    for cohort_key, families in diagnostics["dropped_columns"].items():
        division, role = cohort_key.split("::", 1)
        for family, columns in families.items():
            dropped_rows.append({"division": division, "role": role, "family": family, "dropped_columns": ", ".join(columns)})
    if dropped_rows:
        st.dataframe(pd.DataFrame(dropped_rows), use_container_width=True)

    role_for_corr = st.selectbox("Correlation Matrix Cohort", sorted(traces.keys()))
    adjusted = traces[role_for_corr]["adjusted"]
    corr = adjusted.corr(numeric_only=True).round(3)
    st.markdown("**Adjusted Primitive Correlations**")
    st.dataframe(corr, use_container_width=True)

    stability = results[["player", "division", "broad_role", "bootstrap_sd", "uncertainty_score"]].sort_values("bootstrap_sd", ascending=False)
    st.markdown("**Bootstrap Stability Summary**")
    st.dataframe(stability, use_container_width=True)

    all_warnings = [
        {"cohort": cohort_key, "warning": warning}
        for cohort_key, warnings in diagnostics["role_warnings"].items()
        for warning in warnings
    ]
    if all_warnings:
        st.markdown("**Warnings**")
        st.dataframe(pd.DataFrame(all_warnings), use_container_width=True)
