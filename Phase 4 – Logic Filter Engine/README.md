# Phase 4 – Logic Filter Engine



## Overview



Phase 4 introduces a rule-based filtering engine designed to bridge the gap between raw statistical analysis (Phase 3) and real-world decision-making.



Where earlier phases focus on understanding player distributions and probabilities, this phase focuses on consistently narrowing a large slate of lines into a small, reviewable candidate set using explicit, interpretable rules.



This engine is intentionally conservative. Its goal is not to automate decisions, but to eliminate weak candidates and surface only lines that remain strong across multiple historical lenses.



## Why this phase exists



After building:



- a historical data pipeline (Phase 2), and  

- an interpretability-focused probability app (Phase 3),



a clear problem remained:



Even with good context, evaluating dozens of lines manually every slate does not scale.



Phase 4 formalizes the reasoning process that was already being done mentally:



- checking multiple time windows  

- enforcing consistency across samples  

- filtering out misleading short-term trends  

- rejecting lines that barely clear thresholds  



Instead of trusting intuition alone, this phase encodes minimum standards a line must meet before it is even worth human attention.



## What this engine does



At a high level, the logic filter:



- Ingests player prop lines (from supported sources)

- Maps each line to underlying raw statistics

- Evaluates historical hit rates across:

&nbsp; - last 5 games  

&nbsp; - last 10 games  

&nbsp; - last 25 games (when available)  

&nbsp; - current season

\- Enforces strict percentage thresholds

\- Applies additional rule constraints (e.g., odds filters, line-type rules)

\- Outputs a filtered shortlist of candidate lines



Lines that fail any critical check are discarded.



\## Supported data sources



\### Underdog (Odds API)



Underdog lines are fetched via the Odds API using `Underdog\_lines.py`.



\*\*Requirements:\*\*

\- A valid Odds API key

\- API key supplied via environment variable:



\*\*Output:\*\*

\- `data/underdog\_lines.csv`



This script is intentionally generic and can be extended to support additional sportsbooks exposed by the Odds API.



\### PrizePicks (manual JSON input)



PrizePicks data is \*\*not fetched programmatically\*\*.



Due to platform terms of service, this project does not include automated scraping or API calls for PrizePicks.



Instead:



\- A manually downloaded JSON response is placed in:

&nbsp; - `data/sample\_prizepicks\_api.json`

\- `Prizepicks\_lines\_parser.py` parses this file and produces:

&nbsp; - `data/prizepicks\_lines.csv`



The included JSON file is a sanitized sample intended to demonstrate required structure only.



\## Filtering logic (high level)



For a line to pass:



\- A clear side (Over or Under) must meet the threshold in last 5 games

\- That same side must \*\*not\*\* fall below threshold in:

&nbsp; - last 10 games (if available)

&nbsp; - last 25 games (if available)

\- The current season hit rate must also meet the threshold

\- Unsupported stats are discarded

\- Certain line types (e.g., demon lines) may enforce directional constraints

\- For odds-based books, extreme pricing is filtered out



The default threshold is intentionally strict (e.g., 70%) to reduce noise.



\## Season boundary handling (future update)



Early-season data presents a known problem: sample sizes are too small.



A planned future update introduces controlled carryover logic:



\- Up to 10 games from the end of the previous regular season may be included

\- These games will be:

&nbsp; - explicitly labeled as prior-season data

&nbsp; - used only when current-season games are insufficient

\- Once a player has played 10 games in the new season, all prior-season data is excluded



This prevents misleading confidence early in the season without permanently blending seasons together.



\## Human-in-the-loop validation



Passing the logic filter does \*\*not\*\* mean a line is automatically “good.”



This engine produces a shortlist — not final decisions.



\### In practice, every filtered line is manually reviewed for edge cases such as:



\- recent injury returns or minutes restrictions

\- role changes due to trades or lineup shifts

\- back-to-back scheduling effects

\- late-breaking news not reflected in historical data

\- distributions that technically pass thresholds but still “look wrong”



This final review step is intentional and required.



\## Design philosophy



This phase deliberately avoids:



\- black-box scoring

\- hidden weighting schemes

\- fully automated decision logic



Instead, it prioritizes:



\- transparency

\- repeatability

\- conservative filtering

\- explicit assumptions



A recurring theme across this project is reinforced here:



Models generate signal.  

Rules enforce discipline.  

Humans provide judgment.



\## Outputs



Filtered results are written to the `output/` directory as CSV files suitable for:



\- manual review

\- downstream tooling

\- audit and iteration



No output should be treated as authoritative without review.



\## Limitations



\- Historical hit rates cannot capture all contextual factors

\- Strict thresholds may discard lines that are “close but valid”

\- This engine favors precision over recall

\- Human judgment remains necessary



These tradeoffs are intentional.



\## Final note



Phase 4 formalizes something that emerged naturally during development:



Blind automation is fragile.  

Unstructured intuition does not scale.



This engine exists to sit between those two extremes — and make both better.



