# Tails: who fails on the coldest days?

Andy Moran (Heaviside Analytics) · draft, 17 November 2026 · a backtest study, descriptive

For: a reader who wants to know whether average error hides how accurate forecasters are on the coldest days, when demand peaks, margins are tightest and an error costs most.

**What this does not show.**
- **Live performance.** The foundation models may have seen these days in training.
- **A cold-day effect apart from a winter effect,** except where the comparison with other days of the same months shows one.
- **A ranking.** 96 cold days from two winters cannot settle who is best.
- **Prices or profit.** The study scores demand forecasts, one input to price.
- **Other series, horizons or countries.** It covers GB national demand (INDO), a day ahead.

## Headline

In a backtest Chronos-2 may have seen in training, it did not clearly lose or gain ground against a weather regression on the coldest tenth of days, compared with other days of the same months (tail shift 1.055, 90% interval 0.915–1.213).

On the coldest tenth of days in a 960-day backtest, LightGBM did not clearly lose or gain ground against a weather regression, compared with other days of the same months (tail shift 1.102, 90% interval 0.988–1.217).

H1 was unclear: LightGBM S1 lost ground against all other days but not clearly against other days of the same months: a winter effect, not a cold-day effect. The T4 clause was not assessed: no scored day had a forecast temperature below the lowest in LightGBM's training rows, so T4 is empty.

The plan's rules chose these three sentences, and the scoring script wrote them before anyone read the tables (`PLAN.md` §7–8).

**What this does show.** A *tail shift* compares how a forecaster fares against the weather regression on the 96 coldest days with how it fares on other days. Above 1, it does relatively worse on cold days.
- **LightGBM's gap is a winter gap.** Against all other days, LightGBM S1 clearly lost ground (tail shift 1.187, 90% interval 1.066–1.298). Against other days of the same months, it did not clearly lose ground (1.102, 0.988–1.217). On those days it was already 10.5% worse than the regression (ratio 1.105, 1.056–1.150), so most of its cold-day gap was present on ordinary winter days.
- **TimesFM 2.5 lost ground on cold days,** against other days of the same months (1.302, 1.117–1.533).
- **Chronos-2 neither clearly lost nor gained ground** (1.055, 0.915–1.213), but it under-forecast the daily peak by 511 MW (195 to 837).

## What was compared

The backtest covers the weather study's 960 days, 16 March 2024 to 31 October 2026. The study made no new forecasts. It scores the saved forecasts from the weather study and checkpoint 0, checked against their hashes (`PLAN.md` §4).

The compared forecasters had the same weather and calendar. NESO's forecast appears as a reference only, because NESO had more information. Error is outturn minus forecast, in MW, so a positive bias means under-forecast.

**Choosing the cold days.** T1 holds the 96 days with the lowest mean forecast temperature. That is the national 2 m temperature the regression received, from the forecast public at 09:30 the day before. The days were chosen from that forecast alone and written down before any error was computed. Choosing days by what demand turned out to be can make a skilful forecast look poor (Lerch et al., 2017).

**Measuring the shift.** A day's error is its mean absolute error over its half-hours; mean daily error averages that over days. Divide a forecaster's mean daily error by the regression's on the cold days, and again on the comparison days. The tail shift is the first ratio over the second.

**Two sets of comparison days.**
- **Same months (narrow):** the other 175 days in the 9 months that hold a cold day. They help tell a cold-day pattern from a winter one, and the headlines use them.
- **All other days (broad):** 864 days. They mix the two.

Intervals are 90%, from a moving-block bootstrap over days (blocks of 7, 2,000 draws, seed 20261117). A forecaster loses or gains ground only where the interval excludes 1. An interval that includes 1 means the study cannot tell; it does not mean the forecasters performed the same.

## Results on the coldest tenth of days (T1)

