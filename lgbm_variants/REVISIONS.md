# LightGBM variants: revisions

Every implementation choice the plan (`PLAN.md`, tag `lgbm-variants-plan`) does not name, and every change after a script has run on the backtest. Newest last.

## V5's data, before any fetch (20 November 2026)

1. **New data go in new files; nothing frozen changes.** INDO for March to December 2022 goes to `data/indo_2022.csv`, not into `data/indo.csv`, whose hash is in `data/fetch_manifest.json`. ERA5's half-hourly series for 15 March 2022 to 14 March 2023 goes to its own file, beside the frozen one. `lgbm_variants/v5_data_manifest.json` records both hashes.
2. **Each new file is checked where it meets the frozen data.** INDO's December 2022, held by both files, must agree to the megawatt. The ERA5 series is rebuilt by the backtest's own functions for six days past the join, and must agree with the frozen file to its four decimals. If either check fails, nothing is used.
3. **Gaps are counted, not filled.** The manifest lists every incomplete training day from 15 March to 30 November 2022. V5 drops incomplete days from training, as every forecaster here does.
4. **The ERA5 download reuses `era5_download.py` unchanged,** with its first month moved back to March 2022 at run time. The request, the files, the log and the single-instance lock are the same as the hourly task's.
