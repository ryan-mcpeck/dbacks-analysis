#!/usr/bin/env python3
"""
Dbacks Analytics - Player Performance Dashboard

Three-tab dashboard covering Pitching, Batting, and Fielding for the
Arizona Diamondbacks. Starts at team level with drill-down to individual
players compared against team averages.

Data Source: dbacks_team_statcast.csv (pitch-by-pitch Statcast data)
Team ID: AZ (Arizona Diamondbacks)

Pitching filter  : (home_team=='AZ' & inning_topbot=='Top') |
                   (away_team=='AZ' & inning_topbot=='Bot')
Batting filter   : (home_team=='AZ' & inning_topbot=='Bot') |
                   (away_team=='AZ' & inning_topbot=='Top')
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dbacks Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (D-backs branding) ────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-header {
        color: #A71930;
        text-align: center;
        padding: 20px 0;
        border-bottom: 3px solid #30CED8;
        margin-bottom: 30px;
    }
    .data-note {
        background-color: #e0f7fa;
        border-left: 4px solid #30CED8;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">'
    "<h1>⚾ Dbacks Analytics</h1>"
    "<h3>Player Performance Dashboard</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── D-backs Brand Colors ──────────────────────────────────────────────────────
DBACKS_RED = "#A71930"
DBACKS_TEAL = "#30CED8"
DBACKS_BLACK = "#000000"
DBACKS_COLORS = [DBACKS_RED, DBACKS_TEAL, DBACKS_BLACK, "#DBCEAC", "#8B0000", "#C8A882"]

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_and_enhance_data():
    """Load and enhance Diamondbacks Statcast data with derived pitch metrics.

    Adds boolean flag columns for strikes, balls, balls in play, and zone
    classification that are used throughout all three dashboard tabs.

    Returns:
        pd.DataFrame or None: Enhanced dataframe, or None on failure.
    """
    try:
        data = pd.read_csv("dbacks_team_statcast.csv")
        data["game_date"] = pd.to_datetime(data["game_date"])

        # Build derived columns in a single concat to avoid DataFrame fragmentation
        extra: dict = {}
        if "type" in data.columns:
            extra["is_strike"] = (data["type"] == "S").astype(int)
            extra["is_ball"] = (data["type"] == "B").astype(int)
            extra["is_bip"] = (data["type"] == "X").astype(int)
        else:
            extra["is_strike"] = 0
            extra["is_ball"] = 0
            extra["is_bip"] = 0

        # Zone classification: zones 1-9 are the defined strike zone
        extra["in_zone"] = (
            (data["zone"] <= 9).astype(int) if "zone" in data.columns else 0
        )

        data = pd.concat([data, pd.DataFrame(extra, index=data.index)], axis=1)
        return data

    except FileNotFoundError:
        st.error(
            "❌ Data file 'dbacks_team_statcast.csv' not found. "
            "Please run update_dbacks_statcast.py first."
        )
        return None
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None


# ── Data Filters ──────────────────────────────────────────────────────────────
def get_pitching_data(data):
    """Return rows when D-backs are the pitching/fielding team.

    D-backs pitch when they are the home team in the top half of an inning
    (opponent batting) or the away team in the bottom half (opponent batting).

    Args:
        data (pd.DataFrame): Full enhanced Statcast dataframe.

    Returns:
        pd.DataFrame: Rows where D-backs are pitching, or empty DataFrame.
    """
    if data is None or data.empty:
        return pd.DataFrame()
    try:
        mask = (
            ((data["home_team"] == "AZ") & (data["inning_topbot"] == "Top"))
            | ((data["away_team"] == "AZ") & (data["inning_topbot"] == "Bot"))
        )
        return data[mask].copy()
    except Exception as e:
        st.error(f"❌ Error filtering pitching data: {e}")
        return pd.DataFrame()


def get_batting_data(data):
    """Return rows when D-backs are the batting team.

    D-backs bat when they are the home team in the bottom half of an inning
    or the away team in the top half.

    Args:
        data (pd.DataFrame): Full enhanced Statcast dataframe.

    Returns:
        pd.DataFrame: Rows where D-backs are batting, or empty DataFrame.
    """
    if data is None or data.empty:
        return pd.DataFrame()
    try:
        mask = (
            ((data["home_team"] == "AZ") & (data["inning_topbot"] == "Bot"))
            | ((data["away_team"] == "AZ") & (data["inning_topbot"] == "Top"))
        )
        return data[mask].copy()
    except Exception as e:
        st.error(f"❌ Error filtering batting data: {e}")
        return pd.DataFrame()


# ── Pitcher Role Classification ───────────────────────────────────────────────
def classify_pitcher_roles(data):
    """Classify each pitcher's primary role based on game appearance patterns.

    Args:
        data (pd.DataFrame): D-backs pitching data.

    Returns:
        pd.DataFrame: One row per pitcher with a primary_role column.
    """
    if data is None or data.empty:
        return pd.DataFrame()
    try:
        required = ["game_pk", "player_name", "inning"]
        if not all(c in data.columns for c in required):
            return pd.DataFrame()

        game_stats = (
            data.groupby(["game_pk", "player_name"])
            .agg(
                first_inning=("inning", "min"),
                last_inning=("inning", "max"),
                total_pitches=("player_name", "count"),
            )
            .reset_index()
        )

        game_stats["is_starter"] = (
            (game_stats["first_inning"] == 1) & (game_stats["total_pitches"] >= 50)
        )
        game_stats["is_opener"] = (
            (game_stats["first_inning"] == 1) & (game_stats["total_pitches"] < 50)
        )
        game_stats["is_reliever"] = game_stats["first_inning"] > 1
        game_stats["is_closer"] = (
            (game_stats["last_inning"] >= 9) & game_stats["is_reliever"]
        )

        roles = (
            game_stats.groupby("player_name")
            .agg(
                is_starter=("is_starter", "sum"),
                is_opener=("is_opener", "sum"),
                is_reliever=("is_reliever", "sum"),
                is_closer=("is_closer", "sum"),
            )
            .reset_index()
        )

        def _primary(row):
            if row["is_starter"] >= 5:
                return "Starter"
            if row["is_closer"] >= 3:
                return "Closer"
            if row["is_opener"] >= 3:
                return "Opener"
            if row["is_reliever"] >= 5:
                return "Reliever"
            return "Utility"

        roles["primary_role"] = roles.apply(_primary, axis=1)
        return roles
    except Exception as e:
        st.error(f"❌ Error classifying pitcher roles: {e}")
        return pd.DataFrame()


# ── Metric Computation ────────────────────────────────────────────────────────
def compute_pitching_metrics(data):
    """Compute per-pitcher performance metrics from Statcast pitching data.

    Volume metrics: total pitches thrown, batters faced, games appeared.
    Performance metrics: K%, BB%, K/BB ratio, Strike%.

    Batters faced is derived from the count of at-bat-ending rows
    (rows where the 'events' column is non-null).

    Args:
        data (pd.DataFrame): D-backs pitching data (date/role filtered).

    Returns:
        pd.DataFrame: One row per pitcher sorted by total_pitches desc.
    """
    if data is None or data.empty:
        return pd.DataFrame()
    try:
        if "player_name" not in data.columns:
            st.warning("⚠️ Missing 'player_name' column for pitching metrics.")
            return pd.DataFrame()

        # Pitch-level aggregation
        pitch_agg = (
            data.groupby("player_name")
            .agg(
                total_pitches=("player_name", "count"),
                games=("game_pk", "nunique"),
                strikes=("is_strike", "sum"),
            )
            .reset_index()
        )

        # At-bat-level: the final pitch of each AB carries a non-null events value
        ab_data = data[data["events"].notna() & (data["events"] != "")].copy()

        strikeout_events = {"strikeout", "strikeout_double_play"}
        walk_events = {"walk"}

        bf_agg = ab_data.groupby("player_name").size().reset_index(name="batters_faced")
        k_agg = (
            ab_data[ab_data["events"].isin(strikeout_events)]
            .groupby("player_name")
            .size()
            .reset_index(name="strikeouts")
        )
        bb_agg = (
            ab_data[ab_data["events"].isin(walk_events)]
            .groupby("player_name")
            .size()
            .reset_index(name="walks")
        )

        metrics = (
            pitch_agg.merge(bf_agg, on="player_name", how="left")
            .merge(k_agg, on="player_name", how="left")
            .merge(bb_agg, on="player_name", how="left")
        )

        for col in ["batters_faced", "strikeouts", "walks"]:
            metrics[col] = metrics[col].fillna(0).astype(int)

        bf = metrics["batters_faced"].replace(0, np.nan)
        metrics["k_pct"] = (metrics["strikeouts"] / bf * 100).round(1).fillna(0)
        metrics["bb_pct"] = (metrics["walks"] / bf * 100).round(1).fillna(0)
        metrics["k_bb"] = (
            metrics["strikeouts"] / metrics["walks"].replace(0, np.nan)
        ).round(2).fillna(0)
        metrics["strike_pct"] = (
            metrics["strikes"] / metrics["total_pitches"].replace(0, np.nan) * 100
        ).round(1).fillna(0)

        return metrics.sort_values("total_pitches", ascending=False)
    except Exception as e:
        st.error(f"❌ Error computing pitching metrics: {e}")
        return pd.DataFrame()


def compute_batting_metrics(data):
    """Compute per-batter performance metrics from Statcast batting data.

    Volume metrics: plate appearances, at bats, games played.
    Performance metrics: AVG, OBP, Hits, RBI (approximated from score delta).

    Note: The 'batter' column contains MLBAM player IDs (integers) because
    Statcast data does not include a separate batter name field.  The IDs are
    used as player identifiers throughout this tab.

    RBI is approximated as the positive difference between post_bat_score
    and bat_score at the end of each plate appearance.

    Args:
        data (pd.DataFrame): D-backs batting data (date filtered).

    Returns:
        pd.DataFrame: One row per batter sorted by plate_appearances desc.
    """
    if data is None or data.empty:
        return pd.DataFrame()
    try:
        if "batter" not in data.columns:
            st.warning("⚠️ Missing 'batter' column for batting metrics.")
            return pd.DataFrame()

        ab_data = data[data["events"].notna() & (data["events"] != "")].copy()
        if ab_data.empty:
            return pd.DataFrame()

        hit_events = {"single", "double", "triple", "home_run"}
        walk_events = {"walk"}
        hbp_events = {"hit_by_pitch"}
        non_ab_events = {
            "walk", "hit_by_pitch", "sac_fly", "sac_bunt",
            "catcher_interf", "truncated_pa", "sac_fly_double_play",
        }

        games_agg = (
            data.groupby("batter")["game_pk"].nunique().reset_index(name="games")
        )
        pa_agg = ab_data.groupby("batter").size().reset_index(name="plate_appearances")
        ab_agg = (
            ab_data[~ab_data["events"].isin(non_ab_events)]
            .groupby("batter")
            .size()
            .reset_index(name="at_bats")
        )
        hits_agg = (
            ab_data[ab_data["events"].isin(hit_events)]
            .groupby("batter")
            .size()
            .reset_index(name="hits")
        )
        walks_agg = (
            ab_data[ab_data["events"].isin(walk_events)]
            .groupby("batter")
            .size()
            .reset_index(name="walks")
        )
        hbp_agg = (
            ab_data[ab_data["events"].isin(hbp_events)]
            .groupby("batter")
            .size()
            .reset_index(name="hbp")
        )

        rbi_available = (
            "post_bat_score" in ab_data.columns
            and "bat_score" in ab_data.columns
        )
        if rbi_available:
            ab_rbi = ab_data.copy()
            ab_rbi["approx_rbi"] = (
                ab_rbi["post_bat_score"] - ab_rbi["bat_score"]
            ).clip(lower=0)
            rbi_agg = (
                ab_rbi.groupby("batter")["approx_rbi"]
                .sum()
                .reset_index(name="rbi")
            )

        metrics = (
            games_agg.merge(pa_agg, on="batter", how="left")
            .merge(ab_agg, on="batter", how="left")
            .merge(hits_agg, on="batter", how="left")
            .merge(walks_agg, on="batter", how="left")
            .merge(hbp_agg, on="batter", how="left")
        )
        if rbi_available:
            metrics = metrics.merge(rbi_agg, on="batter", how="left")
        else:
            metrics["rbi"] = 0

        for col in ["plate_appearances", "at_bats", "hits", "walks", "hbp", "rbi"]:
            if col in metrics.columns:
                metrics[col] = metrics[col].fillna(0).astype(int)

        ab = metrics["at_bats"].replace(0, np.nan)
        pa = metrics["plate_appearances"].replace(0, np.nan)
        metrics["avg"] = (metrics["hits"] / ab).round(3).fillna(0)
        metrics["obp"] = (
            (metrics["hits"] + metrics["walks"] + metrics["hbp"]) / pa
        ).round(3).fillna(0)

        # Use batter ID as display identifier (no name column available)
        metrics["player_name"] = metrics["batter"].astype(str)

        return metrics.sort_values("plate_appearances", ascending=False)
    except Exception as e:
        st.error(f"❌ Error computing batting metrics: {e}")
        return pd.DataFrame()


def compute_fielding_metrics(data):
    """Compute team-level fielding metrics from D-backs pitching/fielding data.

    Uses balls-in-play (type=='X') events to approximate fielding performance.
    Individual fielder attribution is not computed because fielder_2..9
    columns contain MLBAM player IDs without a bundled name lookup table.

    Metrics:
        balls_in_play   : Count of balls put in play against D-backs fielders.
        in_zone_bip     : BIP within the strike zone (zones 1-9).
        zone_coverage_pct: in_zone_bip / balls_in_play * 100.
        outs_recorded   : Fielding out events (double plays count as 2 outs).
        double_plays    : Count of double-play events.
        out_rate_pct    : outs_recorded / balls_in_play * 100.

    Args:
        data (pd.DataFrame): D-backs pitching/fielding data.

    Returns:
        dict: Team-level fielding metric summary, or empty dict on failure.
    """
    if data is None or data.empty:
        return {}
    try:
        bip_data = (
            data[data["type"] == "X"].copy()
            if "type" in data.columns
            else pd.DataFrame()
        )

        balls_in_play = len(bip_data)
        in_zone_bip = (
            int(bip_data["in_zone"].sum())
            if ("in_zone" in bip_data.columns and not bip_data.empty)
            else 0
        )
        zone_coverage_pct = in_zone_bip / max(balls_in_play, 1) * 100

        out_events = {
            "field_out", "force_out", "grounded_into_double_play",
            "sac_fly", "sac_bunt", "fielders_choice_out",
            "double_play", "sac_fly_double_play",
        }
        dp_events = {
            "grounded_into_double_play", "double_play", "sac_fly_double_play"
        }

        if not bip_data.empty and "events" in bip_data.columns:
            outs_bip = bip_data[bip_data["events"].isin(out_events)]
            single_outs = len(outs_bip[~outs_bip["events"].isin(dp_events)])
            double_plays = len(outs_bip[outs_bip["events"].isin(dp_events)])
        else:
            single_outs = 0
            double_plays = 0

        outs_recorded = single_outs + (double_plays * 2)
        out_rate_pct = outs_recorded / max(balls_in_play, 1) * 100

        return {
            "balls_in_play": balls_in_play,
            "in_zone_bip": in_zone_bip,
            "zone_coverage_pct": round(zone_coverage_pct, 1),
            "outs_recorded": outs_recorded,
            "double_plays": double_plays,
            "out_rate_pct": round(out_rate_pct, 1),
        }
    except Exception as e:
        st.error(f"❌ Error computing fielding metrics: {e}")
        return {}


# ── Chart Helpers ─────────────────────────────────────────────────────────────
def ranking_bar_chart(df, player_col, metric_col, title, y_label, team_avg):
    """Bar chart ranking players by a metric with a team average reference line.

    Bars at or above the team average are Sedona Red; below are Teal.

    Args:
        df (pd.DataFrame): Per-player metrics dataframe.
        player_col (str): Column for player labels (x-axis).
        metric_col (str): Column for the plotted metric (y-axis).
        title (str): Chart title.
        y_label (str): Y-axis / hover label for the metric.
        team_avg (float): Value at which the dashed reference line is drawn.

    Returns:
        go.Figure: Plotly figure ready for st.plotly_chart.
    """
    sorted_df = df.sort_values(metric_col, ascending=False).copy()
    colors = [
        DBACKS_RED if v >= team_avg else DBACKS_TEAL
        for v in sorted_df[metric_col]
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=sorted_df[player_col],
            y=sorted_df[metric_col],
            marker_color=colors,
            marker_line_color=DBACKS_BLACK,
            marker_line_width=0.5,
            name=y_label,
            hovertemplate=f"<b>%{{x}}</b><br>{y_label}: %{{y:.2f}}<extra></extra>",
        )
    )
    fig.add_hline(
        y=team_avg,
        line_dash="dash",
        line_color=DBACKS_TEAL,
        line_width=2,
        annotation_text=f"Team Avg: {team_avg:.2f}",
        annotation_position="top right",
        annotation_font_color=DBACKS_TEAL,
    )
    fig.update_layout(
        title=title,
        xaxis_title="Player",
        yaxis_title=y_label,
        height=450,
        xaxis_tickangle=-40,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=DBACKS_TEAL),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
    )
    return fig


def player_vs_team_chart(player_name, player_vals, team_vals, metric_labels, title):
    """Grouped bar chart comparing a player's metrics against team averages.

    Args:
        player_name (str): Display name for the selected player.
        player_vals (list[float]): Player metric values (one per label).
        team_vals (list[float]): Corresponding team average values.
        metric_labels (list[str]): Display labels for each metric pair.
        title (str): Chart title.

    Returns:
        go.Figure: Plotly figure ready for st.plotly_chart.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=metric_labels,
            y=team_vals,
            name="Team Average",
            marker_color=DBACKS_TEAL,
            marker_line_color=DBACKS_BLACK,
            marker_line_width=1,
        )
    )
    fig.add_trace(
        go.Bar(
            x=metric_labels,
            y=player_vals,
            name=player_name,
            marker_color=DBACKS_RED,
            marker_line_color=DBACKS_BLACK,
            marker_line_width=1,
        )
    )
    fig.update_layout(
        barmode="group",
        title=title,
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=DBACKS_TEAL),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
    )
    return fig


