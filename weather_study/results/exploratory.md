# Exploratory analyses of the backtest (not in the plan)

## E1: before and after each model's release (Q1 ratio)

- Chronos-2, released 2025-10-30: before 0.695 (0.663–0.729; p 0.0000; 593 days); after 0.664 (0.631–0.703; p 0.0000; 367 days)
- Timestral, released 2026-10-15: before 0.775 (0.753–0.798; p 0.0000; 943 days); after 0.693 (0.528–0.721; p 0.0000; 17 days)
- TimesFM 2.5, released 2025-09-15: before 0.935 (0.895–0.974; p 0.0050; 548 days); after 0.948 (0.910–0.987; p 0.0160; 412 days)

## E2: bootstrap block length (Q1 ratio, 90% interval, p)

- 7-day blocks: Chronos-2 0.683 (0.658–0.707; p 0.0000; 960 days); Timestral 0.773 (0.751–0.796; p 0.0000; 960 days); TimesFM 2.5 0.941 (0.913–0.968; p 0.0000; 960 days); Regression 0.658 (0.631–0.686; p 0.0000; 960 days)
- 14-day blocks: Chronos-2 0.683 (0.659–0.708; p 0.0000; 960 days); Timestral 0.773 (0.749–0.799; p 0.0000; 960 days); TimesFM 2.5 0.941 (0.907–0.973; p 0.0010; 960 days); Regression 0.658 (0.629–0.688; p 0.0000; 960 days)
- 28-day blocks: Chronos-2 0.683 (0.657–0.710; p 0.0000; 960 days); Timestral 0.773 (0.744–0.802; p 0.0000; 960 days); TimesFM 2.5 0.941 (0.903–0.975; p 0.0025; 960 days); Regression 0.658 (0.622–0.693; p 0.0000; 960 days)

## E3: the regression with its ECMWF inputs on ERA5's scale

- Mean daily error 1,015.8 MW, against 1,014.4 MW as scored; ratio 1.001 (0.995–1.008; p 0.6370; 960 days)
- Q1 for this regression: 0.659 (0.632–0.686; p 0.0000; 960 days)
- Q3, Chronos-2 ÷ this regression: 0.965 (0.928–1.001; p 0.0535; 960 days)
- Q3, Timestral ÷ this regression: 1.072 (1.033–1.114; p 1.0000; 960 days)
- Q3, TimesFM 2.5 ÷ this regression: 1.451 (1.392–1.510; p 1.0000; 960 days)

## E4: calendar (added 12 November 2026, after publication)

Ordinary days: all but 35 bank-holiday and 24 December to 2 January days.

| Error ÷ regression's | All days, without weather | All days, with | Ordinary days, without | Ordinary days, with |
| --- | --- | --- | --- | --- |
| Chronos-2 | 0.932 (0.904–0.959) | 0.966 (0.931–1.001) | 0.924 (0.897–0.951) | 0.940 (0.907–0.971) |
| Timestral | 0.914 (0.889–0.941) | 1.074 (1.034–1.115) | 0.904 (0.879–0.928) | 1.055 (1.017–1.092) |
| TimesFM 2.5 | 1.017 (0.983–1.052) | 1.453 (1.394–1.510) | 1.018 (0.986–1.050) | 1.455 (1.397–1.515) |

| Q1 on ordinary days | Ratio (90% interval) | Mean error on excluded days, without → with weather (MW) |
| --- | --- | --- |
| Chronos-2 | 0.670 (0.648–0.693) | 2,551 → 2,194 |
| Timestral | 0.768 (0.746–0.791) | 2,573 → 2,159 |
| TimesFM 2.5 | 0.942 (0.913–0.972) | 2,376 → 2,175 |
| Regression | 0.659 (0.632–0.686) | 2,372 → 1,541 |
