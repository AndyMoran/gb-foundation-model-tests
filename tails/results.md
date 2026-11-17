# Tails: results (descriptive)

Backtest days the foundation models may have seen in training. Error is outturn minus forecast (MW): positive means under-forecast. Tail shift = ratio to the regression on the set ÷ ratio on the complement. 90% intervals by moving-block bootstrap. A forecaster loses or gains ground only where the shift's interval excludes 1 (PLAN.md §6).

**Headline (PLAN.md §8):**

In a backtest Chronos-2 may have seen in training, it did not clearly lose or gain ground against a weather regression on the coldest tenth of days, compared with other days of the same months (tail shift 1.055, 90% interval 0.915–1.213).

On the coldest tenth of days in a 960-day backtest, LightGBM did not clearly lose or gain ground against a weather regression, compared with other days of the same months (tail shift 1.102, 90% interval 0.988–1.217).

H1 was unclear: LightGBM S1 lost ground against all other days but not clearly against other days of the same months: a winter effect, not a cold-day effect. The T4 clause was not assessed: no scored day had a forecast temperature below the lowest in LightGBM's training rows, so T4 is empty.

Days scored: 960; not scored: 0.

## T1: coldest 10% by mean forecast temperature (primary)

Scored days: 96 (listed 96; not scored: none). Narrow complement: 175 days in 9 months; broad: 864 days.

| Forecaster | Days | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th pct (MW) |
|---|---|---|---|---|---|---|---|---|---|
| Weather regression | 96 | 1,025 | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | -178 (-358–6) | -134 (-357–91) | 2025-12-25: 2,968 | 2,717 |
| Chronos-2 | 96 | 968 | 0.944 (0.841–1.039) | 1.055 (0.915–1.213) | 1.051 (0.932–1.166) | 170 (-16–352) | 511 (195–837) | 2025-12-25: 3,690 | 2,729 |
| TimesFM 2.5 (one day per call) | 96 | 2,075 | 2.024 (1.758–2.359) | 1.302 (1.117–1.533) | 1.307 (1.138–1.521) | 468 (-58–1004) | 861 (198–1539) | 2024-11-19: 6,100 | 6,461 |
| LightGBM, S1 settings | 96 | 1,249 | 1.218 (1.097–1.330) | 1.102 (0.988–1.217) | 1.187 (1.066–1.298) | 49 (-288–357) | 349 (-65–741) | 2025-12-25: 4,577 | 3,654 |
| LightGBM, defaults (sensitivity) | 96 | 1,384 | 1.350 (1.197–1.504) | 1.124 (0.995–1.257) | 1.236 (1.095–1.381) | 70 (-316–437) | 476 (13–917) | 2025-12-25: 5,123 | 3,960 |
| LightGBM, S2 settings (sensitivity) | 96 | 1,313 | 1.281 (1.147–1.413) | 1.121 (0.999–1.245) | 1.213 (1.084–1.340) | 63 (-298–392) | 444 (-4–864) | 2025-12-25: 5,210 | 3,865 |
| Timestral (shown, not compared) | 96 | 1,475 | 1.439 (1.229–1.656) | 1.431 (1.212–1.679) | 1.374 (1.174–1.586) | 589 (246–935) | 862 (378–1372) | 2026-01-05: 5,306 | 4,331 |
| NESO day-ahead (reference) | 96 | 739 | 0.721 (0.647–0.805) | 1.111 (0.964–1.282) | 1.049 (0.939–1.181) | 45 (-71–168) | 130 (-51–328) | 2024-11-19: 1,763 | 2,024 |

| Forecaster | Ratio, narrow complement | Ratio, broad complement | Bias, narrow (MW) | Bias, broad (MW) |
|---|---|---|---|---|
| Weather regression | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 145 (-57–339) | -88 (-164–-14) |
| Chronos-2 | 0.895 (0.817–0.978) | 0.898 (0.867–0.931) | -380 (-514–-257) | -137 (-191–-75) |
| TimesFM 2.5 (one day per call) | 1.554 (1.403–1.718) | 1.549 (1.488–1.607) | -458 (-753–-182) | -14 (-144–116) |
| LightGBM, S1 settings | 1.105 (1.056–1.150) | 1.026 (1.004–1.046) | -64 (-289–151) | -72 (-150–7) |
| LightGBM, defaults (sensitivity) | 1.201 (1.138–1.260) | 1.092 (1.065–1.117) | -123 (-381–123) | -83 (-167–2) |
| LightGBM, S2 settings (sensitivity) | 1.143 (1.086–1.195) | 1.056 (1.032–1.079) | -104 (-348–133) | -79 (-163–4) |
| Timestral (shown, not compared) | 1.006 (0.917–1.097) | 1.048 (1.014–1.083) | -17 (-179–143) | 67 (-3–139) |
| NESO day-ahead (reference) | 0.649 (0.592–0.714) | 0.687 (0.664–0.708) | -76 (-157–5) | -11 (-51–30) |

