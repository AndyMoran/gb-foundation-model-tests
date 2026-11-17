# Pipeline rules

How the benchmark's code is built: `code/`, the daily harness and every study script. Each rule is a lesson learned the hard way on an earlier project, restated for a data pipeline. Adapted from the battery project's pipeline rules (23 October 2026), with this repository's examples.

For: anyone writing or reviewing code in this repository.

## 1. Enforce checks in the pipeline, not in the reading

Any check that matters is an assertion in the code that stops the run: units, value ranges, row counts, input hashes, and the call-mode check (rule 4.8). A chart that looks wrong is a prompt to investigate, not a check.

## 2. Fail visibly; define the failure before the success

Before writing a step's happy path, decide what it outputs when it fails. API errors, missing half-hours and unparseable files produce explicit records with a reason. Nothing is dropped silently. Every run writes a coverage report: what was requested, what arrived, what was excluded and why.

## 3. Excluded is not deleted

An entrant-day that can't be scored stays in the published table as "not scored", with its reason. It never counts in a denominator. Readers can see what is missing and why, which matters for a comparison that names models (rule 5.3).

## 4. Make invalid states unrepresentable

Each record carries exactly the fields its stage has produced:

raw → validated → forecast → scored, or excluded(reason) at any point.

Enforce this with schemas (for example pandera or pydantic). A scored day without the outturn version it was scored against fails validation rather than reaching a table.

## 5. Each stage writes a complete output

Every stage's output is a valid end state, not a half-finished one. A rerun resumes from the last complete stage rather than starting over. A day's later attempts forecast only the entrants still missing (rule 10.2).

## 6. Version every stored format from first use

Output tables, manifests and intermediate files carry an explicit schema version from the first release, with a stub migration path. Keep the version identifiers separate:

| Identifier | Versions |
|---|---|
| Git tag | Code and plans |
| Harness version (rule 8.1) | The code that made each forecast |
| Manifest | Data vintage |
| Schema version | Output table format |
| Zenodo deposit | A checkpoint's record |

A change to one does not imply a change to the others.

## 7. Never re-derive a number to verify it

Upstream data revises: NESO reissues demand outturn. A fresh pull can legitimately produce a different number. Verify a published figure against its pinned run (manifest, code tag and output hash), not against a new download. A fresh pull is a new version and is reported as one (rule 5.4).

## 8. Deterministic by construction

Sort inputs, fix random seeds, pin library versions, and set threads, bins and windows explicitly. The same inputs and code must give byte-identical outputs, or outputs within a stated tolerance where a library cannot promise more. CI tests this.

## 9. Check the property, not the label

Identify things from the data, not from names or announcements:
- A forecast's issue time is set by the public-by times of its inputs (rule 2.1), not by when the job ran.
- Whether a model's forecasts depend on what else is in the call is tested (rule 4.8), not assumed from its documentation. TimesFM 2.5's covariate regression pooled every series in a call (weather study, correction 1).
- A model revision is identified by its weights' hash and its package version (rule 3.3), not by its name.

## 10. Declare degraded modes in the output

When a planned input is missing, the output records which mode it ran in, as a field, not a footnote. Examples: weather from the D−2 run when D−1's was not public by 09:30; a forecast made off the runner during an outage (rule 10.2). Leave a component out rather than filling it with a placeholder.

## 11. State what each number shows and doesn't show

Keep a claims map: for each published output, what it supports and what it doesn't. Example: a ratio below 1 shows that an entrant was more accurate than a baseline over one window. It doesn't show that it would be in another season, on another series or at another revision (rule 2.2).

## 12. Hard limits fail the build; everything else is monitored

CI fails on schema violations, non-determinism and hash mismatches. It tracks run time, memory and data volume against the budget (rule 3.3) without failing on them.

## 13. Derive, don't maintain in parallel

Field tables in the documentation are generated from the schema code. The published table's format is derived from the internal one. Two hand-maintained copies of a structure drift apart.

## 14. Retiring something means sweeping every reference

A retirement is done when the decision log has an entry and a search of all code and documents for the retired term comes back clean.

## 15. Deferred is not cut

Every out-of-scope item is labelled either deferred (with what would bring it back) or cut (with the reason).
