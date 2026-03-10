# Phase 2 — ML Prediction Pipeline

## Overview

This phase represents the core machine learning pipeline built to generate **daily NBA player stat predictions in a production-style environment**.

Unlike a notebook-based workflow, this system was designed to operate as an automated pipeline with clear separation between:

- data ingestion and maintenance  
- model training  
- daily inference  

The system originally ran on a scheduled basis using **GitHub Actions and cloud infrastructure**, allowing predictions to be generated automatically as new NBA data became available.

The goal of this phase was not to create a one-click demo, but to answer a systems-level question:

> Can a machine learning system generate stable, reusable NBA player stat predictions on a daily schedule under real league conditions?

These conditions include injuries, trades, role changes, missing data, and the operational challenge of maintaining the underlying dataset.

---

# Data & Reproducibility Notice

This repository intentionally **does not include**:

- raw NBA datasets  
- processed training tables  
- trained model artifacts  
- prediction outputs  

The pipeline relies on historical NBA data originally sourced from `nba.com` endpoints. To avoid redistributing scraped datasets, the required data must be generated locally after downloading the repository.

This phase includes fetch/update scripts that allow users to:

- generate the historical dataset locally  
- update the master games file with newly completed games  
- rebuild the dataset used by downstream phases  

The generated raw dataset is reused across multiple phases of the project:

- Phase 2 — ML Prediction Pipeline  
- Phase 3 — Probability & Interpretability App  
- Phase 4 — Logic Filter Engine  

This ensures all downstream phases operate on a **consistent underlying data source**.

During execution, the pipeline automatically creates required directories such as:

- `data/raw/`
- `data/processed/`
- `outputs/`

These generated folders are intentionally excluded from version control.

---

# Problem This Phase Addresses

After Phase 1 demonstrated that **market comparison alone was not a reliable long-term edge**, the project shifted toward independently estimating player outcomes using historical data.

The primary goals of this phase were to:

- build models that predict common NBA stat categories  
- run those models on a **daily schedule**  
- produce outputs stable enough to feed downstream systems  
- operate in an **automated, production-style environment**

This phase deliberately prioritizes **system reliability, repeatability, and structure over model novelty**.

---

# High-Level Pipeline Flow

Conceptually, the pipeline operates as follows:

### 1. Raw data generation and maintenance

Historical player game logs, schedules, and rosters are generated locally and updated over time through standalone fetch/update scripts.

### 2. Minutes prediction

A dedicated model predicts expected playing time for each player.

### 3. Stat prediction models

Separate models generate predictions for:

- Points  
- Rebounds  
- Assists  
- Three-point makes  

### 4. Prediction merging

Individual stat outputs are combined into a unified daily prediction dataset.

### 5. Automated execution

In production, the pipeline ran automatically using **GitHub Actions**.

This structure mirrors how real analytical systems operate rather than a typical exploratory notebook workflow.

---

# Local Execution

Although originally designed for automated execution, the pipeline can also be executed locally for transparency and reproducibility.

