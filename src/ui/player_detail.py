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
    roles = player_rows["broad_role"].tolist()
    selected_role = st.selectbox("Eligible Role", roles)
    row = player_rows[player_rows["broad_role"] == selected_role].iloc[0]

    card_cols = st.columns(4)
    card_cols[0].metric("Performance", f"{row['performance_score']:.1f}" if pd.notna(row["performance_score"]) else "NA")
    card_cols[1].metric("Cost", f"{row['cost_score']:.1f}" if pd.notna(row["cost_score"]) else "NA")
    card_cols[2].metric("Value Gap", f"{row['value_gap_score']:.1f}" if pd.notna(row["value_gap_score"]) else "NA")
    card_cols[3].metric("Uncertainty", f"{row['uncertainty_score']:.1f}" if pd.notna(row["uncertainty_score"]) else "NA")

    family_scores = row.filter(like="__score").dropna()
    if not family_scores.empty:
        family_display = family_scores.rename(lambda value: value.replace("__score", ""))
        st.bar_chart(family_display)
        st.dataframe(family_display.rename("percentile").to_frame(), use_container_width=True)

    role_trace = traces[selected_role]
    raw_frame = role_trace["raw_primitives"].set_index("player_role_id")
    shrunk = role_trace["shrunk"]
    standardized = role_trace["standardized"]
    adjusted = role_trace["adjusted"]

    player_role_id = row["player_role_id"]
    family_meta = diagnostics["role_artifacts"][selected_role]["family"]
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
    st.markdown("**Adjusted Metrics**")
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

    warnings = diagnostics["role_warnings"].get(selected_role, [])
    if warnings:
        st.markdown("**Warnings**")
        for warning in warnings:
            st.warning(warning)
