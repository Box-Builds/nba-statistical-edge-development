\# Phase 1 – Market Comparison



\## What question was this phase trying to answer?



This phase explored whether comparing sharp sportsbooks against softer markets (primarily DFS-style apps) could reliably identify positive expected value (EV) opportunities.



The initial hypothesis was that sharp books, which are heavily bet into and closely tuned, could act as a proxy for “true” probability, while softer markets might lag behind or misprice certain outcomes.



\## What was done in this phase?



Identified sportsbooks that behave as sharp markets (high liquidity, fast-moving lines).



Compared those lines against softer DFS markets that use simplified or standardized payout structures.



Looked for discrepancies where the sharp book strongly favored one side while the DFS market offered that same side under a fixed payout system.



Evaluated whether these discrepancies translated into repeatable EV in practice.



\## What worked (partially)?



Sharp books do contain meaningful information about market expectations.



In certain cases, when a sharp book heavily favored one side and the DFS market reflected that same side, the DFS payout structure (e.g., flat payouts on 2-leg parlays) could amplify value.



These situations were more favorable when the DFS market did not dynamically adjust payouts based on implied probability.



\## What didn’t work (and why)?



Sharp books actively balance their books by adjusting lines in response to liquidity, not solely probability.



Because of this, sharp lines are not static indicators of “true” outcomes.



Direct line comparison was therefore not reliable as a standalone strategy.



Additionally, DFS markets differ fundamentally from sportsbooks:



They do not price individual outcomes independently.



Their payout structures vary by platform and format.



These structural differences introduced noise and inconsistency into pure market-comparison approaches.



\## Key insight from this phase



One major limitation of relying on sportsbook lines is that the underlying data and reasoning used to set those lines is not directly observable.



While sharp books almost certainly incorporate historical performance, matchup context, and other signals, that information is embedded in the line itself rather than exposed as data.



In contrast, direct historical player data provides transparent access to:



actual outcome distributions



variance and edge cases



how often specific lines are realistically hit or missed



This realization highlighted that working directly with historical data offers more control, interpretability, and flexibility than attempting to reverse-engineer market pricing alone.



\## Key takeaway



Market comparison can provide useful context, but direct analysis of historical data is a more reliable foundation for understanding player outcome probabilities.



This insight led to a shift away from pure market-based strategies and toward independent statistical modeling, where assumptions and inputs are explicit rather than implicit.



\## What would be improved or explored next?



Using market data as a contextual signal rather than a primary decision driver.



Explicitly modeling historical outcome distributions instead of inferring probability from pricing.



Combining market context with model-based predictions rather than relying on line discrepancies alone.