| Forecaster | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th percentile (MW) |
|---|---|---|---|---|---|---|---|---|
| Weather regression | 1,025 | 1 | 1 | 1 | −178 (−358 to 6) | −134 (−357 to 91) | 2025-12-25: 2,968 | 2,717 |
| Chronos-2 | 968 | 0.944 (0.841–1.039) | 1.055 (0.915–1.213) | 1.051 (0.932–1.166) | 170 (−16 to 352) | 511 (195 to 837) | 2025-12-25: 3,690 | 2,729 |
| TimesFM 2.5 (one day per call) | 2,075 | 2.024 (1.758–2.359) | 1.302 (1.117–1.533) | 1.307 (1.138–1.521) | 468 (−58 to 1,004) | 861 (198 to 1,539) | 2024-11-19: 6,100 | 6,461 |
| LightGBM, S1 settings | 1,249 | 1.218 (1.097–1.330) | 1.102 (0.988–1.217) | 1.187 (1.066–1.298) | 49 (−288 to 357) | 349 (−65 to 741) | 2025-12-25: 4,577 | 3,654 |
| LightGBM, defaults (sensitivity) | 1,384 | 1.350 (1.197–1.504) | 1.124 (0.995–1.257) | 1.236 (1.095–1.381) | 70 (−316 to 437) | 476 (13 to 917) | 2025-12-25: 5,123 | 3,960 |
| LightGBM, S2 settings (sensitivity) | 1,313 | 1.281 (1.147–1.413) | 1.121 (0.999–1.245) | 1.213 (1.084–1.340) | 63 (−298 to 392) | 444 (−4 to 864) | 2025-12-25: 5,210 | 3,865 |
| Timestral (shown, not compared) | 1,475 | 1.439 (1.229–1.656) | 1.431 (1.212–1.679) | 1.374 (1.174–1.586) | 589 (246 to 935) | 862 (378 to 1,372) | 2026-01-05: 5,306 | 4,331 |
| NESO day-ahead (reference) | 739 | 0.721 (0.647–0.805) | 1.111 (0.964–1.282) | 1.049 (0.939–1.181) | 45 (−71 to 168) | 130 (−51 to 328) | 2024-11-19: 1,763 | 2,024 |

Comparison days, T1: 175 in the same months, 864 in all.

| Forecaster | Ratio, same months | Ratio, all other days | Bias, same months (MW) | Bias, all other days (MW) |
|---|---|---|---|---|
| Weather regression | 1 | 1 | 145 (−57 to 339) | −88 (−164 to −14) |
| Chronos-2 | 0.895 (0.817–0.978) | 0.898 (0.867–0.931) | −380 (−514 to −257) | −137 (−191 to −75) |
| TimesFM 2.5 (one day per call) | 1.554 (1.403–1.718) | 1.549 (1.488–1.607) | −458 (−753 to −182) | −14 (−144 to 116) |
| LightGBM, S1 settings | 1.105 (1.056–1.150) | 1.026 (1.004–1.046) | −64 (−289 to 151) | −72 (−150 to 7) |
| LightGBM, defaults (sensitivity) | 1.201 (1.138–1.260) | 1.092 (1.065–1.117) | −123 (−381 to 123) | −83 (−167 to 2) |
| LightGBM, S2 settings (sensitivity) | 1.143 (1.086–1.195) | 1.056 (1.032–1.079) | −104 (−348 to 133) | −79 (−163 to 4) |
| Timestral (shown, not compared) | 1.006 (0.917–1.097) | 1.048 (1.014–1.083) | −17 (−179 to 143) | 67 (−3 to 139) |
| NESO day-ahead (reference) | 0.649 (0.592–0.714) | 0.687 (0.664–0.708) | −76 (−157 to 5) | −11 (−51 to 30) |

Peak error is the day's highest outturn half-hour minus the forecaster's highest forecast half-hour, wherever each falls.

**Chronos-2 under-forecast the daily peak on cold days,** by 511 MW (195 to 837), though its overall bias was not clearly different from zero. On other days of the same months it over-forecast, by 380 MW (257 to 514). This fits a flatter forecast profile on cold days, but the study measured the peak and the bias, not the profile.

**All three LightGBM settings agree.** The defaults and S2, run as sensitivity checks, have same-month tail shifts of 1.124 (0.995–1.257) and 1.121 (0.999–1.245). Like S1's, each interval just reaches 1. Against all other days, both clearly lost ground: 1.236 (1.095–1.381) and 1.213 (1.084–1.340).

**References.** NESO's error on cold days was 28% below the regression's (ratio 0.721), and its tail shifts include 1: 1.111 (0.964–1.282) against the same months. Timestral is shown but not compared, because a known defect affects its calendar input (`mistralai/timestral#9`). It lost ground: 1.431 (1.212–1.679).

