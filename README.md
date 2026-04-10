# 🏟️ DbacksAnalytics Pro

**Player Performance Dashboard — Arizona Diamondbacks**

A comprehensive baseball analytics platform combining pitching, batting, and
fielding analysis for the Arizona Diamondbacks using real MLB Statcast data.

## ⭐ Features

### Three-Tab Dashboard

| Tab | Focus | Key Metrics |
|-----|-------|-------------|
| ⚾ **Pitching** | Strike out batters, avoid walks | K%, BB%, K/BB, Strike% |
| 🏏 **Batting** | Get on base, drive in runs | AVG, OBP, Hits, RBI |
| 🧤 **Fielding** | Zone coverage, recording outs | BIP, Zone Coverage%, Outs, Out Rate |

### 📊 UX Pattern (all tabs)
1. **Team-level metric cards** at the top showing totals and averages
2. **Ranking bar chart** — all players sorted by the tab's primary metric with a team-average reference line
3. **Player drill-down** — select any player from a dropdown
4. **Comparison chart** — player metrics vs team averages (grouped bar)

### 🎨 Professional Interface
- **D-backs Branding**: Sedona Red (`#A71930`), Sonoran Sand (`#E3D4AD`), Black
- **Interactive Dashboard**: Streamlit-powered with tabbed navigation
- **Sidebar Controls**: Date range filter + pitcher role filter
- **Responsive Design**: Works on desktop and mobile devices

## 🚀 Quick Start

### Prerequisites
```bash
pip install streamlit pandas numpy plotly
```

### Run the Dashboard
```bash
streamlit run dbacks_analytics_pro.py
```

The dashboard will open at `http://localhost:8501`

## 📁 Project Structure

```
dbacks-analysis/
├── dbacks_analytics_pro.py        # Main three-tab dashboard
├── update_dbacks_statcast.py      # Data update utility
├── dbacks_team_statcast.csv       # Statcast dataset (~25k pitches)
├── gallen_contract_analysis.py    # Zac Gallen contract value analysis
├── scout_mcp.py                   # MCP scouting interface
├── launch_dashboard.bat           # Windows quick-launch script
├── README.md                      # This file
├── .copilot-instructions.md       # AI assistant context
└── legacy/                        # Archived dashboard versions
```

## 📊 Dashboard Tabs

### ⚾ Tab 1: Pitching
*D-backs pitchers — when AZ is fielding*

**Volume / Basic Metrics:**
- **Total Pitches** — pitches thrown in the selected period
- **Batters Faced** — plate appearances against D-backs pitchers
- **Games Appeared** — unique game appearances

**Performance Metrics (focus: strikeouts & avoiding walks):**
- **K%** — Strikeout Rate: strikeouts / batters faced × 100
- **BB%** — Walk Rate: walks / batters faced × 100
- **K/BB** — Command quality in a single number
- **Strike%** — Strikes thrown / total pitches × 100

### 🏏 Tab 2: Batting
*D-backs hitters — when AZ is at bat*

> **Data Note:** The current `dbacks_team_statcast.csv` contains only
> D-backs *pitching* rows (pybaseball `statcast(team='AZ')` returns
> pitches thrown *by* the team). This tab is fully implemented and will
> populate automatically once the data source is updated to include
> D-backs batting rows.

**Volume / Basic Metrics:**
- **Plate Appearances** — total PA in the selected period
- **At Bats** — official AB (PA minus walks, HBP, sac flies, etc.)
- **Games Played** — unique games appeared in

**Performance Metrics (focus: getting on base & driving in runs):**
- **AVG** — Batting Average: hits / at bats
- **OBP** — On-Base Percentage: (H + BB + HBP) / plate appearances
- **Hits** — total hits (single + double + triple + HR)
- **RBI** — approximated from post-plate-appearance score change

### 🧤 Tab 3: Fielding
*D-backs fielders — derived from pitching/fielding rows*

> **Data Note:** Statcast pitch-level data does not include traditional
> fielding box-score stats. Individual fielder attribution requires a
> MLBAM player-ID lookup that is not bundled with the dataset; metrics
> here are at the **team level**.

**Team Fielding Metrics:**
- **Balls in Play** — `type == 'X'` events while D-backs are fielding
- **Zone Coverage** — in-zone BIP rate (zones 1–9)
- **Outs Recorded** — out-producing events (double plays count as 2)
- **Out Rate** — outs recorded / balls in play × 100

**Visual Breakdowns:**
- BIP type distribution (ground balls, fly balls, line drives, pop-ups)
- BIP outcome chart (field outs, hits, errors, etc.)
- Zone coverage % trend game-by-game

## 🔧 Data Management

### Update Statcast Data
```bash
python update_dbacks_statcast.py
```

**Features:**
- Smart incremental updates (14-day lookback for corrections)
- Full season refresh capability
- Automatic duplicate detection and removal
- Data validation and backup creation

### Data Coverage
- **Season**: 2025 complete season (March 20 – September 28)
- **Scope**: 24,946+ pitches from all D-backs games
- **Metrics**: Velocity, movement, location, outcomes, and situational data
- **Update Frequency**: Daily during season, weekly during offseason

## ⚙️ Sidebar Filters

| Filter | Applies To | Description |
|--------|-----------|-------------|
| Start Date / End Date | All tabs | Restrict analysis to a date window |
| Pitcher Role | Pitching tab | All / Starters / Relievers / Closers |

## 📚 Key Metrics Explained

| Metric | Formula | Context |
|--------|---------|---------|
| K% | SO / BF × 100 | Higher = more dominant pitcher |
| BB% | BB / BF × 100 | Lower = better command |
| K/BB | SO / BB | >3 considered excellent |
| Strike% | Strikes / Pitches × 100 | >65% is above average |
| AVG | H / AB | Context: MLB avg ~.248 |
| OBP | (H+BB+HBP) / PA | Context: >. 340 is good |

## 🗂️ Legacy Files

Previous dashboard versions are stored in `legacy/`:
- `dbacks_analytics_pro_original.py` — pitching-only dashboard (pre-refactor)
- `dashboard.py` — initial proof-of-concept
- `dashboard_enhanced.py` — enhanced version with more pitch metrics
- `dashboard_improvements.py` — improvement patches

## 🤝 Contributing

This project uses AI-assisted development. See `.copilot-instructions.md`
for context and contribution guidelines.

## 📄 License

Built for Arizona Diamondbacks analysis. Data provided by MLB via pybaseball.

---

**DbacksAnalytics Pro** — *Professional baseball analytics for the Sedona Red and Black* ⚾
