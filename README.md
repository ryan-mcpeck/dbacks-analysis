# 🏟️ Dbacks Analytics

**Player Performance Dashboard — Arizona Diamondbacks**

Welcome to the Diamondbacks coaching staff! This repository is designed to give you a clean, simple, and intuitive look at player performance without overwhelmingly complicated data.

As your Assistant Coach, this tool is built to help you track the fundamental metrics that drive game-day strategy.

## ⭐ Features

### Three-Tab Dashboard

| Tab | Focus | Basic Metrics to Watch |
|-----|-------|-------------|
| ⚾ **Pitching** | Strike out batters, avoid walks | K% (Strikeouts), BB% (Walks) |
| 🏏 **Batting** | Get on base, drive in runs | AVG (Average), OBP (On-Base) |
| 🧤 **Fielding** | Zone coverage, recording outs | Zone Coverage%, Out Rate |

### 📊 Coaching UX
1. **Team-Level Summaries:** Check the top of any tab to immediately see how the Diamondbacks are doing as a squad.
2. **Rankings:** Quickly see who is performing above the team average (Sedona Red) and who is falling behind (Sonoran Sand).
3. **Player Drill-Down:** Select any individual player to see their head-to-head comparison against the team average.

## 🚀 Quick Start

### Run the Dashboard
Just double-click the `launch_dashboard.bat` file in your folder, or run the following command in your terminal:
```bash
streamlit run dbacks_analytics.py
```
The dashboard will open automatically in your browser at `http://localhost:8501`.

## 📁 Project Structure

```
dbacks-analysis/
├── dbacks_analytics.py            # The main interactive dashboard
├── update_dbacks_statcast.py      # Background utility to fetch fresh MLB data
├── dbacks_team_statcast.csv       # The local database of pitches
├── launch_dashboard.bat           # Easy launch script
├── README.md                      # This file
├── .copilot-instructions.md       # Persona instructions for AI assistants
└── legacy/                        # Archive of complicated/advanced scripts
```

## 🔧 Keeping Data Fresh

As a coach, you generally won't have to worry about this, but to fetch the newest games, you or an assistant can run:
```bash
python update_dbacks_statcast.py
```
This utility automatically detects the latest games and patches the local database so your dashboard is always up to date.

## 📚 Key Metrics Refresher

As you get up to speed with coaching, keep these benchmarks in mind:

| Metric | Focus | Context |
|--------|---------|---------|
| **K% (Strikeouts)** | Pitching dominance | A rate above 20% is solid for most pitchers. |
| **BB% (Walks)** | Pitching command | We want to keep this below 8-9%. Less free bases! |
| **AVG (Average)** | Hitting success | The league average floats around .245. |
| **OBP (On-Base)** | Overall hitting value | Anything above .330 means the player is consistently getting on base. |

---

**Dbacks Analytics** — *Foundational baseball metrics for the Sedona Red and Black* ⚾