Bootstrap draws dropped (no days in the set or complement): none.

## T1b: coldest 10% by coldest forecast half-hour (sensitivity)

Scored days: 96 (listed 96; not scored: none). Narrow complement: 221 days in 11 months; broad: 864 days.

| Forecaster | Days | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th pct (MW) |
|---|---|---|---|---|---|---|---|---|---|
| Weather regression | 96 | 1,101 | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | -297 (-522–-76) | -202 (-465–50) | 2025-12-25: 2,968 | 2,969 |
| Chronos-2 | 96 | 1,012 | 0.920 (0.820–1.021) | 0.994 (0.858–1.134) | 1.022 (0.904–1.143) | 72 (-132–261) | 380 (31–719) | 2025-12-25: 3,690 | 2,867 |
| TimesFM 2.5 (one day per call) | 96 | 2,084 | 1.894 (1.658–2.151) | 1.173 (1.024–1.331) | 1.213 (1.066–1.376) | 297 (-283–867) | 734 (28–1430) | 2024-11-19: 6,100 | 6,710 |
| LightGBM, S1 settings | 96 | 1,329 | 1.208 (1.092–1.326) | 1.102 (0.993–1.225) | 1.177 (1.065–1.295) | -26 (-402–323) | 234 (-235–683) | 2025-12-25: 4,577 | 3,904 |
| LightGBM, defaults (sensitivity) | 96 | 1,468 | 1.333 (1.184–1.486) | 1.133 (1.002–1.278) | 1.221 (1.084–1.367) | -5 (-449–417) | 364 (-163–871) | 2025-12-25: 5,123 | 4,331 |
| LightGBM, S2 settings (sensitivity) | 96 | 1,388 | 1.262 (1.132–1.399) | 1.115 (0.992–1.252) | 1.194 (1.068–1.329) | -25 (-436–357) | 312 (-190–786) | 2025-12-25: 5,210 | 4,139 |
| Timestral (shown, not compared) | 96 | 1,490 | 1.353 (1.130–1.588) | 1.258 (1.031–1.511) | 1.283 (1.069–1.517) | 507 (141–886) | 809 (311–1337) | 2026-01-05: 5,306 | 4,532 |
| NESO day-ahead (reference) | 96 | 760 | 0.690 (0.626–0.762) | 0.963 (0.859–1.076) | 1.000 (0.904–1.108) | 20 (-93–147) | 44 (-149–238) | 2025-03-05: 2,989 | 2,090 |

| Forecaster | Ratio, narrow complement | Ratio, broad complement | Bias, narrow (MW) | Bias, broad (MW) |
|---|---|---|---|---|
| Weather regression | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 43 (-126–204) | -75 (-151–-3) |
| Chronos-2 | 0.925 (0.854–1.008) | 0.900 (0.868–0.934) | -237 (-349–-129) | -126 (-181–-67) |
| TimesFM 2.5 (one day per call) | 1.614 (1.498–1.753) | 1.561 (1.498–1.621) | -332 (-561–-116) | 5 (-122–132) |
| LightGBM, S1 settings | 1.096 (1.057–1.136) | 1.026 (1.004–1.046) | -5 (-172–147) | -64 (-143–11) |
| LightGBM, defaults (sensitivity) | 1.177 (1.126–1.230) | 1.092 (1.065–1.117) | -32 (-212–135) | -75 (-160–6) |
| LightGBM, S2 settings (sensitivity) | 1.131 (1.087–1.179) | 1.057 (1.032–1.079) | -15 (-188–147) | -69 (-152–9) |
| Timestral (shown, not compared) | 1.076 (1.002–1.158) | 1.055 (1.020–1.091) | 38 (-94–168) | 76 (7–149) |
| NESO day-ahead (reference) | 0.717 (0.665–0.772) | 0.690 (0.667–0.713) | -40 (-127–43) | -8 (-48–33) |

Bootstrap draws dropped (no days in the set or complement): none.

## T2: top 10% by NESO's forecast peak (secondary)

Scored days: 96 (listed 96; not scored: none). Narrow complement: 144 days in 8 months; broad: 864 days.