```text
pip install -r requirements_pipeline.txt
python run_local_fetch.py
python Master.py
'''text

### What these scripts do

**run_local_fetch.py**

Runs the local data-fetch pipeline in the correct order by executing:

- the schedule builder  
- the roster updater  
- the games updater  

It also automatically creates the runtime directories:

- `data/raw/`
- `data/processed/`
- `outputs/`

**Master.py**

Runs the prediction pipeline assuming the required data already exists.

This local execution path is included for reproducibility and inspection rather than as a polished demo workflow.

---

# Important Data Dependency

The dataset generated in this phase is required for later phases of the project.

In particular, the **raw games dataset** produced by the fetch/update scripts is reused by:

- Phase 3 — Probability & Interpretability App  
- Phase 4 — Logic Filter Engine  

These phases assume that the Phase 2 data pipeline has already been executed locally.

---

# Data Maintenance Layer

An important part of this phase was maintaining the **master raw games dataset** over time.

The update scripts were designed to do more than a one-time fetch. They also handled operational tasks such as:

- pulling recent game logs for active players  
- appending only new games to the master dataset  
- backing up the existing raw file before modification  
- repairing season-related fields when needed  
- retrying failed requests  
- tracking players that repeatedly failed to fetch  
- removing duplicate rows using stable player/game keys  

This made the data layer more reliable and reduced the amount of manual cleanup required to keep the pipeline usable over time.

---

# Execution Context

This folder reflects the **production-oriented version of the pipeline**.

Key assumptions include:

- data fetching, updating, training, and prediction are logically separated  
- fetch/update scripts are decoupled from prediction orchestration  
- training scripts exist but trained artifacts are not committed  
- `Master.py` orchestrates prediction assuming required data already exists  
- path resolution is centralized through `paths.py`

This phase is **not intended to be plug-and-play**.

The goal is to document how the system operated under real constraints rather than optimizing for tutorial-style ease of use.

---

# Key Design Decisions

## Explicit Minutes Modeling

Player minutes were modeled separately and injected into downstream stat models.

This significantly improved prediction stability for situations such as:

- bench players  
- role changes  
- players returning from injury  

Minutes act as an upstream constraint that reduces unrealistic stat projections.

---

## Stat-Specific Models

Rather than training a single monolithic model, each stat category has its own model.

This makes it easier to:

- reason about performance  
- debug model behavior  
- adjust models independently  

---

# Schedule-Aware Inference with Ghost Rows

A key challenge was generating predictions for **future games that do not yet exist in the dataset**.

Because models operate on player–game rows, inference requires a row with the same feature structure used during training.

Upcoming games have no box score data, so no natural row exists.

To solve this, the pipeline introduces **ghost rows**.

---

## What is a Ghost Row?

A ghost row is a **synthetic player–game record representing a real upcoming NBA game**.

These rows:

- correspond to a real scheduled game  
- contain no outcome data  
- include only features known prior to the game  

---

## How Ghost Rows Are Created

Ghost rows are generated by:

1. identifying each team’s most recent completed game  
2. locating the team’s next scheduled game  
3. expanding that game across rostered players  
4. populating rows with pre-game features such as:

- opponent information  
- home/away status  
- game date  
- rolling historical statistics  
- days of rest  

---

## Minutes as an Upstream Dependency

Ghost rows are merged with predicted minutes.

The workflow is:

1. minutes are predicted first  
2. predictions are joined by `Player_ID` and `GAME_DATE`  
3. stat models generate predictions conditional on expected playing time  

This allows the system to generate game-specific predictions **without data leakage**.

---

## Practical Nuance

Ghost rows are roster-driven, meaning the pipeline may generate rows for players who ultimately do not play due to:

- inactive status  
- last-minute lineup changes  
- trades or roster edge cases  

This is intentional.

Rather than attempting to perfectly predict availability at inference time, these cases were handled later through filtering logic and human review.

---

# What Worked Well

Several aspects of the pipeline proved effective:

- the system ran reliably on a daily schedule  
- minutes modeling improved downstream prediction stability  
- outputs were stable enough to feed later phases  
- automation reduced manual intervention at the prediction stage  
- the data maintenance scripts helped keep the dataset clean and current  

---

# Limitations

Some limitations remained unavoidable:

- early-season cold starts  
- role changes following trades  
- small sample sizes inflating short-term trends  
- predictions that were statistically reasonable but contextually misleading  
- availability uncertainty that cannot be fully resolved at inference time  

These limitations directly motivated later phases focused on **probability interpretation and logic filtering**.

---

# Train/Test Split Limitation

The current evaluation framework uses a **random train/test split**.

While this is a common default approach in many machine learning workflows, it is not ideal for time-dependent data such as sports performance.

Because player game logs are chronological, random splitting can introduce **temporal leakage**, where future games appear in the training data while earlier games appear in the test set. This can lead to overly optimistic evaluation metrics such as MAE or RMSE.

Importantly, this does **not change the predictions generated by the trained models themselves**. However, it can make model performance appear stronger during evaluation than it truly is when applied in real-world scenarios.

This limitation became apparent when predictions that looked reasonable according to model metrics did not translate into actionable results in practice. Investigating this discrepancy revealed that the evaluation framework was allowing future information to influence model evaluation.

A more appropriate approach would be a **time-based split**, where models are trained on earlier games and evaluated on later games in chronological order.

Future improvements to the pipeline would include time-aware evaluation methods such as chronological splits, rolling-window evaluation, or walk-forward validation to better simulate real-world prediction conditions.

---

# Relationship to Later Phases

This phase intentionally stops at **prediction generation**.

Subsequent phases build on these outputs:

**Phase 3 — Probability & Interpretability App**

Interprets predictions in the context of historical distributions and probability signals.

**Phase 4 — Logic Filter Engine**

Applies rule-based filtering and human-in-the-loop constraints to convert signals into actionable decisions.

Prediction provides signal — not judgment.

---

# Key Takeaway

A machine learning pipeline can reliably generate daily NBA player stat expectations in an automated environment.

However, prediction alone is not sufficient for decision-making.

Models provide signal.  
Context, uncertainty, and human judgment must exist downstream.

---

# Final Note

This phase is best understood as a **production system case study**, not a tutorial.

It reflects the structure, compromises, and operational decisions involved in building a real automated NBA prediction pipeline — including the supporting data maintenance work required to keep that system running over time.
