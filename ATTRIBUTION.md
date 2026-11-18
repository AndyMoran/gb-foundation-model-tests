# Attribution and licences

Every forecast, score and report this repository publishes is derived from the data and models below. Each publication carries the four data attributions, by citing this file or by repeating them. Licences checked on 18 November 2026 (`ASSUMPTIONS.md`, A9).

## Data

| Source | Used for | Licence | Attribution to carry |
|---|---|---|---|
| ECMWF open-data forecasts (00 UTC IFS runs) | Weather forecasts for every entrant | CC BY 4.0 | Contains modified Copernicus/ECMWF data (open-data forecasts). |
| ERA5, Copernicus Climate Change Service | Past weather: training weather and model context | CC BY 4.0 (replaced the Licence to use Copernicus Products on 2 July 2025) | Contains modified Copernicus Climate Change Service information (ERA5). Neither ECMWF nor the European Commission is responsible for any use of this information. |
| Elexon Insights Solution (BMRS) | INDO outturn; NESO's day-ahead forecast publications | [Licence to use BMRS open data](https://www.elexon.co.uk/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/): copying, publishing, adapting and commercial use permitted | Contains BMRS data © Elexon Limited copyright and database right 2026. Link to the licence where possible. |
| NESO Data Portal | NESO's forecast performance record; historic demand (robustness checks only) | NESO Open Licence, based on the Open Government Licence v3.0; set for each dataset | Supported by National Energy SO Open Data. |

Elexon's attribution is the wording its licence requires, with the year of use (`ASSUMPTIONS.md`, A15). Every source's attribution forbids implying official status or endorsement: neither Elexon, NESO, ECMWF nor the European Commission endorses this work.

## Models

| Model | Revision used | Licence | Condition |
|---|---|---|---|
| Chronos-2 | `amazon/chronos-2` | Apache 2.0 | None beyond Apache 2.0's notice requirements |
| TimesFM 2.5 | `google/timesfm-2.5-200m-pytorch` | Apache 2.0 | None beyond Apache 2.0's notice requirements |
| Timestral | `mistralai/Timestral-209M` | Mistral's "Modified MIT" | No rights for anyone whose company, or employer, has global consolidated monthly revenue above $20 million; attribution "2026 - Mistral AI" |

Timestral's condition limits who may run the model, not what may be published from its outputs. A forecasting team at a large company could not rerun the Timestral entrant without a commercial licence from Mistral. `benchmark/ENTRANTS.md` repeats this when it is written.

## Sources

- ECMWF, [CC-BY licence to replace the Licence to use Copernicus Products on 2 July 2025](https://forum.ecmwf.int/t/cc-by-licence-to-replace-licence-to-use-copernicus-products-on-02-july-2025/13464).
- Elexon, [Copyright: Licence to use BMRS open data](https://www.elexon.co.uk/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/) (saved copy, 30 October 2026: `AndyMoran/dispatch-realisation`, `docs/licences/`).
- Elexon, [The Insights Solution puts data on the wholesale market at your fingertips](https://elexon.co.uk/article/bsc-insight-the-insights-solution-puts-data-on-the-wholesale-market-at-your-fingertips).
- NESO, [NESO Open Licence](https://www.neso.energy/data-portal/neso-open-licence).
- Model cards: [Chronos-2](https://huggingface.co/amazon/chronos-2), [TimesFM 2.5](https://huggingface.co/google/timesfm-2.5-200m-pytorch), [Timestral licence](https://huggingface.co/mistralai/Timestral-209M/blob/main/LICENSE).