# ── Load & Validate Data ──────────────────────────────────────────────────────
with st.spinner("🔄 Loading D-backs data…"):
    raw_data = load_and_enhance_data()

if raw_data is None:
    st.stop()

pitching_data_full = get_pitching_data(raw_data)
batting_data_full = get_batting_data(raw_data)

if pitching_data_full.empty:
    st.error("❌ No D-backs pitching data found in the dataset.")
    st.stop()

pitcher_roles = classify_pitcher_roles(pitching_data_full)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("⚾ Dashboard Controls")

min_date = pitching_data_full["game_date"].min().date()
max_date = pitching_data_full["game_date"].max().date()

# Default start = first game of the most recent season in the dataset
season_start = (
    pitching_data_full[
        pitching_data_full["game_date"].dt.year == max_date.year
    ]["game_date"].min().date()
)

st.sidebar.markdown(f"**Data range:** {min_date} → {max_date}")

start_date = st.sidebar.date_input(
    "Start Date", value=season_start, min_value=min_date, max_value=max_date
)
end_date = st.sidebar.date_input(
    "End Date", value=max_date, min_value=min_date, max_value=max_date
)

st.sidebar.markdown("---")
st.sidebar.markdown("**⚾ Pitching Filters**")
role_filter = st.sidebar.selectbox(
    "Pitcher Role",
    ["All Pitchers", "Starters Only", "Relievers Only", "Closers Only"],
)