## H1: does LightGBM fail on cold days because it cannot extrapolate?

The hypothesis, fixed before any tail error was computed: LightGBM S1 loses ground on the coldest days and under-forecasts them, because a tree predicts only values it has seen.

| Condition on T1 | Result |
|---|---|
| Tail shift against other days of the same months above 1 | 1.102 (0.988–1.217): not clearly |
| Tail shift against all other days above 1 | 1.187 (1.066–1.298): yes |
| Bias above 0 | 49 MW (−288 to 357): not clearly |
| Peak error above 0 | 349 MW (−65 to 741): not clearly |

By the plan's rule, this is **a winter effect, not a cold-day effect**.

**The mechanism test had nothing to test.** T4 was to hold the days on which a forecast temperature fell below the coldest in LightGBM's training data. It is empty: LightGBM never received a temperature colder than it had trained on. It came closest on 6 January 2026, when its coldest forecast half-hour was 0.40 °C above its training minimum. Whatever causes LightGBM's winter gap, it is not temperatures outside its training range. That undercuts H1's stated reason; the study does not test what does cause the gap.

## Other day sets

These sets were planned as secondary or sensitivity checks, and their results are descriptive. Their tables follow this section.

**Coldest half-hour (T1b, sensitivity).** Choosing the 96 days by their coldest forecast half-hour gives the same picture. Same-month tail shifts: LightGBM S1 1.102 (0.993–1.225), TimesFM 2.5 1.173 (1.024–1.331), Chronos-2 0.994 (0.858–1.134).

**NESO's highest forecast peaks (T2).** On these 96 days, no compared forecaster clearly lost ground against other days of the same months. Most forecasters under-forecast both demand and the daily peak:
- the regression: 272 MW (115 to 451); peak 218 MW (26 to 422);
- Chronos-2: 170 MW (5 to 347); peak 405 MW (177 to 639);
- LightGBM S1: 365 MW (155 to 601); peak 644 MW (394 to 902); the other two settings likewise;
- Timestral: 684 MW (455 to 932); peak 751 MW (450 to 1,056).

TimesFM 2.5's bias and peak error include 0. NESO over-forecast its own peak, by 178 MW (17 to 347).

**Holidays (T3).** This calendar set is kept out of the cold-day reading. On the 35 bank holidays and days from 24 December to 2 January:
- Chronos-2 lost ground against other days of the same months (tail shift 1.375, 1.166–1.703), and over-forecast demand by 929 MW (484 to 1,582).
- LightGBM S1 lost ground: 1.135 (1.022–1.239).
- NESO gained ground: 0.789 (0.686–0.956).

## Tables for the other sets

Each set has two tables: the set, then its comparison days. Intervals are 90%. T4 is empty, so it has none. `results.md` and `results.json` hold every figure the script computed.

### T1b: the coldest 10% by coldest forecast half-hour (sensitivity)

| Forecaster | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th percentile (MW) |
|---|---|---|---|---|---|---|---|---|
| Weather regression | 1,101 | 1 | 1 | 1 | −297 (−522 to −76) | −202 (−465 to 50) | 2025-12-25: 2,968 | 2,969 |
| Chronos-2 | 1,012 | 0.920 (0.820–1.021) | 0.994 (0.858–1.134) | 1.022 (0.904–1.143) | 72 (−132 to 261) | 380 (31 to 719) | 2025-12-25: 3,690 | 2,867 |
| TimesFM 2.5 (one day per call) | 2,084 | 1.894 (1.658–2.151) | 1.173 (1.024–1.331) | 1.213 (1.066–1.376) | 297 (−283 to 867) | 734 (28 to 1,430) | 2024-11-19: 6,100 | 6,710 |
| LightGBM, S1 settings | 1,329 | 1.208 (1.092–1.326) | 1.102 (0.993–1.225) | 1.177 (1.065–1.295) | −26 (−402 to 323) | 234 (−235 to 683) | 2025-12-25: 4,577 | 3,904 |
| LightGBM, defaults (sensitivity) | 1,468 | 1.333 (1.184–1.486) | 1.133 (1.002–1.278) | 1.221 (1.084–1.367) | −5 (−449 to 417) | 364 (−163 to 871) | 2025-12-25: 5,123 | 4,331 |
| LightGBM, S2 settings (sensitivity) | 1,388 | 1.262 (1.132–1.399) | 1.115 (0.992–1.252) | 1.194 (1.068–1.329) | −25 (−436 to 357) | 312 (−190 to 786) | 2025-12-25: 5,210 | 4,139 |
| Timestral (shown, not compared) | 1,490 | 1.353 (1.130–1.588) | 1.258 (1.031–1.511) | 1.283 (1.069–1.517) | 507 (141 to 886) | 809 (311 to 1,337) | 2026-01-05: 5,306 | 4,532 |
| NESO day-ahead (reference) | 760 | 0.690 (0.626–0.762) | 0.963 (0.859–1.076) | 1.000 (0.904–1.108) | 20 (−93 to 147) | 44 (−149 to 238) | 2025-03-05: 2,989 | 2,090 |

