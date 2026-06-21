# NBA Statistical Edge Development

## Executive Summary

This repository documents a multi-phase system built to analyze NBA player prop outcomes using historical data, statistical analysis, and rule-based filtering.

The project began with a common hypothesis — that comparing sharp sportsbooks to softer DFS markets could reliably identify value.

However, this assumption broke down under real-world constraints. Market prices embed information but do not expose the underlying distributions or variance that drive player outcomes.

As a result, the project shifted toward **direct analysis of historical player data**.

Over time the system evolved through several approaches, including market comparison and machine learning prediction pipelines. While these approaches provided useful insights, they ultimately proved less reliable than **historical distribution analysis combined with disciplined filtering**.

The final system used in practice relies primarily on:

- historical outcome distributions
- multi-window hit rate analysis
- minutes-based context signals
- conservative rule-based filtering
- human-in-the-loop evaluation

Machine learning predictions were explored as part of the development process but are **not used directly in the final decision workflow**.

Instead, the most reliable signal came from **understanding how outcomes historically occur** and enforcing consistent statistical thresholds before any line is considered for review.

This repository is best understood as a **case study in developing a real-world analytical system under uncertainty**, where iteration, skepticism, and disciplined filtering ultimately proved more valuable than complex models.

---

# Technologies Used

- Python
- Pandas
- NumPy
- Scikit-learn
- Streamlit
- Google Cloud Run
- GitHub Actions
- Google Sheets API
- NBA Stats API
- Sportsbook Odds API

---

# Production Deployment Architecture

The prediction pipeline was fully automated and ran nightly without manual intervention across two separate systems with clearly defined responsibilities.

## Cloud Run — Data Maintenance Layer

A containerized job ran nightly at approximately 10pm PST on Google Cloud Run.

Its sole responsibility was keeping the raw games dataset current:

1. Pulled the existing raw games file from the GitHub repository
2. Fetched newly completed NBA game logs and appended them to the master dataset
3. Ran a deduplication and cleaning pass to remove any duplicate rows
4. Committed the updated raw games file back to the repository

This commit acted as the handoff signal to the next layer.

## GitHub Actions — ML Pipeline Layer

The commit from Cloud Run automatically triggered a GitHub Actions workflow.

That single workflow handled the entire prediction and distribution process in sequence:

1. Built the training dataset from the updated raw games file
2. Trained separate models for each stat category — points, rebounds, assists, and three-point makes
3. Generated **Ghost Rows** — synthetic player–game records representing each player's next scheduled game — so models could run inference on future games with no existing box score data
4. Ran inference across all stat models and combined outputs into a unified daily prediction document
5. Pushed the combined predictions to Google Sheets for access from any device
6. Pushed the updated raw games file to the Phase 3 App repository, overwriting the previous version to keep the Streamlit app current

## Why This Structure

Cloud Run and GitHub Actions were kept as separate systems intentionally.

Cloud Run owns the data — it runs on a fixed schedule regardless of anything else, keeps the dataset clean, and signals downstream when new data is ready.

GitHub Actions owns the ML pipeline — it only runs when there is actually new data to process, triggered by the commit rather than a separate schedule.

This separation means the two layers cannot get out of sync. The pipeline never runs against stale data, and the data layer never needs to know anything about the models.

---

# System Overview

The project is structured as a four-phase progression where each phase reflects a shift in approach based on what worked, what failed, and what proved fragile in practice.

```
NBA_Statistical_Edge_Development/

├── Phase 1 – Market Comparison
├── Phase 2 – ML Prediction Pipeline
├── Phase 3 – Probability & Interpretability App
└── Phase 4 – Logic Filter Engine
```

**Phase 2 generates the historical dataset used by later phases, while Phase 3 and Phase 4 build analytical tools on top of that shared data layer.**

Each phase has its own README explaining:

- the question being investigated
- the methodology used
- what insights were discovered
- why the next phase became necessary

The progression is intentionally preserved because the **evolution of ideas is as important as the final system**.

---

# Core Philosophy

A central theme runs through every phase of the project:

**Prediction is not decision-making.**

Models generate signal.  
Rules enforce discipline.  
Humans provide judgment.