# Apply date filter to pitching data
pitching_filtered = pitching_data_full[
    (pitching_data_full["game_date"].dt.date >= start_date)
    & (pitching_data_full["game_date"].dt.date <= end_date)
].copy()

# Apply role filter
if role_filter != "All Pitchers" and not pitcher_roles.empty:
    role_map = {
        "Starters Only": ["Starter"],
        "Relievers Only": ["Reliever", "Opener", "Utility"],
        "Closers Only": ["Closer"],
    }
    allowed = pitcher_roles[
        pitcher_roles["primary_role"].isin(role_map[role_filter])
    ]["player_name"].tolist()
    pitching_filtered = pitching_filtered[
        pitching_filtered["player_name"].isin(allowed)
    ]

if pitching_filtered.empty:
    st.warning("⚠️ No data for the selected filters — please adjust the sidebar.")
    st.stop()

# Apply date filter to batting data
batting_filtered = pd.DataFrame()
if not batting_data_full.empty:
    batting_filtered = batting_data_full[
        (batting_data_full["game_date"].dt.date >= start_date)
        & (batting_data_full["game_date"].dt.date <= end_date)
    ].copy()

# Pre-compute all metrics
pitching_metrics = compute_pitching_metrics(pitching_filtered)
batting_metrics = compute_batting_metrics(batting_filtered)
fielding_summary = compute_fielding_metrics(pitching_filtered)

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab_pitch, tab_bat, tab_field = st.tabs(
    ["⚾ Pitching", "🏏 Batting", "🧤 Fielding"]
)