Comparison days, T1b: 221 in the same months, 864 in all.

| Forecaster | Ratio, same months | Ratio, all other days | Bias, same months (MW) | Bias, all other days (MW) |
|---|---|---|---|---|
| Weather regression | 1 | 1 | 43 (−126 to 204) | −75 (−151 to −3) |
| Chronos-2 | 0.925 (0.854–1.008) | 0.900 (0.868–0.934) | −237 (−349 to −129) | −126 (−181 to −67) |
| TimesFM 2.5 (one day per call) | 1.614 (1.498–1.753) | 1.561 (1.498–1.621) | −332 (−561 to −116) | 5 (−122 to 132) |
| LightGBM, S1 settings | 1.096 (1.057–1.136) | 1.026 (1.004–1.046) | −5 (−172 to 147) | −64 (−143 to 11) |
| LightGBM, defaults (sensitivity) | 1.177 (1.126–1.230) | 1.092 (1.065–1.117) | −32 (−212 to 135) | −75 (−160 to 6) |
| LightGBM, S2 settings (sensitivity) | 1.131 (1.087–1.179) | 1.057 (1.032–1.079) | −15 (−188 to 147) | −69 (−152 to 9) |
| Timestral (shown, not compared) | 1.076 (1.002–1.158) | 1.055 (1.020–1.091) | 38 (−94 to 168) | 76 (7 to 149) |
| NESO day-ahead (reference) | 0.717 (0.665–0.772) | 0.690 (0.667–0.713) | −40 (−127 to 43) | −8 (−48 to 33) |

### T2: the top 10% by NESO's forecast peak (secondary)

| Forecaster | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th percentile (MW) |
|---|---|---|---|---|---|---|---|---|
| Weather regression | 940 | 1 | 1 | 1 | 272 (115 to 451) | 218 (26 to 422) | 2025-12-15: 2,528 | 2,252 |
| Chronos-2 | 870 | 0.926 (0.811–1.047) | 0.981 (0.842–1.141) | 1.028 (0.899–1.172) | 170 (5 to 347) | 405 (177 to 639) | 2026-01-05: 2,493 | 2,370 |
| TimesFM 2.5 (one day per call) | 1,747 | 1.858 (1.547–2.235) | 1.142 (0.938–1.385) | 1.183 (0.988–1.428) | 445 (−8 to 951) | 519 (−89 to 1,189) | 2024-11-19: 6,100 | 5,596 |
| LightGBM, S1 settings | 1,079 | 1.148 (1.034–1.270) | 0.997 (0.892–1.108) | 1.109 (0.997–1.230) | 365 (155 to 601) | 644 (394 to 902) | 2025-01-08: 3,845 | 2,868 |
| LightGBM, defaults (sensitivity) | 1,209 | 1.286 (1.123–1.459) | 1.030 (0.900–1.177) | 1.168 (1.024–1.328) | 387 (123 to 680) | 816 (532 to 1,107) | 2025-01-08: 4,321 | 3,202 |
| LightGBM, S2 settings (sensitivity) | 1,138 | 1.211 (1.079–1.354) | 1.016 (0.901–1.143) | 1.136 (1.011–1.273) | 362 (123 to 620) | 715 (456 to 984) | 2025-01-08: 4,084 | 2,990 |
| Timestral (shown, not compared) | 1,222 | 1.299 (1.063–1.542) | 1.145 (0.935–1.372) | 1.219 (1.004–1.451) | 684 (455 to 932) | 751 (450 to 1,056) | 2026-01-05: 5,306 | 3,503 |
| NESO day-ahead (reference) | 674 | 0.717 (0.629–0.818) | 1.143 (0.978–1.331) | 1.043 (0.915–1.193) | −79 (−191 to 40) | −178 (−347 to −17) | 2024-11-19: 1,763 | 1,779 |

