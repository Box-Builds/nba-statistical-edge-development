# Phase 1 — Market Comparison

## Objective

This phase explored whether **sharp sportsbook pricing could act as a better proxy for true outcome probability than DFS-style prop markets**.

The core hypothesis was:

> If a sharp sportsbook prices one side of a player prop as significantly more likely to hit, that side may offer positive expected value when a DFS platform still offers a softer line or fixed payout structure.

At the time, the working assumption was that sharp books were generally **more correct on pricing** than DFS books. If a sharp market heavily favored an over or under, that side was treated as more likely to be the “true” direction of the prop.

The goal of this phase was to test whether those pricing discrepancies could be identified systematically and converted into repeatable EV opportunities.

---

# Methodology

This phase used an automated market scanner to compare NBA player props across one selected sharp sportsbook and multiple DFS-style platforms.

### What the script did

- Pulled upcoming NBA events from an odds API
- Requested multiple player prop markets for each event
- Selected one sportsbook as the **sharp reference market**
- Compared that market against DFS books such as PrizePicks and Underdog
- Matched player props by market, player, and side
- Converted American odds into implied probabilities
- Applied a **no-vig adjustment** to estimate cleaner underlying probabilities
- Compared the sharp line against the DFS line
- Flagged cases where the sharp-favored side appeared more favorable than the DFS offering
- Ranked and exported candidate plays to TXT and CSV reports

### What was being tested

The scanner was designed to answer a simple question:

> When the sharp book prices one side as more likely, and the DFS line or payout structure has not fully adjusted, does that create usable edge?

In practice, the script looked for situations where:

- the sharp book favored an over or under
- the DFS platform offered a line that appeared softer relative to that sharp position
- the estimated no-vig probability suggested positive EV on the sharp-favored side

---

# What Worked (Partially)

This phase produced several useful observations.

**Sharp books do contain meaningful information about market expectations.**

When a sharp market strongly favored one side of a player prop, that often signaled that the side was more likely than a flat DFS payout structure might imply.

The script was also useful for:

- systematically scanning multiple player prop markets
- converting sportsbook prices into implied probabilities
- estimating no-vig probabilities for over/under outcomes
- surfacing discrepancies that would have been difficult to spot manually

In some cases, DFS platforms offered lines or payout structures that made the sharp-favored side appear attractive, especially when those platforms did not dynamically adjust payouts based on implied probability.

---

# Limitations Discovered

Despite promising signals, several important limitations emerged.

### 1. Sharp books are not pure probability engines

Sharp sportsbooks adjust lines in response to both **information and liquidity**.

That means their prices reflect not only expected outcomes, but also market-making behavior, risk balancing, and betting pressure. As a result, the line is not a direct or static measure of “true” probability.

### 2. No-vig probability still depends on market assumptions

The script removed vig from over/under prices to estimate cleaner implied probabilities, but this still depended on the assumption that the sharp book was pricing efficiently enough to serve as a trustworthy baseline.

That assumption was useful, but not fully verifiable from line data alone.

### 3. DFS markets are structurally different

DFS-style prop platforms do not behave like sportsbooks.

They often:

- use fixed payout multipliers
- avoid pricing each outcome independently
- standardize large parts of the user experience across props

Because of this, direct sportsbook-to-DFS comparisons were often noisy and inconsistent.

### 4. The underlying reasoning behind the line is hidden

Even when a sharp line appeared informative, the actual reasoning behind that price was not observable.

The historical data, matchup effects, player-role context, and modeling assumptions embedded in the line were all hidden inside the final market price.

This made it difficult to validate *why* the line looked the way it did.

---

# Key Insight

The biggest takeaway from this phase was that **market prices contain information, but they hide the structure behind that information**.

A sharp sportsbook may price a prop well, but the user cannot directly inspect:

- the historical distributions behind the line
- the variance of the player outcome
- how often similar lines were hit historically
- how matchup or minutes context contributed to the price

By contrast, working directly with historical player data allows those factors to be examined explicitly.

That offered a much more transparent foundation for building a decision-support system.

---

# Key Takeaway

Market comparison was useful as an exploratory framework and as a way to think about implied probability.

However, it proved too indirect and too structurally noisy to serve as a reliable standalone edge.

This phase ultimately led to a shift away from trying to infer truth from pricing alone and toward **direct analysis of historical player data**, where assumptions and context could be made explicit.

---

# What This Phase Led To

The limitations discovered here motivated the next stage of the project:

**Phase 2 — ML Prediction Pipeline**

Instead of treating sportsbook pricing as the primary source of truth, the project shifted toward building predictions directly from historical NBA data and engineered features.

This marked the beginning of a more controlled and transparent analytical pipeline.

---

# Additional Notes

Some exploratory NFL and NHL market-comparison scripts are also included in this phase.

These were early experiments testing whether the same sharp-vs-soft market comparison framework could generalize across multiple sports. They were not developed further once the project shifted toward historical data modeling.