| Forecaster | Days | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th pct (MW) |
|---|---|---|---|---|---|---|---|---|---|
| Weather regression | 96 | 940 | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 272 (115–451) | 218 (26–422) | 2025-12-15: 2,528 | 2,252 |
| Chronos-2 | 96 | 870 | 0.926 (0.811–1.047) | 0.981 (0.842–1.141) | 1.028 (0.899–1.172) | 170 (5–347) | 405 (177–639) | 2026-01-05: 2,493 | 2,370 |
| TimesFM 2.5 (one day per call) | 96 | 1,747 | 1.858 (1.547–2.235) | 1.142 (0.938–1.385) | 1.183 (0.988–1.428) | 445 (-8–951) | 519 (-89–1189) | 2024-11-19: 6,100 | 5,596 |
| LightGBM, S1 settings | 96 | 1,079 | 1.148 (1.034–1.270) | 0.997 (0.892–1.108) | 1.109 (0.997–1.230) | 365 (155–601) | 644 (394–902) | 2025-01-08: 3,845 | 2,868 |
| LightGBM, defaults (sensitivity) | 96 | 1,209 | 1.286 (1.123–1.459) | 1.030 (0.900–1.177) | 1.168 (1.024–1.328) | 387 (123–680) | 816 (532–1107) | 2025-01-08: 4,321 | 3,202 |
| LightGBM, S2 settings (sensitivity) | 96 | 1,138 | 1.211 (1.079–1.354) | 1.016 (0.901–1.143) | 1.136 (1.011–1.273) | 362 (123–620) | 715 (456–984) | 2025-01-08: 4,084 | 2,990 |
| Timestral (shown, not compared) | 96 | 1,222 | 1.299 (1.063–1.542) | 1.145 (0.935–1.372) | 1.219 (1.004–1.451) | 684 (455–932) | 751 (450–1056) | 2026-01-05: 5,306 | 3,503 |
| NESO day-ahead (reference) | 96 | 674 | 0.717 (0.629–0.818) | 1.143 (0.978–1.331) | 1.043 (0.915–1.193) | -79 (-191–40) | -178 (-347–-17) | 2024-11-19: 1,763 | 1,779 |

| Forecaster | Ratio, narrow complement | Ratio, broad complement | Bias, narrow (MW) | Bias, broad (MW) |
|---|---|---|---|---|
| Weather regression | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 67 (-143–254) | -138 (-212–-67) |
| Chronos-2 | 0.944 (0.862–1.030) | 0.900 (0.869–0.933) | -402 (-567–-244) | -137 (-192–-74) |
| TimesFM 2.5 (one day per call) | 1.627 (1.463–1.813) | 1.570 (1.510–1.627) | -403 (-757–-62) | -11 (-147–120) |
| LightGBM, S1 settings | 1.152 (1.099–1.204) | 1.035 (1.013–1.056) | -106 (-374–139) | -107 (-188–-29) |
| LightGBM, defaults (sensitivity) | 1.248 (1.182–1.316) | 1.101 (1.075–1.127) | -165 (-464–120) | -118 (-208–-33) |
| LightGBM, S2 settings (sensitivity) | 1.192 (1.128–1.258) | 1.066 (1.042–1.089) | -134 (-420–131) | -112 (-198–-30) |
| Timestral (shown, not compared) | 1.134 (1.029–1.245) | 1.066 (1.031–1.103) | -60 (-304–184) | 56 (-17–135) |
| NESO day-ahead (reference) | 0.627 (0.574–0.690) | 0.688 (0.665–0.708) | 31 (-58–124) | 3 (-36–45) |

Bootstrap draws dropped (no days in the set or complement): none.

## T3: bank holidays and 24 December to 2 January (calendar; not a cold-day set)

Scored days: 35 (listed 35; not scored: none). Narrow complement: 381 days in 14 months; broad: 925 days.

