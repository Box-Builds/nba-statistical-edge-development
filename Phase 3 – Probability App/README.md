# Phase 3 – Probability \& Interpretability App



## Overview



This phase introduces an interactive probability and hit-rate analysis app designed to interpret NBA player prop outcomes using historical data, contextual statistics, and simple weighted projections.



Unlike Phase 2, which focuses on automated prediction generation, this phase is intentionally human-facing. Its purpose is not to automate decisions, but to help a user understand why a prediction might or might not be trustworthy.



Although this app was not originally planned as a formal project phase, it emerged organically during development and proved to be a critical missing layer between raw model outputs and real-world decision-making.



## How this phase came to be



While building and evaluating the machine learning pipeline in Phase 2, a recurring issue became obvious:



Model outputs alone were not enough to confidently evaluate player props.



### In practice, questions kept coming up



Is this prediction supported by historical outcomes?



Is a strong recent trend meaningful, or just small-sample noise?



Does the long-term distribution agree with the model?



Are minutes or role changes distorting the signal?



Answering these questions manually was slow and error-prone.

This app was built as a fast, interactive way to inspect distributions, hit rates, and contextual signals directly.



### What began as a one-day exploratory tool quickly became indispensable.



## What problem this phase solves



Phase 2 produces daily stat predictions, but predictions are still just numbers.

Before using those numbers downstream, they need context.



### This phase focuses on answering



How often does a player actually clear a given line?



How stable is that outcome across different time windows?



Are results being driven by minutes, role changes, or outliers?



Does the data itself look sane?



The goal is clarity, not automation.



## Data dependency (important)



This app does not ship with NBA data.



It relies on the same raw player game log data generated in Phase 2.



### To run this app locally:



In Phase 2, run:



python run\_local\_fetch.py



Copy:



Phase 2/data/raw/nba\_player\_game\_stats\_full.csv



into:



Phase 3/data/raw/



Start the Streamlit app.



If the data file is missing, the app will display a clear error message explaining this dependency.



This design avoids redistributing proprietary datasets while keeping the project fully reproducible.



\## What the app does



The app allows a user to:



Search for a player (supports partial name matching)



Select a stat and input a line (e.g., PTS, 20.0)



View probability-oriented outputs, including:



An experimental weighted stat projection



Hit rates over multiple rolling windows



Season-by-season hit rate breakdowns



Full historical distribution



Average minutes per window for context



The output is designed to be scanned quickly, not analyzed academically.



### Output structure (conceptual)



For a given player and stat line, the app displays:



Weighted projection (experimental, directional only)



Last 5 / 10 / 25 games



Over / Under / Push percentages



Raw hit counts



Average minutes



Season-level hit rates



Full dataset summary



Seeing all of these together makes it easier to identify:



Small-sample inflation



Minutes-driven volatility



Misleading “100% hit rate” scenarios



Distributions that disagree with model output



## Key design decisions



### Use direct historical outcomes (not market prices)



Rather than inferring probability from sportsbook or DFS pricing, this app works directly with player game logs.



### This provides:



Transparent access to outcome distributions



Visibility into variance and outliers



A clearer picture of what outcomes are realistically possible



Markets may encode this information indirectly, but they do not expose it as data.



Multiple time windows to avoid single-window traps



No single time window tells the full story:



Short windows exaggerate hot streaks



Long windows hide recent role changes



Small samples create false certainty



Displaying multiple windows simultaneously encourages reasoning across time rather than trusting one percentage.



### Weighted projection as guidance, not truth



The weighted stat projection is included as an experimental directional signal, not a decision rule.



Its purpose is to:



Provide a rough central tendency



Highlight disagreements between historical distributions and projected output



#### This reinforced a recurring lesson throughout the project



No single number should be trusted in isolation.



## How this phase was used in practice



In practice, this app served three main purposes



### Decision support



A fast way to sanity-check potential plays before committing to them.



### Model validation



A tool for comparing model outputs against real historical distributions.



### Data integrity checks



An early warning system for:



Bad merges



Duplicate rows



Trade-related inconsistencies



Outcomes that “look wrong” when compared to actual game logs



This phase frequently caught issues before they propagated downstream.



## What worked well



Extremely fast feedback loop



Clear visibility into sample sizes and distributions



Reduced reliance on blind trust in model outputs



Effective at catching edge cases and data quality problems



## Limitations



Historical hit rates do not capture full matchup context or coaching decisions



Distributions can still mislead without human judgment



Weighted projections are directional, not probabilistic guarantees



This phase supports decision-making — it does not automate it.



## Key takeaway



This phase added a human-interpretability layer between raw predictions and automated filtering.



It reinforced a core theme of the project:



Models generate signal.

Humans provide judgment.



That realization directly motivated the logic-based filtering system in Phase 4.



## Final note



This app was not originally planned as a formal phase — but it earned its place.



By making model outputs interpretable, inspectable, and grounded in reality, it became a necessary component of the overall system rather than a side experiment.



Sometimes the correct direction only becomes obvious once you start building.

