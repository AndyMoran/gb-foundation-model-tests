# Exploratory check E5: the models given the calendar

Specified before running (weather/calendar_study.py). Calendar days: 35. Ratios of mean daily error, 90% intervals.

## Chronos-2

| Comparison | All days | Ordinary days | Calendar days |
| --- | --- | --- | --- |
| calendar gain (A / model with weather) | 0.934 (0.917–0.952) | 0.943 (0.927–0.960) | 0.833 (0.782–0.876) |
| Q3 with calendar (A / regression with weather) | 0.903 (0.871–0.933) | 0.886 (0.857–0.915) | 1.186 (0.922–1.379) |
| Q3 without weather (B / regression without weather) | 0.927 (0.899–0.954) | 0.921 (0.895–0.947) | 1.026 (0.772–1.190) |
| Q1 with calendar (A / model without weather) | 0.637 (0.616–0.660) | 0.632 (0.611–0.653) | 0.717 (0.596–0.802) |

| Mean daily error (MW) | All days | Ordinary days | Calendar days |
| --- | --- | --- | --- |
| A calendar + weather | 916 | 881 | 1,828 |
| B calendar only | 1,428 | 1,390 | 2,433 |
| weather (scored) | 980 | 934 | 2,194 |
| no weather (scored) | 1,436 | 1,394 | 2,551 |
| regression, weather (scored) | 1,014 | 994 | 1,541 |
| regression, no weather (scored) | 1,541 | 1,509 | 2,372 |

## Timestral

| Comparison | All days | Ordinary days | Calendar days |
| --- | --- | --- | --- |
| calendar gain (A / model with weather) | 1.013 (1.006–1.020) | 1.015 (1.008–1.022) | 0.984 (0.960–1.008) |
| Q3 with calendar (A / regression with weather) | 1.087 (1.046–1.131) | 1.070 (1.032–1.109) | 1.378 (1.055–1.662) |
| Q3 without weather (B / regression without weather) | 0.920 (0.893–0.946) | 0.915 (0.889–0.939) | 1.015 (0.759–1.237) |
| Q1 with calendar (A / model without weather) | 0.783 (0.761–0.806) | 0.780 (0.757–0.804) | 0.825 (0.738–0.913) |

| Mean daily error (MW) | All days | Ordinary days | Calendar days |
| --- | --- | --- | --- |
| A calendar + weather | 1,103 | 1,064 | 2,124 |
| B calendar only | 1,418 | 1,380 | 2,406 |
| weather (scored) | 1,089 | 1,049 | 2,159 |
| no weather (scored) | 1,409 | 1,365 | 2,573 |
| regression, weather (scored) | 1,014 | 994 | 1,541 |
| regression, no weather (scored) | 1,541 | 1,509 | 2,372 |