Rather than building a black-box system that attempts to automate decisions, this project focuses on **building transparent analytical tools that assist human reasoning**.

Every component is designed to be:

- interpretable
- inspectable
- debuggable
- overrideable by a human

The goal is not automation — it is **structured decision support**.

---

# Phase Summaries

## Phase 1 — Market Comparison

### Question

Can sharp sportsbooks be used as a proxy for "true probability" and exploited against softer DFS markets?

### Outcome

Partially informative but unreliable as a standalone strategy.

### Key Insight

Market prices contain information, but they **do not expose the distributions behind those prices**. Important context such as variance, minutes volatility, and matchup effects remain hidden.

### Result

Shift toward direct statistical analysis of historical player data.

---

## Phase 2 — ML Prediction Pipeline

### Question

Can a machine learning system generate stable daily NBA player stat predictions under real league conditions?

### What this phase delivers

- fully automated nightly pipeline running on Google Cloud Run and GitHub Actions
- separate minutes modeling
- stat-specific prediction models
- schedule-aware inference using Ghost Rows
- reproducible daily prediction outputs delivered to Google Sheets

### Key Insight

Prediction modeling can improve signal quality but does not resolve the uncertainty inherent in player performance.

While useful for exploration and feature engineering, model predictions alone proved insufficient for reliable decision-making.

---

## Phase 3 — Probability & Interpretability App

### Question

How can we evaluate whether a projected outcome is actually trustworthy?

### What this phase introduces

- multi-window historical hit-rate analysis
- distribution visualization
- minutes context signals
- season-level performance breakdowns
- experimental weighted projections

### Purpose

Expose the historical context surrounding a line rather than relying solely on predictions.

### Key Insight

Understanding **how outcomes occur historically** is often more informative than any single predicted value.

---

## Phase 4 — Logic Filter Engine

### Question

How can disciplined reasoning be scaled across a full slate of potential lines?

### What this phase does

- enforces minimum statistical thresholds
- checks consistency across multiple time windows
- filters misleading short-term trends
- produces a shortlist for human review

### What it intentionally avoids

- making final decisions
- guaranteeing outcomes
- replacing human evaluation

### Key Insight

Consistency and statistical discipline are more valuable than aggressive selection.

This phase ultimately became the **primary practical workflow used in the system**.

---

# Data & Reproducibility Notice

This repository intentionally **does not include**:

- raw NBA datasets
- scraped sportsbook or DFS data
- trained model artifacts
- prediction outputs

Reasons:

- NBA data originates from `nba.com` endpoints
- DFS platforms have restrictive terms of service
- redistributing scraped data would violate platform policies

Instead:

- Phase 2 provides scripts to generate NBA data locally
- Phase 3 and Phase 4 rely on that locally generated dataset
- PrizePicks inputs are intentionally manual
- Odds API usage requires user-supplied credentials

This keeps the project **reproducible without redistributing proprietary datasets**.

The production version of this pipeline — including the Cloud Run container, GitHub Actions workflows, and Google Sheets integration — ran on a separate private repository due to these data constraints. The architecture is documented here in full.

---

# What This Project Is (and Is Not)

### This project is

- a case study in building a real-world analytical system
- an example of production-style ML pipeline development with cloud deployment and CI/CD automation
- a framework for statistical decision support
- a demonstration of disciplined analytical reasoning

### This project is not

- a betting bot
- a guaranteed strategy
- financial advice
- a plug-and-play system

---

# Intended Audience

This repository is best suited for readers interested in:

- applied machine learning systems
- cloud-deployed data pipelines and CI/CD automation
- probabilistic reasoning under uncertainty
- sports analytics as a modeling problem
- human-in-the-loop decision systems

It is **not optimized for beginner tutorials or one-click usage**.

---

# Final Notes

This project evolved through several approaches, many of which initially appeared promising but proved fragile under closer analysis.

Market-based inference, machine learning predictions, and statistical exploration all contributed insights, but the most reliable results ultimately came from disciplined analysis of historical distributions combined with explicit filtering rules.

Rather than attempting to automate decisions, the system now focuses on generating structured context that allows a human to evaluate opportunities more consistently.

The most valuable outcome of this project is not any single model or filter, but the process of iteratively refining ideas under real-world constraints.
