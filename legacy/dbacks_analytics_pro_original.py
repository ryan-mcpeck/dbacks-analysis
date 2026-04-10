#!/usr/bin/env python3
"""
DbacksAnalytics Pro - Advanced Arizona Diamondbacks Pitching Analysis
Fixed Version - Comprehensive Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date

# Set page config
st.set_page_config(
    page_title="DbacksAnalytics Pro",
    page_icon="⚾", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for D-backs branding
st.markdown("""
<style>
.main-header {
    color: #A71930;
    text-align: center;
    padding: 20px 0;
    border-bottom: 3px solid #E3D4AD;
    margin-bottom: 30px;
}
</style>
""", unsafe_allow_html=True)

# Title with D-backs branding
st.markdown('<div class="main-header"><h1>⚾ DbacksAnalytics Pro</h1><h3>Advanced Arizona Diamondbacks Pitching Analysis</h3></div>', unsafe_allow_html=True)

# Enhanced data loading with comprehensive metrics
@st.cache_data
def load_and_enhance_data():
    """Load and enhance the Diamondbacks statcast data with advanced metrics"""
    try:
        data = pd.read_csv('dbacks_team_statcast.csv')
        
        # Convert game_date to datetime
        data['game_date'] = pd.to_datetime(data['game_date'])
        
        # Add derived performance metrics - with safety checks
        if 'type' in data.columns and 'description' in data.columns:
            data['called_strike'] = ((data['type'] == 'S') & (data['description'] == 'called_strike')).astype(int)
            data['swinging_strike'] = ((data['type'] == 'S') & (data['description'] == 'swinging_strike')).astype(int)
            data['whiff'] = data['swinging_strike']
            data['contact'] = ((data['type'] == 'X') | (data['description'].str.contains('foul', na=False))).astype(int)
            data['strike'] = (data['type'] == 'S').astype(int)
            data['ball'] = (data['type'] == 'B').astype(int)
        
        # Zone analysis - with safety checks
        if 'zone' in data.columns:
            data['in_zone'] = (data['zone'] <= 9).astype(int)  # Strike zone pitches
            data['chase'] = ((data['zone'] > 9) & (data['type'] == 'S')).astype(int)  # Swings at pitches outside zone
        else:
            data['in_zone'] = 0
            data['chase'] = 0
        
        return data
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None

def identify_dbacks_pitching(data):
    """Identify when D-backs were pitching with enhanced logic"""
    if data is None:
        return None
    
    try:
        is_dbacks_pitching = (
            ((data['home_team'] == 'AZ') & (data['inning_topbot'] == 'Top')) |
            ((data['away_team'] == 'AZ') & (data['inning_topbot'] == 'Bot'))
        )
        return data[is_dbacks_pitching].copy()
    except Exception as e:
        st.error(f"❌ Error filtering D-backs data: {e}")
        return None

def classify_pitcher_roles(data):
    """Advanced pitcher role classification with error handling"""
    if data is None or len(data) == 0:
        return pd.DataFrame()
    
    try:
        # Required columns check
        required_cols = ['game_pk', 'player_name', 'inning']
        if not all(col in data.columns for col in required_cols):
            st.warning("⚠️ Missing required columns for pitcher role classification")
            return pd.DataFrame()
        
        game_pitcher_stats = data.groupby(['game_pk', 'player_name']).agg({
            'inning': ['min', 'max'],
            'game_pk': 'count'  # Use this for pitch count instead of player_name
        }).reset_index()
        
        game_pitcher_stats.columns = ['game_pk', 'player_name', 'first_inning', 'last_inning', 'total_pitches']
        
        # Enhanced role classification
        game_pitcher_stats['is_starter'] = (
            (game_pitcher_stats['first_inning'] == 1) & 
            (game_pitcher_stats['total_pitches'] >= 50)
        )
        game_pitcher_stats['is_opener'] = (
            (game_pitcher_stats['first_inning'] == 1) & 
            (game_pitcher_stats['total_pitches'] < 50)
        )
        game_pitcher_stats['is_reliever'] = game_pitcher_stats['first_inning'] > 1
        game_pitcher_stats['is_closer'] = (
            (game_pitcher_stats['last_inning'] >= 9) & 
            (game_pitcher_stats['is_reliever'])
        )
        
        # Aggregate role counts per pitcher
        pitcher_roles = game_pitcher_stats.groupby('player_name').agg({
            'is_starter': 'sum',
            'is_opener': 'sum',
            'is_reliever': 'sum', 
            'is_closer': 'sum',
            'total_pitches': 'sum'
        }).reset_index()
        
        # Primary role determination
        def determine_primary_role(row):
            if row['is_starter'] >= 5:  # 5+ starts = starter
                return 'Starter'
            elif row['is_closer'] >= 3:  # 3+ closer appearances = closer
                return 'Closer'
            elif row['is_opener'] >= 3:  # 3+ opener appearances = opener
                return 'Opener'
            elif row['is_reliever'] >= 5:  # 5+ relief appearances = reliever
                return 'Reliever'
            else:
                return 'Utility'  # Mixed role or limited appearances
        
        pitcher_roles['primary_role'] = pitcher_roles.apply(determine_primary_role, axis=1)
        
        return pitcher_roles
    except Exception as e:
        st.error(f"❌ Error in pitcher role classification: {e}")
        return pd.DataFrame()

def calculate_advanced_metrics(data):
    """Calculate comprehensive pitch-level metrics with error handling"""
    if data is None or len(data) == 0:
        return pd.DataFrame()
    
    try:
        # Check for required columns
        if 'player_name' not in data.columns or 'pitch_name' not in data.columns:
            st.warning("⚠️ Missing required columns for metrics calculation")
            return pd.DataFrame()
        
        # Basic aggregation that should always work
        basic_metrics = data.groupby(['player_name', 'pitch_name']).agg({
            'player_name': 'count',  # Total pitches (using player_name count instead)
            'release_speed': 'mean' if 'release_speed' in data.columns else lambda x: 0
        }).reset_index()
        
        basic_metrics.columns = ['player_name', 'pitch_name', 'total_pitches', 'avg_velo']
        
        # Add advanced metrics if columns exist
        if 'strike' in data.columns:
            strike_metrics = data.groupby(['player_name', 'pitch_name'])['strike'].agg(['sum', 'count']).reset_index()
            strike_metrics.columns = ['player_name', 'pitch_name', 'strikes', 'total_thrown']
            basic_metrics = basic_metrics.merge(strike_metrics, on=['player_name', 'pitch_name'], how='left')
            basic_metrics['strike_rate'] = (basic_metrics['strikes'] / basic_metrics['total_thrown'] * 100).round(1)
        else:
            basic_metrics['strike_rate'] = 0
        
        # Calculate usage rate
        basic_metrics['usage_rate'] = (
            basic_metrics['total_pitches'] / 
            basic_metrics.groupby('player_name')['total_pitches'].transform('sum') * 100
        ).round(1)
        
        return basic_metrics
    except Exception as e:
        st.error(f"❌ Error calculating metrics: {e}")
        return pd.DataFrame()

# Load data with progress indicators
st.info("🔄 Loading D-backs data...")

dbacks_data = load_and_enhance_data()
if dbacks_data is not None:
    st.success(f"✅ Raw data loaded: {len(dbacks_data)} total pitches")
    
    dbacks_pitching_data = identify_dbacks_pitching(dbacks_data)
    if dbacks_pitching_data is not None and len(dbacks_pitching_data) > 0:
        st.success(f"✅ D-backs pitching data: {len(dbacks_pitching_data)} pitches")
        
        pitcher_roles = classify_pitcher_roles(dbacks_pitching_data)
        st.success(f"✅ Pitcher roles classified: {len(pitcher_roles)} pitchers")
    else:
        st.error("❌ No D-backs pitching data found")
        st.stop()
else:
    st.error("❌ Failed to load data")
    st.stop()

# Sidebar controls
st.sidebar.title("⚾ Analysis Controls")

# Date range selection
if len(dbacks_pitching_data) > 0:
    min_date = dbacks_pitching_data['game_date'].min().date()
    max_date = dbacks_pitching_data['game_date'].max().date()
    
    st.sidebar.markdown(f"**Data Range**: {min_date} to {max_date}")
    
    start_date = st.sidebar.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )
    
    # Pitcher role filter
    role_filter = st.sidebar.selectbox(
        "Pitcher Role",
        ["All Pitchers", "Starters Only", "Relievers Only", "Closers Only"]
    )
    
    # Filter data by date range
    filtered_data = dbacks_pitching_data[
        (dbacks_pitching_data['game_date'].dt.date >= start_date) &
        (dbacks_pitching_data['game_date'].dt.date <= end_date)
    ]
    
    # Apply role filter
    if role_filter != "All Pitchers" and len(pitcher_roles) > 0:
        if role_filter == "Starters Only":
            relevant_pitchers = pitcher_roles[pitcher_roles['primary_role'] == 'Starter']['player_name'].tolist()
        elif role_filter == "Relievers Only": 
            relevant_pitchers = pitcher_roles[pitcher_roles['primary_role'].isin(['Reliever', 'Opener', 'Utility'])]['player_name'].tolist()
        elif role_filter == "Closers Only":
            relevant_pitchers = pitcher_roles[pitcher_roles['primary_role'] == 'Closer']['player_name'].tolist()
        
        filtered_data = filtered_data[filtered_data['player_name'].isin(relevant_pitchers)]
    
    # Check if we have data
    if filtered_data.empty:
        st.warning("⚠️ No data available for the selected filters. Please adjust your criteria.")
        st.stop()
    
    # Calculate metrics for filtered data
    with st.spinner("📊 Calculating advanced metrics..."):
        pitch_metrics = calculate_advanced_metrics(filtered_data)

# Main dashboard layout with tabs
tab1, tab2, tab3 = st.tabs(["📊 Overview", "⚡ Pitch Analysis", "🎯 Performance"])

# Tab 1: Overview
with tab1:
    st.header("🏟️ Season Overview")
    
    # Key metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    total_pitches = len(filtered_data)
    unique_pitchers = filtered_data['player_name'].nunique()
    
    with col1:
        st.metric("Total Pitches", f"{total_pitches:,}")
    with col2: 
        st.metric("Active Pitchers", unique_pitchers)
    with col3:
        if 'release_speed' in filtered_data.columns:
            avg_velocity = filtered_data['release_speed'].mean()
            st.metric("Avg Velocity", f"{avg_velocity:.1f} mph")
        else:
            st.metric("Avg Velocity", "N/A")
    with col4:
        if 'strike' in filtered_data.columns:
            strike_percentage = (filtered_data['strike'].sum() / total_pitches * 100)
            st.metric("Strike Rate", f"{strike_percentage:.1f}%")
        else:
            st.metric("Strike Rate", "N/A")
    
    # Pitch type distribution
    if 'pitch_name' in filtered_data.columns:
        st.subheader("🎯 Pitch Type Distribution")
        
        pitch_usage = filtered_data['pitch_name'].value_counts()
        
        # D-backs themed colors
        dbacks_colors = ['#A71930', '#E3D4AD', '#000000', '#DBCEAC', '#8B4513', '#B8860B']
        
        fig_usage = px.pie(
            values=pitch_usage.values,
            names=pitch_usage.index,
            title="Overall Pitch Usage",
            color_discrete_sequence=dbacks_colors
        )
        fig_usage.update_layout(height=400)
        st.plotly_chart(fig_usage, use_container_width=True)
    
    # Pitcher role breakdown
    if len(pitcher_roles) > 0:
        st.subheader("👥 Pitching Staff Composition")
        
        role_counts = pitcher_roles['primary_role'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_roles = px.bar(
                x=role_counts.values,
                y=role_counts.index,
                orientation='h',
                title="Pitchers by Role",
                color=role_counts.values,
                color_continuous_scale=['#A71930', '#E3D4AD']
            )
            fig_roles.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_roles, use_container_width=True)
        
        with col2:
            # Role details table
            st.markdown("**Role Definitions:**")
            role_definitions = {
                'Starter': '5+ starts',
                'Closer': '3+ save situations', 
                'Reliever': '5+ relief appearances',
                'Opener': '3+ opening assignments',
                'Utility': 'Mixed role/limited data'
            }
            
            for role, definition in role_definitions.items():
                count = role_counts.get(role, 0)
                st.write(f"**{role}**: {count} pitchers ({definition})")

# Tab 2: Pitch Analysis
with tab2:
    st.header("⚡ Advanced Pitch Analysis")
    
    if len(pitch_metrics) > 0:
        # Pitcher selection
        available_pitchers = sorted(pitch_metrics['player_name'].unique())
        selected_pitcher = st.selectbox("Select Pitcher for Detailed Analysis", available_pitchers)
        
        pitcher_data = pitch_metrics[pitch_metrics['player_name'] == selected_pitcher]
        
        if not pitcher_data.empty:
            # Pitcher summary
            total_pitcher_pitches = pitcher_data['total_pitches'].sum()
            
            st.markdown(f"### {selected_pitcher}")
            st.markdown(f"**Total Pitches Analyzed**: {total_pitcher_pitches:,}")
            
            # Pitch arsenal breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                # Velocity by pitch type
                if 'avg_velo' in pitcher_data.columns:
                    fig_velo = px.bar(
                        pitcher_data,
                        x='pitch_name',
                        y='avg_velo',
                        title=f"{selected_pitcher} - Average Velocity by Pitch Type",
                        color='avg_velo',
                        color_continuous_scale='Reds',
                        text='avg_velo'
                    )
                    fig_velo.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                    fig_velo.update_layout(height=400)
                    st.plotly_chart(fig_velo, use_container_width=True)
            
            with col2:
                # Usage percentage
                if 'usage_rate' in pitcher_data.columns:
                    fig_usage = px.pie(
                        pitcher_data,
                        values='usage_rate',
                        names='pitch_name',
                        title=f"{selected_pitcher} - Pitch Usage %",
                        color_discrete_sequence=dbacks_colors
                    )
                    fig_usage.update_layout(height=400)
                    st.plotly_chart(fig_usage, use_container_width=True)
            
            # Advanced metrics table
            st.subheader("📊 Pitch Metrics")
            display_columns = ['pitch_name', 'total_pitches', 'usage_rate', 'avg_velo']
            if 'strike_rate' in pitcher_data.columns:
                display_columns.append('strike_rate')
            
            available_columns = [col for col in display_columns if col in pitcher_data.columns]
            if available_columns:
                metrics_display = pitcher_data[available_columns].copy()
                st.dataframe(metrics_display, use_container_width=True, hide_index=True)
    else:
        st.warning("No pitch metrics available for the current selection.")

# Tab 3: Performance
with tab3:
    st.header("🎯 Performance Analysis")
    
    if len(pitch_metrics) > 0:
        # Team performance comparison
        team_performance = pitch_metrics.groupby('pitch_name').agg({
            'total_pitches': 'sum',
            'avg_velo': 'mean'
        }).reset_index().sort_values('total_pitches', ascending=False)
        
        if 'strike_rate' in pitch_metrics.columns:
            strike_performance = pitch_metrics.groupby('pitch_name')['strike_rate'].mean().reset_index()
            team_performance = team_performance.merge(strike_performance, on='pitch_name', how='left')
        
        st.subheader("⚾ Team Pitch Performance")
        
        # Performance metrics by pitch type
        col1, col2 = st.columns(2)
        
        with col1:
            if 'avg_velo' in team_performance.columns:
                fig_velo = px.bar(
                    team_performance.head(6),
                    x='pitch_name',
                    y='avg_velo', 
                    title="Average Velocity by Pitch Type",
                    color='avg_velo',
                    color_continuous_scale='RdYlBu',
                    text='avg_velo'
                )
                fig_velo.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                fig_velo.update_layout(height=400)
                st.plotly_chart(fig_velo, use_container_width=True)
        
        with col2:
            if 'strike_rate' in team_performance.columns:
                fig_strike_rate = px.bar(
                    team_performance.head(6),
                    x='pitch_name',
                    y='strike_rate',
                    title="Strike Rate by Pitch Type", 
                    color='strike_rate',
                    color_continuous_scale='RdYlGn',
                    text='strike_rate'
                )
                fig_strike_rate.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_strike_rate.update_layout(height=400)
                st.plotly_chart(fig_strike_rate, use_container_width=True)
        
        # Top performers table
        st.subheader("🏆 Top Pitchers")
        
        pitcher_summary = pitch_metrics.groupby('player_name').agg({
            'total_pitches': 'sum',
            'avg_velo': 'mean'
        }).reset_index().sort_values('total_pitches', ascending=False).head(10)
        
        if 'strike_rate' in pitch_metrics.columns:
            strike_summary = pitch_metrics.groupby('player_name')['strike_rate'].mean().reset_index()
            pitcher_summary = pitcher_summary.merge(strike_summary, on='player_name', how='left')
        
        st.dataframe(pitcher_summary, use_container_width=True, hide_index=True)
    else:
        st.warning("No performance data available for the current selection.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #A71930;'>"
    "<strong>DbacksAnalytics Pro</strong> | "
    f"Data through {max_date} | "
    f"{len(dbacks_pitching_data):,} total pitches analyzed"
    "</div>",
    unsafe_allow_html=True
)

st.markdown("\n💡 **Tip**: Use the sidebar controls to filter data and customize your analysis!")