Comparison days, T2: 144 in the same months, 864 in all.

| Forecaster | Ratio, same months | Ratio, all other days | Bias, same months (MW) | Bias, all other days (MW) |
|---|---|---|---|---|
| Weather regression | 1 | 1 | 67 (−143 to 254) | −138 (−212 to −67) |
| Chronos-2 | 0.944 (0.862–1.030) | 0.900 (0.869–0.933) | −402 (−567 to −244) | −137 (−192 to −74) |
| TimesFM 2.5 (one day per call) | 1.627 (1.463–1.813) | 1.570 (1.510–1.627) | −403 (−757 to −62) | −11 (−147 to 120) |
| LightGBM, S1 settings | 1.152 (1.099–1.204) | 1.035 (1.013–1.056) | −106 (−374 to 139) | −107 (−188 to −29) |
| LightGBM, defaults (sensitivity) | 1.248 (1.182–1.316) | 1.101 (1.075–1.127) | −165 (−464 to 120) | −118 (−208 to −33) |
| LightGBM, S2 settings (sensitivity) | 1.192 (1.128–1.258) | 1.066 (1.042–1.089) | −134 (−420 to 131) | −112 (−198 to −30) |
| Timestral (shown, not compared) | 1.134 (1.029–1.245) | 1.066 (1.031–1.103) | −60 (−304 to 184) | 56 (−17 to 135) |
| NESO day-ahead (reference) | 0.627 (0.574–0.690) | 0.688 (0.665–0.708) | 31 (−58 to 124) | 3 (−36 to 45) |

### T3: bank holidays and 24 December to 2 January (calendar)

| Forecaster | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th percentile (MW) |
|---|---|---|---|---|---|---|---|---|
| Weather regression | 1,541 | 1 | 1 | 1 | −200 (−538 to 196) | 46 (−423 to 537) | 2025-12-28: 3,130 | 4,259 |
| Chronos-2 | 1,828 | 1.186 (1.015–1.446) | 1.375 (1.166–1.703) | 1.339 (1.144–1.641) | −929 (−1,582 to −484) | −310 (−1,258 to 457) | 2025-08-25: 4,098 | 4,920 |
| TimesFM 2.5 (one day per call) | 2,475 | 1.605 (1.331–2.002) | 1.083 (0.893–1.356) | 1.006 (0.835–1.265) | −1,506 (−2,408 to −744) | −1,193 (−2,373 to −148) | 2024-12-25: 5,995 | 6,857 |
| LightGBM, S1 settings | 1,809 | 1.174 (1.062–1.268) | 1.135 (1.022–1.239) | 1.131 (1.023–1.226) | −789 (−1,210 to −320) | −80 (−704 to 480) | 2025-12-25: 4,577 | 5,325 |
| LightGBM, defaults (sensitivity) | 1,941 | 1.260 (1.123–1.380) | 1.125 (0.990–1.242) | 1.135 (1.008–1.245) | −960 (−1,421 to −441) | −264 (−913 to 343) | 2025-12-25: 5,123 | 5,749 |
| LightGBM, S2 settings (sensitivity) | 1,860 | 1.207 (1.079–1.314) | 1.126 (1.005–1.235) | 1.126 (1.010–1.229) | −855 (−1,304 to −348) | −36 (−704 to 584) | 2025-12-25: 5,210 | 5,562 |
| Timestral (shown, not compared) | 2,124 | 1.378 (1.147–1.745) | 1.267 (1.049–1.600) | 1.287 (1.070–1.628) | −589 (−1,560 to 116) | 1 (−1,351 to 1,075) | 2026-01-02: 5,025 | 6,262 |
| NESO day-ahead (reference) | 820 | 0.532 (0.465–0.640) | 0.789 (0.686–0.956) | 0.760 (0.663–0.918) | 227 (30 to 422) | 439 (93 to 753) | 2025-12-27: 1,644 | 2,209 |

