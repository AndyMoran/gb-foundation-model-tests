# Descriptive tables (Section 6.4), backtest

From `backtest_attempt1/forecasts.csv`, 960 days. Descriptive: 90% intervals, no tests.

## Mean absolute error by four-hour block, UK clock time (MW)

| Forecaster | Block | Without weather | With weather | Reduction | 90% interval | Error cut |
| --- | --- | --- | --- | --- | --- | --- |
| Chronos-2 | 00:00-04:00 | 862 | 523 | 339 | 302 to 376 | 39% |
| Chronos-2 | 04:00-08:00 | 1,007 | 742 | 266 | 225 to 309 | 26% |
| Chronos-2 | 08:00-12:00 | 1,760 | 1,256 | 504 | 438 to 573 | 29% |
| Chronos-2 | 12:00-16:00 | 2,259 | 1,443 | 816 | 720 to 916 | 36% |
| Chronos-2 | 16:00-20:00 | 1,566 | 1,131 | 435 | 372 to 500 | 28% |
| Chronos-2 | 20:00-24:00 | 1,162 | 787 | 375 | 319 to 434 | 32% |
| Timestral | 00:00-04:00 | 851 | 588 | 264 | 229 to 293 | 31% |
| Timestral | 04:00-08:00 | 1,004 | 813 | 191 | 155 to 227 | 19% |
| Timestral | 08:00-12:00 | 1,733 | 1,412 | 321 | 260 to 385 | 19% |
| Timestral | 12:00-16:00 | 2,207 | 1,656 | 552 | 470 to 639 | 25% |
| Timestral | 16:00-20:00 | 1,512 | 1,213 | 298 | 250 to 350 | 20% |
| Timestral | 20:00-24:00 | 1,146 | 854 | 293 | 245 to 341 | 26% |
| TimesFM 2.5 | 00:00-04:00 | 1,009 | 902 | 107 | 58 to 156 | 11% |
| TimesFM 2.5 | 04:00-08:00 | 1,191 | 1,132 | 60 | 4 to 119 | 5% |
| TimesFM 2.5 | 08:00-12:00 | 1,869 | 1,781 | 88 | 32 to 147 | 5% |
| TimesFM 2.5 | 12:00-16:00 | 2,333 | 2,286 | 48 | -22 to 125 | 2% |
| TimesFM 2.5 | 16:00-20:00 | 1,683 | 1,569 | 114 | 52 to 174 | 7% |
| TimesFM 2.5 | 20:00-24:00 | 1,315 | 1,172 | 143 | 82 to 198 | 11% |
| Regression | 00:00-04:00 | 1,072 | 725 | 347 | 291 to 403 | 32% |
| Regression | 04:00-08:00 | 1,156 | 838 | 318 | 252 to 383 | 27% |
| Regression | 08:00-12:00 | 1,920 | 1,220 | 699 | 613 to 787 | 36% |
| Regression | 12:00-16:00 | 2,361 | 1,358 | 1,003 | 913 to 1,098 | 42% |
| Regression | 16:00-20:00 | 1,583 | 1,216 | 367 | 285 to 453 | 23% |
| Regression | 20:00-24:00 | 1,153 | 729 | 424 | 359 to 492 | 37% |

## Mean daily error by season (MW)

Meteorological seasons, pooled across years.

| Forecaster | Season | Days | Without weather | With weather | Reduction | 90% interval | Error ratio | 90% interval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chronos-2 | winter | 180 | 1,649 | 1,088 | 560 | 431 to 672 | 0.660 | 0.607–0.731 |
| Timestral | winter | 180 | 1,647 | 1,262 | 384 | 267 to 492 | 0.767 | 0.707–0.836 |
| TimesFM 2.5 | winter | 180 | 1,817 | 1,543 | 273 | 137 to 403 | 0.849 | 0.787–0.923 |
| Regression | winter | 180 | 1,926 | 1,065 | 861 | 654 to 1,090 | 0.553 | 0.494–0.622 |
| Chronos-2 | spring | 261 | 1,548 | 1,065 | 483 | 404 to 565 | 0.688 | 0.650–0.733 |
| Timestral | spring | 261 | 1,517 | 1,117 | 401 | 334 to 474 | 0.736 | 0.698–0.776 |
| TimesFM 2.5 | spring | 261 | 1,653 | 1,564 | 89 | 30 to 143 | 0.946 | 0.915–0.982 |
| Regression | spring | 261 | 1,505 | 1,066 | 439 | 368 to 524 | 0.708 | 0.668–0.747 |
| Chronos-2 | summer | 276 | 1,208 | 857 | 351 | 286 to 406 | 0.710 | 0.675–0.753 |
| Timestral | summer | 276 | 1,173 | 975 | 199 | 148 to 241 | 0.831 | 0.799–0.870 |
| TimesFM 2.5 | summer | 276 | 1,339 | 1,236 | 103 | 31 to 180 | 0.923 | 0.871–0.975 |
| Regression | summer | 276 | 1,332 | 980 | 352 | 275 to 437 | 0.736 | 0.693–0.783 |
| Chronos-2 | autumn | 243 | 1,417 | 949 | 468 | 375 to 564 | 0.670 | 0.625–0.716 |
| Timestral | autumn | 243 | 1,384 | 1,062 | 322 | 265 to 385 | 0.767 | 0.734–0.800 |
| TimesFM 2.5 | autumn | 243 | 1,549 | 1,596 | -47 | -145 to 33 | 1.030 | 0.979–1.097 |
| Regression | autumn | 243 | 1,531 | 961 | 570 | 464 to 699 | 0.628 | 0.578–0.676 |