# =============================================================================
# TAB 1 — PITCHING
# =============================================================================
with tab_pitch:
    st.header("⚾ Pitching Performance")

    if pitching_metrics.empty:
        st.warning("No pitching data available for the selected filters.")
    else:
        # ── Team Summary Cards ─────────────────────────────────────────────
        st.subheader("📊 Team Summary")

        total_pitches_team = int(pitching_metrics["total_pitches"].sum())
        total_bf_team = int(pitching_metrics["batters_faced"].sum())
        total_games_team = int(pitching_filtered["game_pk"].nunique())
        total_k = int(pitching_metrics["strikeouts"].sum())
        total_bb = int(pitching_metrics["walks"].sum())
        total_strikes = int(pitching_metrics["strikes"].sum())

        team_k_pct = total_k / max(total_bf_team, 1) * 100
        team_bb_pct = total_bb / max(total_bf_team, 1) * 100
        team_k_bb = total_k / max(total_bb, 1)
        team_strike_pct = total_strikes / max(total_pitches_team, 1) * 100

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        c1.metric("Total Pitches", f"{total_pitches_team:,}")
        c2.metric("Batters Faced", f"{total_bf_team:,}")
        c3.metric("Games", total_games_team)
        c4.metric("K%", f"{team_k_pct:.1f}%")
        c5.metric("BB%", f"{team_bb_pct:.1f}%")
        c6.metric("K/BB", f"{team_k_bb:.2f}")
        c7.metric("Strike%", f"{team_strike_pct:.1f}%")

        st.markdown("---")

        # ── All-Pitcher Ranking Chart ──────────────────────────────────────
        st.subheader("📈 All Pitchers — Ranked by K%")
        st.caption(
            "�� Sedona Red = at or above team average · "
            "🟡 Teal = below team average · "
            "Dashed line = team average"
        )

        # Require at least 1 batter faced to appear on chart
        plot_df = pitching_metrics[pitching_metrics["batters_faced"] >= 1].copy()
        if len(plot_df) >= 2:
            fig_rank = ranking_bar_chart(
                df=plot_df,
                player_col="player_name",
                metric_col="k_pct",
                title="Pitchers Ranked by Strikeout Rate (K%)",
                y_label="K%",
                team_avg=team_k_pct,
            )
            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.info("Need at least 2 pitchers for the ranking chart.")

        st.markdown("---")

        # ── Player Drill-Down ──────────────────────────────────────────────
        st.subheader("🔍 Player Drill-Down")

        available_pitchers = sorted(pitching_metrics["player_name"].unique())
        selected_pitcher = st.selectbox(
            "Select a Pitcher", available_pitchers, key="pitch_select"
        )

        p_row = pitching_metrics[
            pitching_metrics["player_name"] == selected_pitcher
        ]
        if p_row.empty:
            st.warning(f"No data found for {selected_pitcher}.")
        else:
            p = p_row.iloc[0]

            pc1, pc2, pc3, pc4, pc5, pc6, pc7 = st.columns(7)
            pc1.metric("Pitches", f"{int(p['total_pitches']):,}")
            pc2.metric("BF", int(p["batters_faced"]))
            pc3.metric("Games", int(p["games"]))
            pc4.metric(
                "K%", f"{p['k_pct']:.1f}%",
                delta=f"{p['k_pct'] - team_k_pct:+.1f}% vs team",
            )
            pc5.metric(
                "BB%", f"{p['bb_pct']:.1f}%",
                delta=f"{p['bb_pct'] - team_bb_pct:+.1f}% vs team",
                delta_color="inverse",
            )
            pc6.metric(
                "K/BB", f"{p['k_bb']:.2f}",
                delta=f"{p['k_bb'] - team_k_bb:+.2f} vs team",
            )
            pc7.metric(
                "Strike%", f"{p['strike_pct']:.1f}%",
                delta=f"{p['strike_pct'] - team_strike_pct:+.1f}% vs team",
            )

            fig_cmp = player_vs_team_chart(
                player_name=selected_pitcher,
                player_vals=[
                    p["k_pct"], p["bb_pct"], p["k_bb"], p["strike_pct"]
                ],
                team_vals=[
                    team_k_pct, team_bb_pct, team_k_bb, team_strike_pct
                ],
                metric_labels=["K%", "BB%", "K/BB", "Strike%"],
                title=f"{selected_pitcher} vs Team Average — Key Pitching Metrics",
            )
            st.plotly_chart(fig_cmp, use_container_width=True)