Comparison days, T3: 381 in the same months, 925 in all.

| Forecaster | Ratio, same months | Ratio, all other days | Bias, same months (MW) | Bias, all other days (MW) |
|---|---|---|---|---|
| Weather regression | 1 | 1 | −181 (−287 to −78) | −93 (−166 to −24) |
| Chronos-2 | 0.862 (0.815–0.912) | 0.886 (0.856–0.917) | −80 (−158 to 2) | −75 (−125 to −19) |
| TimesFM 2.5 (one day per call) | 1.483 (1.390–1.574) | 1.596 (1.528–1.663) | −105 (−275 to 73) | 93 (−38 to 213) |
| LightGBM, S1 settings | 1.034 (0.991–1.077) | 1.038 (1.014–1.061) | −142 (−259 to −24) | −32 (−109 to 44) |
| LightGBM, defaults (sensitivity) | 1.119 (1.061–1.178) | 1.110 (1.079–1.139) | −152 (−285 to −23) | −34 (−119 to 49) |
| LightGBM, S2 settings (sensitivity) | 1.072 (1.021–1.121) | 1.071 (1.044–1.098) | −156 (−278 to −32) | −35 (−117 to 45) |
| Timestral (shown, not compared) | 1.088 (1.014–1.169) | 1.070 (1.030–1.114) | 143 (42 to 259) | 146 (76 to 220) |
| NESO day-ahead (reference) | 0.674 (0.638–0.709) | 0.700 (0.677–0.720) | −63 (−120 to −9) | −14 (−52 to 25) |

## Limits

- **One winter dominates.** 59 of T1's 96 days (61%) come from winter 2024–25, so T1's result is largely that winter's.
- **Christmas Day 2025 is the worst cold day for most forecasters:** the regression, Chronos-2 and all three LightGBM settings. Ten of T1's 96 days are holidays, so the cold-day reading carries some holiday error. The study does not separate the two: removing those days would be an analysis the plan did not specify.
- **Many comparisons.** The study reports up to 56 tail shifts. At the 90% level, about one in ten would exclude 1 by chance. Only the two headlines and H1 were fixed in advance.
- **Size.** Tail shifts under about 15–20% were unlikely to be detected (`PLAN.md` §6). LightGBM's same-month shift, 10%, is in that range.
- **Training data.** The foundation models may have seen these days in training. LightGBM and the regression trained only on days before each forecast.

## What comes next

The plan's trigger for tails 2, a follow-up on uncertainty, has fired. On T1, LightGBM's shift against all other days and TimesFM's shifts excluded 1, and Chronos-2's peak error excluded 0. Tails 2 is back on the list, but not urgent.

If checkpoint 1 runs, read any result against LightGBM in a cold spring with its winter gap in mind.

## Reproduce

- **Plan:** `PLAN.md`, frozen at tag `tails-plan` before any script ran.
- **Day sets:** `build_days.py`, run at commit dba8c74. The sets are in `days.csv`, with counts and hashes in `days.json`.
- **Scoring:** `score_tails.py` (sha256 07b508de…), run at commit 0db9b84, after its synthetic check passed (`synthetic.json`). Outputs: `results.json`, `results.md`.
- **Changes:** every implementation choice the plan does not name, and the three reviews before the run, are in `REVISIONS.md`.
- **Data:** the forecast files are in this repository. The day sets were built from public data that are not committed: NESO's publications, ERA5, and ECMWF's open-data forecasts. Their files are named and hashed in `days.json`.

## Use of AI

I used AI tools in this work: Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai. The work is designed so that results are calculated numerically and checked against ground truths, and assumptions are checked against original sources. The scoring script passed a synthetic check with known answers before the real days were scored.

## Sources

- Lerch, S., Thorarinsdottir, T. L., Ravazzolo, F. and Gneiting, T. (2017). [Forecaster's dilemma: extreme events and forecast evaluation](https://projecteuclid.org/euclid.ss/1491465630). *Statistical Science* 32(1), 106–127. doi:10.1214/16-STS588.
