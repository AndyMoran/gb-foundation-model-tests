# Checkpoint 0: cost (WP2)

Machine: AMD Ryzen 7 8845HS w/ Radeon 780M Graphics, 8 logical CPUs, 27.4 GB RAM; Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.39. Every forecaster on CPU with 4 threads, one per process, one day per call except where noted below. Times are wall-clock per forecast day, including any daily re-fit; median (range) over the 20 sample days after one untimed warm-up. Memory: peak resident memory of the process, and the part above the memory held once the backtest data had loaded.

| Forecaster | Seconds per day, median (range) | Model load (s) | Peak memory (MB) | Above data (MB) | Matches scored forecasts |
|---|---|---|---|---|---|
| chronos2_A | 1.85 (1.81–2.00) | 2.1 | 1,672 | 545 | yes (max 0.00441 MW) |
| timesfm25_weather | 0.33 (0.33–0.36) | 1.3 | 3,199 | 2,073 | yes (max 0 MW) |
| timesfm25_weather_single | 10.63 (10.34–11.76) | 1.3 | 3,046 | 1,921 | not expected (one day per call; differs by up to 5,643 MW) |
| timestral_A | 7.63 (7.45–7.88) | 1.0 | 2,440 | 1,314 | yes (max 0.00827 MW) |
| timestral_weather | 2.30 (2.21–2.45) | 1.0 | 2,440 | 1,313 | yes (max 0.00781 MW) |
| regression_weather | 0.22 (0.21–0.23) | 0.2 | 1,143 | 15 | yes (max 0 MW) |
| lightgbm_default | 0.36 (0.33–0.56) | 0.2 | 1,141 | 15 | yes (max 0 MW) |
| lightgbm_s1 | 0.62 (0.58–0.84) | 0.2 | 1,140 | 14 | yes (max 0 MW) |
| lightgbm_s2 | 0.60 (0.58–0.74) | 0.2 | 1,142 | 16 | yes (max 0 MW) |

timesfm25_weather is timed inside its scored batches of up to 64 days, per day; timesfm25_weather_single, one day per call. TimesFM fits one covariate regression across every day in a call, so the two give different forecasts; only the batched one reproduces the scored forecasts.

Cost is reported in time and memory only; no £ figure is computed in checkpoint 0 (PLAN.md WP2).