| Forecaster | Days | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th pct (MW) |
|---|---|---|---|---|---|---|---|---|---|
| Weather regression | 35 | 1,541 | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | -200 (-538–196) | 46 (-423–537) | 2025-12-28: 3,130 | 4,259 |
| Chronos-2 | 35 | 1,828 | 1.186 (1.015–1.446) | 1.375 (1.166–1.703) | 1.339 (1.144–1.641) | -929 (-1582–-484) | -310 (-1258–457) | 2025-08-25: 4,098 | 4,920 |
| TimesFM 2.5 (one day per call) | 35 | 2,475 | 1.605 (1.331–2.002) | 1.083 (0.893–1.356) | 1.006 (0.835–1.265) | -1506 (-2408–-744) | -1193 (-2373–-148) | 2024-12-25: 5,995 | 6,857 |
| LightGBM, S1 settings | 35 | 1,809 | 1.174 (1.062–1.268) | 1.135 (1.022–1.239) | 1.131 (1.023–1.226) | -789 (-1210–-320) | -80 (-704–480) | 2025-12-25: 4,577 | 5,325 |
| LightGBM, defaults (sensitivity) | 35 | 1,941 | 1.260 (1.123–1.380) | 1.125 (0.990–1.242) | 1.135 (1.008–1.245) | -960 (-1421–-441) | -264 (-913–343) | 2025-12-25: 5,123 | 5,749 |
| LightGBM, S2 settings (sensitivity) | 35 | 1,860 | 1.207 (1.079–1.314) | 1.126 (1.005–1.235) | 1.126 (1.010–1.229) | -855 (-1304–-348) | -36 (-704–584) | 2025-12-25: 5,210 | 5,562 |
| Timestral (shown, not compared) | 35 | 2,124 | 1.378 (1.147–1.745) | 1.267 (1.049–1.600) | 1.287 (1.070–1.628) | -589 (-1560–116) | 1 (-1351–1075) | 2026-01-02: 5,025 | 6,262 |
| NESO day-ahead (reference) | 35 | 820 | 0.532 (0.465–0.640) | 0.789 (0.686–0.956) | 0.760 (0.663–0.918) | 227 (30–422) | 439 (93–753) | 2025-12-27: 1,644 | 2,209 |

| Forecaster | Ratio, narrow complement | Ratio, broad complement | Bias, narrow (MW) | Bias, broad (MW) |
|---|---|---|---|---|
| Weather regression | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | -181 (-287–-78) | -93 (-166–-24) |
| Chronos-2 | 0.862 (0.815–0.912) | 0.886 (0.856–0.917) | -80 (-158–2) | -75 (-125–-19) |
| TimesFM 2.5 (one day per call) | 1.483 (1.390–1.574) | 1.596 (1.528–1.663) | -105 (-275–73) | 93 (-38–213) |
| LightGBM, S1 settings | 1.034 (0.991–1.077) | 1.038 (1.014–1.061) | -142 (-259–-24) | -32 (-109–44) |
| LightGBM, defaults (sensitivity) | 1.119 (1.061–1.178) | 1.110 (1.079–1.139) | -152 (-285–-23) | -34 (-119–49) |
| LightGBM, S2 settings (sensitivity) | 1.072 (1.021–1.121) | 1.071 (1.044–1.098) | -156 (-278–-32) | -35 (-117–45) |
| Timestral (shown, not compared) | 1.088 (1.014–1.169) | 1.070 (1.030–1.114) | 143 (42–259) | 146 (76–220) |
| NESO day-ahead (reference) | 0.674 (0.638–0.709) | 0.700 (0.677–0.720) | -63 (-120–-9) | -14 (-52–25) |

Bootstrap draws dropped (no days in the set or complement): none.

## T4: forecast below LightGBM's training range (mechanism)

Scored days: 0 (listed 0; not scored: none). Narrow complement: 0 days in 0 months; broad: 960 days.

No days: no metrics.

## H1 (PLAN.md §7)

Outcome: **unclear** (a winter effect, not a cold-day effect).

| Condition on T1 (LightGBM S1) | Interval |
|---|---|
| Narrow tail shift above 1 | includes |
| Broad tail shift above 1 | above |
| Bias above 0 | includes |
| Peak error above 0 | includes |
| T4 clause | not assessed (no scored day had a forecast temperature below the lowest in LightGBM's training rows, so T4 is empty) |

## Provenance

```
{
 "public_commit": "0db9b842a74017519db2a9969b2a46d59daa20cb",
 "script_sha256": "07b508de203e595fe03c7369525b31601760e2c1cbdd76f7a47d4a9775f6f1ee",
 "days_csv_sha256": "d9c6b6a5b1f7c06c168a13521484dbd957cd091510caff44c5eacfbad0a93f7c",
 "files_sha256": {
  "weather_study/results/forecasts.csv": "b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328",
  "weather_study/results/calendar_forecasts.csv": "976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe",
  "checkpoint0/lightgbm_forecasts.csv": "812ffb251e7c4428ec1bb9f1e7467c51bc4f8ae55caf5b78b3fd0c840b6250cd",
  "weather_study/correction1/timesfm25_single_day_forecasts.csv": "479ec318925cc59cd1e4f56a29ef9bc10d297fe3f8fa012482e1ce130dccd821"
 },
 "attempt2_sha256": "891ff5031935fdb095298071550c20086d68bcc49e71908ef64169deb40a6027",
 "seed": 20261117,
 "draws": 2000,
 "block": 7,
 "versions": {
  "python": "3.11.18",
  "numpy": "2.4.6",
  "pandas": "3.1.0"
 }
}
```
