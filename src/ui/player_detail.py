from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.presentation import (
    column_config_for,
    confidence_label,
    format_role_label,
    formatted_table,
    percentile_band,
    percentile_text,
    trait_label,
)


def _category_series(row: pd.Series) -> pd.Series:
    category_scores = row.filter(like="__score").drop(labels=["performance_score"], errors="ignore").dropna()
    return category_scores.drop(labels=["cost_score", "value_gap_score", "uncertainty_score"], errors="ignore")


def _radar_frame(players: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in players.iterrows():
        for metric, value in _category_series(row).items():
            rows.append(
                {
                    "player": row["player"],
                    "category": trait_label(metric.replace("__score", "")),
                    "percentile": float(value),
                }
            )
    return pd.DataFrame(rows)


def render_player_detail(results: pd.DataFrame, traces: dict, diagnostics: dict) -> None:
    st.subheader("Player Report")
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
    st.markdown(f"### {row['player']}")
    st.caption(f"{row['club']} | {selected_division} | {format_role_label(selected_role)}")

    category_scores = _category_series(row)
    top_categories = category_scores.sort_values(ascending=False).head(4)
    if not top_categories.empty:
        category_cols = st.columns(len(top_categories))
        for col, (label, value) in zip(category_cols, top_categories.items()):
            col.metric(trait_label(label.replace("__score", "")), percentile_text(value))

    confidence_text, confidence_value = confidence_label(row["uncertainty_score"])
    meta_cols = st.columns(4)
    meta_cols[0].metric("Scout Confidence", confidence_text if confidence_value is None else f"{confidence_text} ({percentile_text(confidence_value)})")
    meta_cols[1].metric("Value Pick", percentile_text(row["value_gap_score"]) if pd.notna(row["value_gap_score"]) else "NA")
    meta_cols[2].metric("Price Level", percentile_text(row["cost_score"]) if pd.notna(row["cost_score"]) else "NA")
    meta_cols[3].metric("Minutes Played", f"{int(row['minutes'])}" if pd.notna(row["minutes"]) else "NA")

    if not category_scores.empty:
        category_display = category_scores.rename(lambda value: trait_label(value.replace("__score", "")))
        st.markdown("**Role Fit Snapshot**")
        st.bar_chart(category_display)
        category_table = category_display.rename("Percentile").to_frame()
        cohort_category_scores = results[
            (results["division"] == selected_division) & (results["broad_role"] == selected_role)
        ]
        category_ranks = {}
        for metric in category_scores.index:
            rank_series = cohort_category_scores[metric].rank(method="min", ascending=False)
            category_ranks[trait_label(metric.replace("__score", ""))] = int(rank_series.loc[row.name]) if pd.notna(rank_series.loc[row.name]) else pd.NA
        category_table["League Rank"] = category_table.index.map(category_ranks.get)
        category_table["Grade"] = category_table["Percentile"].map(percentile_band)
        st.dataframe(
            formatted_table(category_table, percent_columns=["Percentile"]),
            column_config=column_config_for(category_table),
            width="stretch",
        )

        radar_data = _radar_frame(pd.DataFrame([row]))
        st.markdown("**Role Shape Radar**")
        st.vega_lite_chart(
            radar_data,
            {
                "layer": [
                    {
                        "mark": {"type": "line", "point": True},
                        "encoding": {
                            "theta": {"field": "category", "type": "nominal"},
                            "radius": {"field": "percentile", "type": "quantitative", "scale": {"domain": [0, 100]}},
                            "color": {"field": "player", "type": "nominal"},
                            "tooltip": [
                                {"field": "player", "type": "nominal"},
                                {"field": "category", "type": "nominal"},
                                {"field": "percentile", "type": "quantitative"},
                            ],
                        },
                    }
                ]
            },
            width="stretch",
        )

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
    metric_panel["Metric"] = [trait_label(metric) for metric in used_primitives]
    metric_panel["Percentile"] = metric_percentiles.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
    metric_panel["Grade"] = metric_panel["Percentile"].map(percentile_band)
    metric_panel["Match Value"] = raw_frame.loc[player_role_id, used_primitives].values
    metric_panel = metric_panel.sort_values("Percentile", ascending=False).reset_index(drop=True)

    st.markdown("**Percentile Analyzer**")
    percentile_chart = metric_panel[["Metric", "Percentile"]].copy()
    percentile_chart = percentile_chart.set_index("Metric")
    st.bar_chart(percentile_chart)
    top_metrics = metric_panel.head(5)
    bottom_metrics = metric_panel.tail(5).sort_values("Percentile", ascending=True)
    strength_cols = st.columns(2)
    strength_cols[0].markdown("**Standout Areas**")
    strength_cols[0].dataframe(
        formatted_table(top_metrics, percent_columns=["Percentile"]),
        column_config=column_config_for(top_metrics),
        width="stretch",
    )
    strength_cols[1].markdown("**Monitor Areas**")
    strength_cols[1].dataframe(
        formatted_table(bottom_metrics, percent_columns=["Percentile"]),
        column_config=column_config_for(bottom_metrics),
        width="stretch",
    )

    cohort_pool = results[
        (results["division"] == selected_division) & (results["broad_role"] == selected_role)
    ].copy()
    compare_options = cohort_pool["player"].drop_duplicates().tolist()
    default_compare = [row["player"]] + [player for player in compare_options if player != row["player"]][:1]
    compare_players = st.multiselect(
        "Compare Players In This Cohort",
        options=compare_options,
        default=default_compare,
        max_selections=3,
    )
    compare_rows = cohort_pool[cohort_pool["player"].isin(compare_players)].drop_duplicates(subset=["player"])
    if len(compare_rows) >= 2:
        st.markdown("**Comparison Radar**")
        comparison_radar = _radar_frame(compare_rows)
        st.vega_lite_chart(
            comparison_radar,
            {
                "layer": [
                    {
                        "mark": {"type": "line", "point": True},
                        "encoding": {
                            "theta": {"field": "category", "type": "nominal"},
                            "radius": {"field": "percentile", "type": "quantitative", "scale": {"domain": [0, 100]}},
                            "color": {"field": "player", "type": "nominal"},
                            "tooltip": [
                                {"field": "player", "type": "nominal"},
                                {"field": "category", "type": "nominal"},
                                {"field": "percentile", "type": "quantitative"},
                            ],
                        },
                    }
                ]
            },
            width="stretch",
        )
        compare_table = compare_rows[
            ["player", "club", "minutes", "value_gap_score", "cost_score", "uncertainty_score"]
            + [column for column in compare_rows.columns if column.endswith("__score") and column not in {"performance_score", "cost_score", "value_gap_score", "uncertainty_score"}]
        ].copy()
        compare_table = compare_table.rename(columns=lambda value: trait_label(value.replace("__score", "")) if value.endswith("__score") else value)
        compare_table = compare_table.rename(
            columns={
                "player": "Player",
                "club": "Club",
                "minutes": "Minutes",
                "value_gap_score": "Value Pick",
                "cost_score": "Price Level",
                "uncertainty_score": "Risk",
            }
        )
        percentile_columns = [column for column in compare_table.columns if column not in {"Player", "Club", "Minutes", "Risk"}]
        compare_table["Risk"] = compare_table["Risk"].map(lambda value: confidence_label(value)[0])
        st.markdown("**Side-by-Side Comparison**")
        st.dataframe(
            formatted_table(compare_table, percent_columns=percentile_columns),
            column_config=column_config_for(compare_table),
            width="stretch",
        )

    market_panel = pd.DataFrame(
        {
            "Estimated Fee": [row["Transfer Value"]],
            "Weekly Wage": [row["Wage"]],
            "Price Level": [row["cost_score"]],
            "Value Pick": [row["value_gap_score"]],
        }
    )
    st.markdown("**Market Snapshot**")
    st.dataframe(
        formatted_table(
            market_panel,
            percent_columns=["Price Level", "Value Pick"],
            money_columns=["Estimated Fee", "Weekly Wage"],
        ),
        column_config=column_config_for(market_panel),
        width="stretch",
    )

    with st.expander("Advanced Model Detail"):
        advanced_panel = pd.DataFrame(index=used_primitives)
        advanced_panel["Metric"] = [trait_label(metric) for metric in used_primitives]
        advanced_panel["Match Value"] = raw_frame.loc[player_role_id, used_primitives].values
        advanced_panel["Smoothed"] = shrunk.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
        advanced_panel["Role Context"] = standardized.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
        advanced_panel["Team Context"] = adjusted.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
        advanced_panel["Percentile"] = metric_percentiles.loc[raw_frame.index.get_loc(player_role_id), used_primitives].values
        st.dataframe(
            formatted_table(advanced_panel, percent_columns=["Percentile"]),
            column_config=column_config_for(advanced_panel),
            width="stretch",
        )

    warnings = diagnostics["role_warnings"].get(cohort_key, [])
    if warnings:
        st.markdown("**Notes**")
        for warning in warnings:
            st.warning(warning)
