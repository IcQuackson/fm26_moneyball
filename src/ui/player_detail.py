from __future__ import annotations

import pandas as pd
import streamlit as st


def render_player_detail(results: pd.DataFrame, traces: dict, diagnostics: dict) -> None:
    st.subheader("Player Detail")
    if results.empty:
        st.info("No scored players are available.")
        return

    players = sorted(results["player"].dropna().unique().tolist())
    selected_player = st.selectbox("Player", players)
    player_rows = results[results["player"] == selected_player].copy()
    cohort_labels = [
        f"{row['division']} | {row['broad_role']}"
        for _, row in player_rows[["division", "broad_role"]].drop_duplicates().iterrows()
    ]
    selected_cohort = st.selectbox("Division / Role", cohort_labels)
    selected_division, selected_role = [part.strip() for part in selected_cohort.split("|", 1)]
    row = player_rows[(player_rows["broad_role"] == selected_role) & (player_rows["division"] == selected_division)].iloc[0]
    cohort_key = row["cohort_key"]

    category_scores = row.filter(like="__score").drop(labels=["performance_score"], errors="ignore").dropna()
    category_scores = category_scores.drop(labels=["cost_score", "value_gap_score", "uncertainty_score"], errors="ignore")
    top_categories = category_scores.sort_values(ascending=False).head(4)
    if not top_categories.empty:
        category_cols = st.columns(len(top_categories))
        for col, (label, value) in zip(category_cols, top_categories.items()):
            col.metric(label.replace("__score", "").replace("_", " ").title(), f"{value:.1f}")

    meta_cols = st.columns(4)
    meta_cols[0].metric("Division", row["division"])
    meta_cols[1].metric("Cost", f"{row['cost_score']:.1f}" if pd.notna(row["cost_score"]) else "NA")
    meta_cols[2].metric("Value Gap", f"{row['value_gap_score']:.1f}" if pd.notna(row["value_gap_score"]) else "NA")
    meta_cols[3].metric("Uncertainty", f"{row['uncertainty_score']:.1f}" if pd.notna(row["uncertainty_score"]) else "Pending")

    if not category_scores.empty:
        category_display = category_scores.rename(lambda value: value.replace("__score", ""))
        st.markdown("**Category Percentiles**")
        st.bar_chart(category_display)
        st.dataframe(category_display.rename("percentile").to_frame(), use_container_width=True)

    role_trace = traces[cohort_key]
    raw_frame = role_trace["raw_primitives"].set_index("player_role_id")
    shrunk = role_trace["shrunk"]
    standardized = role_trace["standardized"]
    adjusted = role_trace["adjusted"]
    metric_percentiles = role_trace["metric_percentiles"]

    player_role_id = row["player_role_id"]
    family_meta = diagnostics["role_artifacts"][cohort_key]["family"]
    used_primitives = sorted(
        {
            primitive
            for meta in family_meta.values()
            for primitive in meta.get("kept", [])
        }
    )
    metric_panel = pd.DataFrame(index=used_primitives)
    metric_panel["raw"] = raw_frame.loc[player_role_id, used_primitives]
    metric_panel["shrunk"] = shrunk.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
    metric_panel["standardized"] = standardized.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
    metric_panel["pts_gm_adjusted"] = adjusted.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
    metric_panel["league_percentile"] = metric_percentiles.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
    st.markdown("**Metric Percentiles**")
    st.dataframe(metric_panel, use_container_width=True)

    uncertainty_panel = pd.DataFrame(
        {
            "minutes": [row["minutes"]],
            "bootstrap_dispersion": [row["bootstrap_sd"]],
            "shrinkage_intensity": [row["shrinkage_intensity"]],
            "exposure_uncertainty": [row["exposure_uncertainty"]],
        }
    )
    st.markdown("**Uncertainty Panel**")
    st.dataframe(uncertainty_panel, use_container_width=True)

    market_panel = pd.DataFrame(
        {
            "parsed_transfer_value": [row["Transfer Value"]],
            "parsed_wage": [row["Wage"]],
            "cost_percentile": [row["cost_score"]],
        }
    )
    st.markdown("**Market Panel**")
    st.dataframe(market_panel, use_container_width=True)

    warnings = diagnostics["role_warnings"].get(cohort_key, [])
    if warnings:
        st.markdown("**Warnings**")
        for warning in warnings:
            st.warning(warning)