# =============================================================================
# TAB 2 — BATTING
# =============================================================================
with tab_bat:
    st.header("🏏 Batting Performance")

    if batting_filtered.empty:
        # Data limitation notice
        st.markdown(
            '<div class="data-note">'
            "⚠️ <strong>Data Limitation:</strong> "
            "The current <code>dbacks_team_statcast.csv</code> file contains "
            "only D-backs <em>pitching</em> rows (when AZ is in the field). "
            "Batting rows — when D-backs are at bat — are not present in this "
            "export because <code>pybaseball.statcast(team='AZ')</code> "
            "returns pitches <em>thrown by</em> the team, not pitches faced "
            "as batters. To populate this tab, re-fetch or supplement the "
            "dataset to include games where AZ appears as the batting team."
            "</div>",
            unsafe_allow_html=True,
        )
        st.info(
            "Once batting data is available this tab will display:\n\n"
            "- **Volume metrics:** Plate Appearances · At Bats · Games Played\n"
            "- **Performance metrics:** AVG · OBP · Hits · RBI\n"
            "- **Team-level ranking chart** by OBP with team average reference\n"
            "- **Player drill-down** with head-to-head comparison vs team average"
        )
    else:
        if batting_metrics.empty:
            st.warning(
                "No batting metrics could be computed from the filtered data."
            )
        else:
            # ── Team Summary Cards ─────────────────────────────────────────
            st.subheader("📊 Team Summary")

            total_pa = int(batting_metrics["plate_appearances"].sum())
            total_ab = int(batting_metrics["at_bats"].sum())
            total_games_bat = int(batting_filtered["game_pk"].nunique())
            total_hits = int(batting_metrics["hits"].sum())
            total_walks_bat = int(batting_metrics["walks"].sum())
            total_hbp = int(batting_metrics["hbp"].sum())
            total_rbi = int(batting_metrics["rbi"].sum())

            team_avg = total_hits / max(total_ab, 1)
            team_obp = (total_hits + total_walks_bat + total_hbp) / max(total_pa, 1)

            bc1, bc2, bc3, bc4, bc5, bc6, bc7 = st.columns(7)
            bc1.metric("Plate Apps", f"{total_pa:,}")
            bc2.metric("At Bats", f"{total_ab:,}")
            bc3.metric("Games", total_games_bat)
            bc4.metric("AVG", f"{team_avg:.3f}")
            bc5.metric("OBP", f"{team_obp:.3f}")
            bc6.metric("Hits", f"{total_hits:,}")
            bc7.metric("RBI*", f"{total_rbi:,}")
            st.caption(
                "*RBI approximated via the run-score change on each plate appearance."
            )

            st.markdown("---")

            # ── All-Batter Ranking Chart ───────────────────────────────────
            st.subheader("📈 All Batters — Ranked by OBP")

            plot_bat_df = batting_metrics[
                batting_metrics["plate_appearances"] >= 5
            ].copy()
            if len(plot_bat_df) >= 2:
                fig_bat_rank = ranking_bar_chart(
                    df=plot_bat_df,
                    player_col="player_name",
                    metric_col="obp",
                    title="Batters Ranked by On-Base Percentage (OBP)",
                    y_label="OBP",
                    team_avg=team_obp,
                )
                st.plotly_chart(fig_bat_rank, use_container_width=True)

            st.markdown("---")

            # ── Player Drill-Down ──────────────────────────────────────────
            st.subheader("�� Player Drill-Down")

            available_batters = sorted(batting_metrics["player_name"].unique())
            selected_batter = st.selectbox(
                "Select a Batter (MLBAM ID)", available_batters, key="bat_select"
            )

            b_row = batting_metrics[
                batting_metrics["player_name"] == selected_batter
            ]
            if b_row.empty:
                st.warning(f"No data found for batter {selected_batter}.")
            else:
                b = b_row.iloc[0]

                bpc1, bpc2, bpc3, bpc4, bpc5, bpc6, bpc7 = st.columns(7)
                bpc1.metric("PA", int(b["plate_appearances"]))
                bpc2.metric("AB", int(b["at_bats"]))
                bpc3.metric("Games", int(b["games"]))
                bpc4.metric(
                    "AVG", f"{b['avg']:.3f}",
                    delta=f"{b['avg'] - team_avg:+.3f} vs team",
                )
                bpc5.metric(
                    "OBP", f"{b['obp']:.3f}",
                    delta=f"{b['obp'] - team_obp:+.3f} vs team",
                )
                bpc6.metric("Hits", int(b["hits"]))
                bpc7.metric("RBI*", int(b["rbi"]))

                fig_bat_cmp = player_vs_team_chart(
                    player_name=f"Batter {selected_batter}",
                    player_vals=[b["avg"], b["obp"]],
                    team_vals=[team_avg, team_obp],
                    metric_labels=["AVG", "OBP"],
                    title=f"Batter {selected_batter} vs Team Average",
                )
                st.plotly_chart(fig_bat_cmp, use_container_width=True)

