# LightGBM variants: exploratory additions (after the scored results)

## Each variant's ratio to the regression minus S1's (negative: better than S1), 90% intervals on paired draws

| Variant | All days | Winter (Nov–Mar) | T1 |
|---|---|---|---|
| V1 | -0.062 (-0.082 to -0.043) | -0.133 (-0.175 to -0.096) | -0.242 (-0.347 to -0.144) |
| V2 | +1.999 (+0.962 to +3.448) | +0.919 (+0.258 to +1.771) | +1.754 (+0.014 to +4.564) |
| V3 | +0.109 (+0.082 to +0.139) | +0.148 (+0.084 to +0.221) | +0.346 (+0.191 to +0.522) |
| V4 | +0.010 (+0.002 to +0.017) | +0.005 (-0.011 to +0.019) | -0.020 (-0.060 to +0.018) |
| V5 | -0.036 (-0.049 to -0.023) | -0.074 (-0.100 to -0.050) | -0.097 (-0.170 to -0.038) |
| V2c | -0.025 (-0.034 to -0.016) | -0.040 (-0.058 to -0.021) | -0.041 (-0.090 to +0.009) |

## V2's daily errors (mean absolute error over each day's half-hours, MW; raw model output)

Median 1,020; 90th percentile 2,038; 99th percentile 40,910; maximum 686,933. Days above 5,000 MW: 39; above 20,000 MW: 17. Medians beside it: V2c 956, regression 943.

| Day | V2 daily error (MW) | V2 lowest forecast (MW) | V2 highest forecast (MW) | Outturn range (MW) |
|---|---|---|---|---|
| 2025-07-17 | 686,933 | -9,310,998 | 11,117,409 | 19,813–29,388 |
| 2025-08-12 | 149,312 | -139,502 | 1,483,381 | 19,508–29,694 |
| 2025-02-18 | 130,309 | -6,115,357 | 59,351 | 25,482–42,073 |
| 2024-05-08 | 127,472 | -6,057,634 | 30,054 | 19,797–28,925 |
| 2024-09-07 | 89,507 | -1,459,956 | 883,659 | 18,564–28,186 |
