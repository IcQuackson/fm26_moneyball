from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src.ui.presentation import (
    confidence_label,
    format_role_label,
    formatted_table,
    percentile_band,
    percentile_text,
    trait_label,
)

def _category_score_columns(results: pd.DataFrame) -> list[str]:
    excluded = {"performance_score", "cost_score", "value_gap_score", "uncertainty_score"}
    return [
        column
        for column in results.columns
        if column.endswith("__score") and column not in excluded
    ]


def _add_trait_summary(frame: pd.DataFrame, category_score_cols: list[str]) -> pd.DataFrame:
    summary = frame.copy()
    if category_score_cols:
        category_frame = summary[category_score_cols].copy()
        summary["category_mean_score"] = category_frame.mean(axis=1, skipna=True)
        summary["best_category"] = category_frame.idxmax(axis=1).str.replace("__score", "", regex=False)
        summary["best_category_score"] = category_frame.max(axis=1, skipna=True)
    else:
        summary["category_mean_score"] = pd.NA
        summary["best_category"] = pd.NA
        summary["best_category_score"] = pd.NA
    return summary


def _render_league_rankings(filtered: pd.DataFrame, category_score_cols: list[str]) -> None:
    st.markdown("**League Trait Rankings**")
    if filtered.empty:
        st.info("No player profiles match the current filters.")
        return
    if not category_score_cols:
        st.info("Trait rankings are unavailable because no role-fit traits were scored for this filter.")
        return

    role_options = sorted(filtered["broad_role"].dropna().unique().tolist())
    if not role_options:
        st.info("Select at least one role with scored players to view league trait rankings.")
        return
    ranking_role = st.selectbox(
        "Trait Ranking Role",
        options=role_options,
        format_func=format_role_label,
    )
    role_trait_columns = [
        column
        for column in category_score_cols
        if filtered.loc[filtered["broad_role"] == ranking_role, column].notna().any()
    ]
    if not role_trait_columns:
        st.info("No scored traits are available for that role inside the selected leagues.")
        return
    ranking_category = st.selectbox(
        "Trait To Rank",
        options=role_trait_columns,
        format_func=lambda value: trait_label(value.replace("__score", "")),
    )
    top_n = st.slider("Players To Show Per League", 5, 50, 15)

    league_pool = filtered[filtered["broad_role"] == ranking_role].copy()
    if league_pool.empty:
        st.info("No player profiles are available for that role in the selected leagues.")
        return

    for division in sorted(league_pool["division"].dropna().unique().tolist()):
        league_frame = league_pool[league_pool["division"] == division].copy()
        if league_frame.empty:
            continue
        display = league_frame[["player", "club", "minutes", ranking_category, "value_gap_score", "cost_score", "uncertainty_score"]].copy()
        display["rank"] = display[ranking_category].rank(method="min", ascending=False)
        display["grade"] = display[ranking_category].map(percentile_band)
        display["confidence"] = display["uncertainty_score"].map(lambda value: confidence_label(value)[0])
        display = display.sort_values(["rank", "player"]).head(top_n)
        display = display.rename(
            columns={
                "player": "Player",
                "club": "Club",
                "minutes": "Minutes",
                ranking_category: trait_label(ranking_category.replace("__score", "")),
                "value_gap_score": "Value Pick",
                "cost_score": "Price Level",
                "rank": "Rank",
                "grade": "Grade",
                "confidence": "Confidence",
            }
        )
        display = display[["Rank", "Player", "Club", "Minutes", trait_label(ranking_category.replace("__score", "")), "Grade", "Value Pick", "Price Level", "Confidence"]]
        st.markdown(f"**{division}**")
        st.dataframe(
            formatted_table(
                display,
                percent_columns=[trait_label(ranking_category.replace("__score", "")), "Value Pick", "Price Level"],
            ),
            use_container_width=True,
        )


