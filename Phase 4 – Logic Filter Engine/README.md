# Phase 4 — Logic Filter Engine

## Overview

Phase 4 introduces a rule-based filtering engine designed to bridge the gap between statistical analysis (Phase 3) and real-world decision-making.

Where earlier phases focus on understanding player distributions and probabilities, this phase focuses on **consistently narrowing a large slate of lines into a small, reviewable candidate set using explicit, interpretable rules.**

The engine is intentionally conservative. Its goal is not to automate decisions, but to eliminate weak candidates and surface only lines that remain strong across multiple historical lenses.

---

# Why This Phase Exists

After building:

- a historical data pipeline (Phase 2)
- an interpretability-focused probability app (Phase 3)

a clear problem remained:

Even with strong context, **manually evaluating dozens of potential lines every slate does not scale.**

Phase 4 formalizes the reasoning process that was previously being done manually:

- checking multiple time windows  
- enforcing consistency across samples  
- filtering out misleading short-term trends  
- rejecting lines that barely clear thresholds  

Instead of relying purely on intuition, this phase encodes **minimum statistical standards** that a line must meet before it is even worth human attention.

---

# What This Engine Does

At a high level, the logic filter:

- ingests player prop lines from supported sources
- maps each line to the underlying player statistics
- evaluates historical hit rates across multiple windows
- enforces strict statistical thresholds
- applies additional rule constraints
- outputs a filtered shortlist of candidate lines

Lines that fail any critical check are discarded.

---

# Supported Data Sources

## Underdog (Odds API)

Underdog lines are fetched using the Odds API via:

```
Underdog_lines.py
```

### Requirements

- a valid Odds API key  
- the key supplied through an environment variable

### Output

```
data/underdog_lines.csv
```


This script is intentionally generic and can be extended to support additional sportsbooks exposed by the Odds API.

---

## PrizePicks (Manual JSON Input)

PrizePicks data is **not fetched programmatically**.

Due to platform terms of service, this project does not include automated scraping or API calls for PrizePicks.

Instead:

- a manually downloaded JSON response is placed in:
```
data/sample_prizepicks_api.json
```

- `Prizepicks_lines_parser.py` converts that file into:

```
data/prizepicks_lines.csv
```

The included JSON file is a sanitized sample used only to demonstrate the required structure.

---

# Filtering Logic (High Level)

For a line to pass the filter:

- A clear side (Over or Under) must meet the threshold in the **last 5 games**
- That same side must **not fall below the threshold** in:
  - last 10 games (if available)
  - last 25 games (if available)
- The **current season hit rate** must also meet the threshold
- Unsupported stat types are discarded
- Certain line types (such as demon lines) may enforce directional constraints
- For odds-based books, extreme pricing is filtered out

The default threshold is intentionally strict (for example, 70%) in order to reduce noise.

---

# Data Dependency

This phase relies on the **historical player game log dataset generated in Phase 2**.

Before running the filtering engine, ensure the dataset has been generated locally:
```
python run_local_fetch.py
```
Then copy the generated file:
```
Phase_2/data/raw/nba_player_game_stats_full.csv
```
into the Phase 4 directory:
```
Phase_4/data/raw/
```
This dataset provides the historical player statistics used to compute hit rates and evaluate candidate lines.

---

# Season Boundary Handling (Planned Update)

Early-season data introduces a known problem: **sample sizes are extremely small.**

A planned update introduces controlled carryover logic:

- Up to **10 games from the end of the previous regular season** may be included
- These games will be:
  - explicitly labeled as prior-season data
  - used only when current-season games are insufficient
- Once a player reaches **10 games in the new season**, all prior-season data will be excluded

This approach avoids misleading early-season signals without permanently blending seasons together.

---

# Human-in-the-Loop Validation

Passing the logic filter **does not mean a line is automatically good.**

The engine produces a **shortlist**, not final decisions.

Each filtered line is manually reviewed for edge cases such as:

- recent injury returns or minutes restrictions
- role changes caused by trades or lineup shifts
- back-to-back scheduling effects
- late-breaking news not reflected in historical data
- distributions that technically pass thresholds but still appear suspicious

This final review step is intentional and required.

---

# Design Philosophy

This phase deliberately avoids:

- black-box scoring systems
- hidden weighting schemes
- fully automated decision logic

Instead it prioritizes:

- transparency
- repeatability
- conservative filtering
- explicit assumptions

A recurring theme across the project is reinforced here:

Models generate signal.  
Rules enforce discipline.  
Humans provide judgment.

---

# Outputs

Filtered results are written to the `output/` directory as CSV files suitable for:

- manual review
- downstream tooling
- auditing and iteration

No output should be treated as authoritative without human review.

---

# Limitations

- historical hit rates cannot capture all contextual factors
- strict thresholds may discard lines that are close but still valid
- the system prioritizes **precision over recall**
- human judgment remains necessary

These tradeoffs are intentional.

---

# Final Note

Phase 4 formalizes a pattern that emerged throughout development.

Pure automation can be fragile when models encounter edge cases or incomplete information.  
At the same time, evaluating every line manually does not scale.

This engine exists to bridge that gap.

It removes weak candidates automatically while leaving final judgment to a human reviewer — combining the consistency of rules with the flexibility of human reasoning.
