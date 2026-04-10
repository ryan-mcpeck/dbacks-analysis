@echo off
REM DbacksAnalytics Launch Script
REM Quick launcher for the Arizona Diamondbacks pitching analysis dashboard

echo.
echo ⚾ Dbacks Analytics - Arizona Diamondbacks Basic Metrics
echo ================================================
echo.
echo 🚀 Starting baseball analytics dashboard...
echo 📊 Loading 2025 season data (24,946+ pitches)
echo 🎯 Dashboard will open at http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.

cd /d "%~dp0"
streamlit run dbacks_analytics.py

echo.
echo 👋 Dashboard stopped. Thanks for using Dbacks Analytics!
pause