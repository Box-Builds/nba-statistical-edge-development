# NBA Statistical Edge Development



## Executive Summary



This repository documents a multi-phase system built to analyze NBA player prop outcomes using historical data, machine learning, and explicit logic-based filtering.



The project began with a common hypothesis — that comparing sharp sportsbooks to softer DFS markets could reliably identify value — and evolved as that assumption broke down under real-world constraints.



Instead of relying on market pricing alone, the system shifted toward working directly with historical player data, where outcome distributions, variance, and edge cases are fully observable.



At a high level, the system consists of:



Phase 1: An exploratory market-comparison study that identified the limitations of inferring probability from pricing alone



Phase 2: A production-style machine learning pipeline that generates daily NBA player stat predictions in an automated, reproducible environment



Phase 3: A human-facing probability and interpretability app that contextualizes predictions using historical hit rates, distributions, and minutes-based signals



Phase 4: A conservative, rule-based filtering engine that narrows large slates into a small, reviewable candidate set using explicit historical thresholds



A core design principle throughout the project is that models generate signal, but do not make decisions.



Predictions are treated as inputs — not conclusions — and are intentionally passed through interpretability layers, logic filters, and final human review before being considered actionable.



This repository is best understood as a case study in building a real-world decision support system under uncertainty, where transparency, discipline, and judgment matter more than blind automation.



## Overview



This repository documents a multi-phase exploration into building a statistically grounded decision-support system for NBA player props.



Rather than presenting a single algorithm or “edge,” this project captures the evolution of understanding — from early market-based hypotheses to a structured pipeline combining machine learning, interpretability tools, and conservative logic-based filtering.



The end result is not an automated betting system, but a layered framework designed to:



generate signal,



expose uncertainty,



enforce discipline,



and preserve human judgment.



Each phase reflects a distinct shift in thinking, driven by what worked, what failed, and what proved fragile in practice.



## Core philosophy



A central theme emerges across every phase:



Prediction is not decision-making.

Models generate signal.

Rules enforce discipline.

Humans provide judgment.



This repository intentionally avoids black-box automation.

Every component is designed to be inspectable, debuggable, and overridable by a human.



## Project structure



The project is organized into four sequential phases, each building on the insights of the previous one.



NBA\_Statistical\_Edge\_Development/

├── Phase 1 – Market Comparison

├── Phase 2 – ML Prediction Pipeline

├── Phase 3 – Probability \& Interpretability App

└── Phase 4 – Logic Filter Engine



Each phase has its own README explaining:



the question it attempted to answer



what worked and what failed



why the next phase was necessary



This is intentional. The evolution of ideas is as important as the final system.



## Phase summaries



## Phase 1 – Market Comparison



### Question:

Can sharp sportsbooks be used as a proxy for “true probability” and exploited against softer DFS markets?



### Outcome:

Partially informative, but unreliable as a standalone strategy.



### Key insight:

Market prices embed information — but do not expose it.

Relying on lines alone hides variance, distributions, and edge cases.



### Result:

Shift away from pure market comparison toward direct analysis of historical player data.



## Phase 2 – ML Prediction Pipeline



### Question:

Can a machine learning system generate stable, daily NBA player stat predictions under real league conditions?



### What this phase delivers



A production-style, automated ML pipeline

Separate minutes modeling

Stat-specific models

Schedule-aware inference using ghost rows

Reusable daily prediction outputs

## What it does not claim

That predictions alone are sufficient for decision-making.

## Key insight:

Prediction quality improves systemically — but context and risk remain unresolved.



## Phase 3 – Probability & Interpretability App



### Question:

How do we understand whether a prediction is actually trustworthy?



### What this phase adds:


Multi-window hit-rate analysis

Distribution visibility

Minutes context

Season-level breakdowns

Experimental weighted projections (directional only)


## Purpose

Human-facing interpretability, not automation.

## Key insight:

Seeing how often and why outcomes occur matters more than any single predicted value.



This phase exposed failure modes early and repeatedly — often before they propagated downstream.



## Phase 4 – Logic Filter Engine



### Question:

How can we scale disciplined reasoning across a full slate without automating judgment?



### What this phase does

Encodes minimum statistical standards

Enforces consistency across time windows

Filters out misleading short-term trends

Produces a shortlist for human review

### What it explicitly does not do

Make final decisions

Guarantee outcomes

Replace human evaluation

## Key insight:

Structure and restraint matter more than aggressiveness.

### Data & reproducibility notice (important)

This repository does not include:

raw NBA datasets

scraped sportsbook or DFS data

trained model artifacts

real prediction outputs

Why:

NBA data originates from nba.com endpoints

DFS platforms have restrictive terms of service

Redistributing scraped data would be inappropriate

Instead:

Phase 2 provides scripts to generate NBA data locally

Phase 3 and Phase 4 explicitly depend on that locally generated data

PrizePicks inputs are manual by design

Odds API usage requires user-supplied credentials

This keeps the project reproducible without redistributing proprietary data.

## What this project is (and is not)

### This project is

A case study in building a real-world analytical system

A demonstration of disciplined statistical reasoning

An example of production-aware ML design

A framework for decision support

## This project is not:

A betting bot

A guaranteed edge

A plug-and-play strategy

Financial advice

Intended audience

## This repository is best suited for readers interested in

applied machine learning systems

probabilistic reasoning under uncertainty

sports analytics as a modeling problem

human-in-the-loop system design

translating models into real-world decision processes

It is not optimized for beginners or one-click usage.

## Final note

This project exists because confidence without structure is fragile, and automation without understanding is dangerous.

Every phase reflects a step away from naive certainty and toward disciplined skepticism.

That evolution — not any single model or filter — is the real outcome.