# =============================================================================
# TAB 3 — FIELDING
# =============================================================================
with tab_field:
    st.header("🧤 Fielding Performance")

    st.markdown(
        '<div class="data-note">'
        "📌 <strong>Data Note:</strong> Statcast pitch-level data does not "
        "include traditional fielding box-score stats (putouts, assists, "
        "errors). Metrics here are approximated from ball-in-play events "
        "while D-backs are in the field. Individual fielder attribution "
        "requires a MLBAM player-ID lookup table that is not bundled with "
        "this dataset; all metrics below are at the <strong>team level</strong>."
        "</div>",
        unsafe_allow_html=True,
    )

    if not fielding_summary:
        st.warning("No fielding data available for the selected filters.")
    else:
        # ── Team Summary Cards ─────────────────────────────────────────────
        st.subheader("📊 Team Fielding Summary")

        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("Balls in Play", f"{fielding_summary['balls_in_play']:,}")
        fc2.metric(
            "Zone Coverage",
            f"{fielding_summary['zone_coverage_pct']:.1f}%",
            help="% of balls in play within the defined strike zone (zones 1–9)",
        )
        fc3.metric("Outs Recorded", f"{fielding_summary['outs_recorded']:,}")
        fc4.metric(
            "Out Rate",
            f"{fielding_summary['out_rate_pct']:.1f}%",
            help="Fielding outs / balls in play",
        )
        st.caption(
            f"Double plays: {fielding_summary['double_plays']} "
            f"(each counts as 2 outs in the Outs Recorded total)"
        )

        st.markdown("---")

        # ── BIP Type Breakdown ─────────────────────────────────────────────
        bip_data = pitching_filtered[pitching_filtered["is_bip"] == 1].copy()

        if not bip_data.empty and "bb_type" in bip_data.columns:
            st.subheader("⚾ Ball-in-Play Type Distribution")
            bip_types = (
                bip_data["bb_type"].dropna().value_counts().reset_index()
            )
            bip_types.columns = ["BIP Type", "Count"]

            fig_bip = px.pie(
                bip_types,
                values="Count",
                names="BIP Type",
                title="Ball-in-Play Type Distribution (D-backs fielding)",
                color_discrete_sequence=DBACKS_COLORS,
                hole=0.35,
            )
            fig_bip.update_layout(
                height=380,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=DBACKS_TEAL),
            )
            st.plotly_chart(fig_bip, use_container_width=True)

            st.markdown("---")

        # ── BIP Outcome Breakdown ──────────────────────────────────────────
        if not bip_data.empty and "events" in bip_data.columns:
            st.subheader("📊 Ball-in-Play Outcomes")
            bip_outcomes = (
                bip_data["events"].dropna().value_counts().reset_index()
            )
            bip_outcomes.columns = ["Outcome", "Count"]
            bip_outcomes = bip_outcomes.sort_values("Count", ascending=True)

            fig_outcomes = px.bar(
                bip_outcomes,
                x="Count",
                y="Outcome",
                orientation="h",
                title="Fielding Outcomes on Balls in Play",
                color="Count",
                color_continuous_scale=[DBACKS_TEAL, DBACKS_RED],
            )
            fig_outcomes.update_layout(
                height=max(300, len(bip_outcomes) * 28),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=DBACKS_TEAL),
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
            )
            st.plotly_chart(fig_outcomes, use_container_width=True)

            st.markdown("---")

        # ── Zone Coverage Trend ────────────────────────────────────────────
        st.subheader("📅 Zone Coverage Trend (by Game Date)")

        if not bip_data.empty and "game_date" in bip_data.columns:
            zone_trend = (
                bip_data.groupby("game_date")
                .agg(
                    total_bip=("is_bip", "sum"),
                    in_zone_bip=("in_zone", "sum"),
                )
                .reset_index()
            )
            zone_trend["zone_pct"] = (
                zone_trend["in_zone_bip"]
                / zone_trend["total_bip"].replace(0, np.nan)
                * 100
            ).fillna(0)
            zone_trend = zone_trend.sort_values("game_date")

            fig_trend = go.Figure()
            fig_trend.add_trace(
                go.Scatter(
                    x=zone_trend["game_date"],
                    y=zone_trend["zone_pct"],
                    mode="lines+markers",
                    name="Zone Coverage %",
                    line=dict(color=DBACKS_RED, width=2),
                    marker=dict(size=6),
                    hovertemplate=(
                        "%{x|%Y-%m-%d}<br>Zone Coverage: %{y:.1f}%<extra></extra>"
                    ),
                )
            )
            fig_trend.add_hline(
                y=fielding_summary["zone_coverage_pct"],
                line_dash="dash",
                line_color=DBACKS_TEAL,
                annotation_text=(
                    f"Season Avg: {fielding_summary['zone_coverage_pct']:.1f}%"
                ),
                annotation_position="top right",
                annotation_font_color=DBACKS_TEAL,
            )
            fig_trend.update_layout(
                title="Zone Coverage % — Game by Game",
                xaxis_title="Game Date",
                yaxis_title="Zone Coverage %",
                height=380,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=DBACKS_TEAL),
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.15)"),
            )
            st.plotly_chart(fig_trend, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:{DBACKS_RED};'>"
    f"<strong>DbacksAnalytics Pro</strong> &nbsp;|&nbsp; "
    f"Data through {max_date} &nbsp;|&nbsp; "
    f"{len(pitching_data_full):,} total pitches analyzed"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "💡 **Tip:** Use the sidebar to filter by date range and pitcher role."
)
