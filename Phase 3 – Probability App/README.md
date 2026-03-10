***# Phase 3 — Probability & Interpretability App

## Overview

This phase introduces an interactive Streamlit app used to analyze NBA player prop outcomes using historical data, hit-rate statistics, and experimental weighted projections.

Unlike Phase 2, which focuses on automated prediction generation, this phase is intentionally **human-facing**. Its purpose is not to automate decisions, but to help a user understand whether a potential player prop outcome is supported by historical data.

The tool focuses on making distributions, sample sizes, and hit rates visible so that predictions and trends can be evaluated more realistically.

---

# How This Phase Started

This phase was not originally planned.

While working on the Phase 2 machine learning pipeline, development slowed down as the system grew more complex. During that process, the idea emerged to build a small interactive app to explore player statistics directly.

The original goal was simple:

> "Can I build a quick app that lets me explore player stats interactively?"

The first version of the app was built in a single day as a side experiment.

However, once it existed, it quickly proved extremely useful for inspecting player distributions and understanding how often specific lines were actually hit.

Over time the tool was expanded with additional features such as:

- weighted projections
- combo stat support
- season-level breakdowns
- average minutes context

What began as a small experiment gradually became a regular part of the workflow.

In practice, the information surfaced by this app often proved more immediately actionable than the raw prediction outputs produced in Phase 2. Being able to inspect distributions, hit rates, and minutes context directly made it easier to evaluate potential outcomes than relying on point predictions alone.

This realization gradually shifted development toward tools that emphasized interpretability and historical outcome analysis rather than prediction outputs by themselves.

---

# What Problem This Phase Solves

Phase 2 produces predictions, but predictions alone do not provide enough context to evaluate a player prop.

In practice, several questions still remained when relying on predictions alone:

- How often does a player actually clear this line?
- Is a recent trend meaningful or just noise?
- Does the long-term distribution support the prediction?
- Are minutes or role changes affecting results?

Answering these questions manually by scanning box scores was slow and error-prone.

This app provides a fast way to explore those signals interactively.

The goal is **interpretation and context**, not automation.

---

# Data Dependency (Important)

This app does **not ship with NBA data**.

It relies on the same raw dataset generated in **Phase 2**.

To run the app locally:

### Step 1 — Generate the dataset in Phase 2
**
```
python run_local_fetch.py
```

### Step 2 — Copy the generated dataset

Copy:

```
Phase_2/data/raw/nba_player_game_stats_full.csv
```
Into:

```
Phase_3/data/raw/
```

### Step 3 — Start the Streamlit app

```
streamlit run app.py
```

If the dataset is missing, the app displays an error explaining the dependency.

This design keeps the repository reproducible without redistributing scraped datasets.

---

# What the App Does

The application allows a user to:

- search for a player
- select a stat category
- input a prop line

It then displays:

- an experimental weighted stat projection
- hit rates over multiple rolling windows
- season-by-season hit rate breakdowns
- full historical distribution
- average minutes for each window

These outputs are designed to be **quickly interpretable**, rather than academically complex.

---

# Supported Stat Types

The app supports both single statistics and combo statistics.

### Single stats

- PTS
- REB
- AST
- TOV
- STL
- BLK
- FG3M

### Combo stats

- PTS + REB
- PTS + AST
- AST + REB
- PTS + REB + AST

Combo stats are calculated dynamically from the underlying game log data.

---

# Weighted Projection System

The app includes an experimental weighted projection designed to provide a rough directional estimate for a player's expected stat output.

The weighting system considers:

- recency (exponential decay)
- minutes played
- selected advanced metrics depending on stat type

A decay parameter (λ) is tuned per player and stat using historical data to minimize prediction error.

This projection is included as **guidance**, not as a decision rule.

---

# Hit Rate Analysis

For a selected stat line, the app calculates hit rates across multiple contexts:

### Rolling windows

- Last 5 games
- Last 10 games
- Last 25 games

Each window shows:

- Over percentage
- Under percentage
- Push percentage
- Raw hit counts
- Average minutes

### Season breakdown

Hit rates are also displayed by NBA season.

### Full dataset

The player's full historical record is summarized as well.

Viewing multiple windows simultaneously helps reveal:

- small-sample inflation
- minutes-driven volatility
- misleading "perfect hit rate" scenarios
- distributions that disagree with projections

---

# Additional Practical Use Cases

Beyond evaluating props, the app also proved useful for:

### Model sanity checks

Comparing model predictions against historical distributions.

### Data integrity checks

Spotting issues such as:

- duplicate rows
- merge errors
- trade-related inconsistencies

### Rapid exploration

Quickly exploring players without writing additional scripts.

---

# What Worked Well

Several aspects of the app proved especially useful:

- extremely fast feedback loop
- clear visibility into sample sizes
- easy comparison across time windows
- strong support for exploratory analysis
- useful early warning system for data issues

---

# Limitations

Historical hit rates alone cannot capture all context.

Examples include:

- defensive matchups
- coaching decisions
- rotation changes
- game script effects

Weighted projections are also **directional estimates**, not probabilistic guarantees.

This tool provides **context**, not automated decisions.

---

# Key Takeaway

This phase introduced a human interpretability layer between raw model outputs and automated filtering.

It reinforced a recurring lesson throughout the project:

Models generate signal.

Humans provide judgment.

This realization directly motivated the logic-based filtering system introduced in **Phase 4**.

---

# Final Note

This app started as a one-day side experiment.

Despite its simple origins, it became a useful tool for understanding player distributions and evaluating predictions more realistically.

Sometimes the most useful tools emerge from small experiments rather than carefully planned systems.
