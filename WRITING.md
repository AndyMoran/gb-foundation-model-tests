# Writing standard

Applies to every document in this repository: READMEs, plans, rules, notes, code comments, commit messages and papers. Adopted from the battery project's writing standard, with this repository's examples.

Based on Strunk and White, *The Elements of Style*, and William Zinsser, *On Writing Well*. The rules below are paraphrased and adapted for technical writing.

The standard: a capable reader who wasn't in the room understands it on the first read.

## Rules

1. **Lead with the point.** The first sentence of a section states the decision or finding. Reasons follow.
2. **Omit needless words.** Cut "in order to", "it should be noted that", "basically", "very", "actually". If a sentence survives losing a word, lose it.
3. **One idea per sentence.** Split sentences over about 30 words. A sentence with two parentheses, or with a dash and a semicolon, is two sentences.
4. **Active voice, named actor.** "NESO publishes INDO", not "INDO is published". Use the passive only when the actor is unknown or doesn't matter.
5. **Positive form.** Say what is: "late", not "not on time". Keep negatives for real prohibitions: "Committed files are not edited."
6. **Specific and concrete.** Numbers with units, dates, names, sources. "Chronos-2's mean daily error was 916 MW over 960 backtest days" beats "Chronos-2 was quite accurate".
7. **Hedge once, precisely.** Put uncertainty in an interval or an `ASSUMPTIONS.md` status, not in stacked qualifiers ("may possibly", "somewhat likely").
8. **Keep related words together.** Put the qualifier next to what it qualifies. Use parallel structure in lists.
9. **One term, one meaning.** Define a term once and use it the same way every time. Don't vary words for elegance.
10. **State each rule once.** Link to it elsewhere instead of restating it. Copies drift.
11. **Current state in the document; history in the log.** Retired decisions move to the decision log. Committed results are the exception: they are never edited, and errors go in `CORRECTIONS.md` (rule 8.5).
12. **Write for one reader.** Name them at the top of each document, for example "for a reviewer checking the method".
13. **Plain words.** Use jargon only when the reader needs it, and define it on first use.
14. **Rewrite.** A first draft is for the writer. Revise before committing.

These rules serve clarity. Break one only when following it would make the meaning less clear.

## Checklist before commit

- [ ] Does each section's first sentence state its point?
- [ ] Any sentence over 30 words? Split it or justify it.
- [ ] Any parenthesis over about 10 words? Make it a sentence or a link.
- [ ] Any claim without a number, a source or an `ASSUMPTIONS.md` ID?
- [ ] Any rule stated in two places?
- [ ] Any retired content still in the live text?
- [ ] Read it aloud. Rewrite wherever you stumble.

## Example

From an early draft of the battery project's README.

Before (one sentence, 48 words):

> The £ estimate comes from within-unit change over time (each unit's GC0166 switch date, the end of NESO's grace period, changes in redeclaration behaviour), using whichever pre-registered design the adoption data supports (staggered event study if switch dates are dispersed; otherwise within-unit fixed effects or a grace-period dose-response).

After (two sentences, 51 words):

> The £ estimate comes from change within each unit over time: its GC0166 switch date, the end of NESO's grace period, or shifts in its redeclaration behaviour. Which design is used depends on how spread out the switch dates are, and the rule for choosing was fixed in advance (PROJECT.md §5A).

The rewrite splits two ideas into two sentences and replaces a nested parenthesis with a colon list. It also points to where the design rule lives instead of restating it. It is not shorter, and doesn't need to be: clarity, not word count, is the test.
