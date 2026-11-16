# Correction: TimesFM 2.5 with weather, one day per call

| Measure | Published (batched) | Corrected (one day per call) |
|---|---|---|
| Mean daily error with weather (MW) | 1,474 | 1,620 |
| Q1: with / without weather | 0.941 (0.913–0.968), p = 0.0000 | 1.034 (0.999–1.068), p = 0.9465 |
| Q2: gap to NESO closed (MW; share) | 93; 11% | -53; -6% |
| Q3: with weather / regression with weather | 1.453 (1.394–1.510) | 1.597 (1.530–1.662) |
| Q1 without fallback days | 0.943 (0.913–0.974) | 1.043 (1.004–1.080) |
| Q1 on winter days | 0.875 (0.827–0.926) | 0.985 (0.924–1.050) |

Largest difference between the two forecasts on any half-hour: 6,801 MW; median over days of each day's largest difference: 927 MW. Other forecasters' results unchanged: True.

Withdrawn, not rerun: descriptive.q1_timesfm_other_mode; descriptive.q1_unadjusted_inputs.timesfm25; descriptive.q1_decision13_min20.timesfm25; descriptive.q1_decision13_min45.timesfm25; exploratory E1 (release split), E2 (block length), E3: TimesFM 2.5 rows.
