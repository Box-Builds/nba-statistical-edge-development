# Phase 2 – ML Prediction Pipeline



## Overview



This phase represents the core machine learning prediction pipeline used to generate daily NBA player stat predictions in a production-style environment.



Unlike a notebook-based or interactive workflow, this pipeline was designed to run fully automated using GitHub Actions and cloud infrastructure, with a clear separation between data ingestion, model training, and daily inference.



The purpose of this phase was not to build a one-click demo, but to answer a practical systems question:



Can a machine learning system generate stable, reusable NBA player stat predictions on a daily schedule under real league conditions (injuries, trades, role changes, missing data)?



This folder documents how that system was structured, automated, and operated in practice.



## Data & reproducibility notice (important)



This repository does not include raw NBA datasets, processed training tables, trained models, or prediction outputs.



The pipeline relies on historical NBA player game logs, schedules, and rosters originally sourced from nba.com endpoints. To avoid redistributing scraped datasets, all such data is generated locally by the user.



For reproducibility, this phase includes fetch scripts that allow external users to generate the required data on their own machine.



The generated raw game log dataset is intentionally reused across multiple phases of this project:



Phase 2 – ML Prediction Pipeline



Phase 3 – Probability App



Phase 4 – Logic Filter Engine



This ensures all downstream phases operate on a consistent underlying data source.



## What problem was this phase trying to solve?



After determining that market comparison alone was not a reliable long-term edge (Phase 1), this phase focused on independently estimating player outcomes using historical data.



The primary goals were to:



Build models that predict common player stat categories (PTS, REB, AST, FG3M)



Run those models daily with updated data



Produce outputs stable enough to be consumed downstream



Operate in an automated, production-like environment rather than ad hoc scripts



This phase deliberately prioritizes system reliability and structure over model novelty.



## High-level pipeline flow



At a conceptual level, the pipeline operates as follows:



Raw data is generated locally

Player game logs, schedules, and rosters are fetched via standalone scripts.



Minutes are modeled first

A dedicated minutes model predicts expected playing time.



Stat-specific models run

Separate models generate predictions for:



Points



Rebounds



Assists



Three-point makes



Predictions are merged

Individual stat outputs are combined into a unified daily prediction dataset.



Automation executes the process

In production, prediction and merge steps ran on a schedule using GitHub Actions.



This structure mirrors how a real automated system operates rather than an exploratory notebook workflow.



## Local execution (optional)



Although this phase was originally designed to run in a production / serverless environment, the pipeline can be executed locally for transparency and reproducibility.



From this folder:



pip install -r requirements\_pipeline.txt

python run\_local\_fetch.py

python Master.py



run\_local\_fetch.py generates raw NBA data locally



Master.py runs the prediction pipeline assuming required data exists



This local path is provided for reproducibility, not as a polished demo experience.



## Execution context (important)



This folder reflects the production-oriented version of the pipeline.



## Key design assumptions



Data fetching, training, and prediction are logically separated



Fetch scripts exist but are intentionally decoupled from prediction orchestration



Training scripts exist, but trained artifacts are not committed



Master.py orchestrates prediction only and assumes required data already exists



Path resolution is centralized via paths.py to enforce consistent execution



This phase is not intended to be plug-and-play.

It documents how the system was structured and automated under real constraints, not how to maximize ease of use.



## Key design decisions



Explicit minutes modeling



Player minutes were modeled separately and injected into downstream stat models.



This materially improved stability, especially for:



Bench players



Role changes



Players returning from injury



Minutes act as an upstream constraint that limits unrealistic stat projections.



### Stat-specific models



Rather than one monolithic model, each stat category has its own model.



This made it easier to:



Reason about performance



Debug issues



Adapt individual models independently



## Schedule-aware inference with “ghost rows”



A core challenge was generating predictions for future games that do not yet exist in the dataset.



Because models are trained on player–game rows, inference requires a row with the same feature structure. Upcoming games have no box score data and therefore no natural row to predict against.



To solve this, the pipeline introduces ghost rows.



## What is a ghost row?



A ghost row is a synthetic player–game record representing a real upcoming scheduled game that has not yet been played.



### These rows



Correspond to an actual future NBA game



Contain no outcome data



Include only features known prior to the game



### How ghost rows are created



Identify each team’s last completed game



Scan the NBA schedule for the team’s next unplayed game



Expand that game to all rostered players



Populate rows with:



Team and opponent context



Home/away flag and game date



Rolling historical features



Days of rest since last game



### Minutes as an upstream dependency



Ghost rows are merged with predicted minutes:



Minutes are predicted first



Predictions are joined by Player\_ID and GAME\_DATE



Downstream stat models predict conditional on expected playing time



This design allows the system to generate predictions for specific scheduled events without data leakage.



### Practical nuance



Ghost rows are roster-driven, meaning the pipeline may generate rows for players who ultimately do not play (e.g., inactive players, DNPs, or edge cases around trades).



This is intentional.



Rather than attempting to perfectly predict availability at inference time, these cases are handled downstream through minutes behavior, filtering logic, and human sanity checks.



## What worked well



The pipeline ran reliably on a daily schedule



Minutes modeling materially improved downstream predictions



Outputs were stable enough to be consumed by downstream logic



Automation reduced manual intervention and human bias at the prediction stage



## Limitations and where human judgment was required



Cold starts early in the season



Trade-related role changes



Small sample sizes inflating short-term trends



Predictions that were statistically reasonable but contextually misleading



These limitations directly motivated later phases focused on probability interpretation and logic filtering.



## Relationship to later phases



This phase intentionally stops at prediction generation.



Phase 3 focuses on interpreting predictions as probabilities rather than raw point estimates



Phase 4 applies logic-based filtering and human-in-the-loop constraints to convert predictions into actionable decisions



Prediction provides signal — not judgment.



## Key takeaway



A machine learning pipeline can reliably generate daily NBA player stat expectations, but prediction alone is not sufficient for decision-making.



Models provide signal.

Context, risk management, and judgment must exist downstream.



## Final note



This phase is best understood as a production case study, not a tutorial.



It reflects the constraints, compromises, and structure of a real system that ran end-to-end in an automated environment — including the parts that required human judgment outside the model.