def render_overview(results: pd.DataFrame) -> None:
    st.subheader("Scout Board")
    if results.empty:
        st.info("No eligible player-role rows were produced from the upload.")
        return

    division_options = sorted(results["division"].dropna().unique().tolist())
    selected_divisions = st.multiselect("Leagues", division_options, default=division_options)
    role_options = ["All"] + sorted(results["broad_role"].dropna().unique().tolist())
    selected_role = st.selectbox("Role", role_options, index=0)
    club_options = ["All"] + sorted(results["club"].dropna().unique().tolist())
    selected_club = st.selectbox("Club", club_options, index=0)
    age_range = st.slider("Age band", 15, 45, (15, 45))
    max_minutes = int(results["minutes"].fillna(0).max())
    if max_minutes > 0:
        minutes_range = st.slider(
            "Minutes band",
            0,
            max_minutes,
            (0, max_minutes),
        )
    else:
        minutes_range = None
        st.info("Minutes filter is unavailable because all rows have zero or missing minutes.")

    filtered = results.copy()
    if selected_divisions:
        filtered = filtered[filtered["division"].isin(selected_divisions)]
    else:
        filtered = filtered.iloc[0:0]
    if selected_role != "All":
        filtered = filtered[filtered["broad_role"] == selected_role]
    if selected_club != "All":
        filtered = filtered[filtered["club"] == selected_club]
    filtered = filtered[filtered["age"].between(age_range[0], age_range[1], inclusive="both")]
    if minutes_range is not None:
        filtered = filtered[filtered["minutes"].between(minutes_range[0], minutes_range[1], inclusive="both")]

    category_score_cols = _category_score_columns(filtered)
    filtered = _add_trait_summary(filtered, category_score_cols)

    headline_cols = st.columns(4)
    headline_cols[0].metric("Profiles", str(len(filtered)))
    headline_cols[1].metric("Average Age", f"{filtered['age'].mean():.1f}" if not filtered.empty else "NA")
    headline_cols[2].metric("Average Squad Fit", percentile_text(filtered["category_mean_score"].mean()) if filtered["category_mean_score"].notna().any() else "NA")
    headline_cols[3].metric("Value Picks", str(int((filtered["value_gap_score"] >= 75).sum())) if filtered["value_gap_score"].notna().any() else "0")

    if selected_divisions:
        league_copy = ", ".join(selected_divisions[:3])
        if len(selected_divisions) > 3:
            league_copy += f" +{len(selected_divisions) - 3} more"
        st.caption(f"Showing {len(filtered)} profiles across {len(selected_divisions)} selected league(s): {league_copy}.")
    else:
        st.warning("Pick at least one league to populate the scout board.")

    scout_view = filtered[
        [
            "player",
            "division",
            "club",
            "broad_role",
            "age",
            "minutes",
            "best_category",
            "best_category_score",
            "category_mean_score",
            "cost_score",
            "value_gap_score",
            "uncertainty_score",
        ]
    ]
    scout_view = scout_view.rename(
        columns={
            "player": "Player",
            "division": "League",
            "club": "Club",
            "broad_role": "Role",
            "age": "Age",
            "minutes": "Minutes",
            "best_category": "Top Trait",
            "best_category_score": "Trait Score",
            "category_mean_score": "Squad Fit",
            "cost_score": "Price Level",
            "value_gap_score": "Value Pick",
            "uncertainty_score": "Scout Confidence",
        }
    )
    scout_view["Role"] = scout_view["Role"].map(format_role_label)
    scout_view["Top Trait"] = scout_view["Top Trait"].map(trait_label)
    scout_view["Scout Confidence"] = scout_view["Scout Confidence"].map(lambda value: confidence_label(value)[0])
    scout_view = scout_view.sort_values(["Value Pick", "Squad Fit"], ascending=False)
    st.dataframe(
        formatted_table(
            scout_view,
            percent_columns=["Trait Score", "Squad Fit", "Price Level", "Value Pick"],
        ),
        use_container_width=True,
    )

    buffer = io.StringIO()
    export_frame = filtered[
        [
            "player",
            "division",
            "club",
            "broad_role",
            "age",
            "minutes",
            "best_category",
            "best_category_score",
            "category_mean_score",
            "performance_score",
            "cost_score",
            "value_gap_score",
            "uncertainty_score",
        ]
        + category_score_cols
    ]
    export_frame.to_csv(buffer, index=False)
    st.download_button("Export scout board to CSV", data=buffer.getvalue(), file_name="fm26_cohort_overview.csv")

    chart_columns = ["player", "cost_score", "category_mean_score", "minutes", "broad_role", "division", "uncertainty_score"]
    chart_data = filtered[chart_columns].dropna(subset=["player", "cost_score", "category_mean_score", "minutes", "broad_role", "division"])
    if not chart_data.empty:
        encoding = {
            "x": {"field": "cost_score", "type": "quantitative", "title": "Price Level"},
            "y": {"field": "category_mean_score", "type": "quantitative", "title": "Squad Fit"},
            "size": {"field": "minutes", "type": "quantitative", "title": "Minutes"},
            "tooltip": [
                {"field": "player", "type": "nominal"},
                {"field": "division", "type": "nominal"},
                {"field": "broad_role", "type": "nominal", "title": "Role"},
                {"field": "minutes", "type": "quantitative"},
                {"field": "category_mean_score", "type": "quantitative", "title": "Squad Fit"},
                {"field": "cost_score", "type": "quantitative", "title": "Price Level"},
            ],
        }
        if chart_data["uncertainty_score"].notna().any():
            encoding["color"] = {"field": "uncertainty_score", "type": "quantitative", "title": "Risk"}
            encoding["tooltip"].append({"field": "uncertainty_score", "type": "quantitative", "title": "Risk"})
        st.vega_lite_chart(
            chart_data,
            {
                "mark": {"type": "circle", "tooltip": True},
                "encoding": encoding,
            },
            use_container_width=True,
        )

    if category_score_cols and not filtered.empty:
        st.markdown("**League Trait Snapshot**")
        category_snapshot = (
            filtered[category_score_cols]
            .rename(columns=lambda value: trait_label(value.replace("__score", "")))
            .mean(axis=0)
            .sort_values(ascending=False)
        )
        st.bar_chart(category_snapshot)

    if not filtered.empty:
        st.markdown("**Quick Read**")
        quick_read = filtered[["player", "best_category", "best_category_score", "value_gap_score", "uncertainty_score"]].copy()
        quick_read["best_category"] = quick_read["best_category"].map(trait_label)
        quick_read["trait_band"] = quick_read["best_category_score"].map(percentile_band)
        quick_read["value_band"] = quick_read["value_gap_score"].map(percentile_band)
        quick_read["confidence"] = quick_read["uncertainty_score"].map(lambda value: confidence_label(value)[0])
        quick_read_display = quick_read.rename(
                columns={
                    "player": "Player",
                    "best_category": "Standout Trait",
                    "best_category_score": "Trait Score",
                    "trait_band": "Trait Grade",
                    "value_gap_score": "Value Pick",
                    "value_band": "Value Grade",
                    "confidence": "Confidence",
                }
        )
        st.dataframe(
            formatted_table(
                quick_read_display,
                percent_columns=["Trait Score", "Value Pick"],
            ),
            use_container_width=True,
        )

    _render_league_rankings(filtered, category_score_cols)
