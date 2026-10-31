# Hukommelse LM: pilot protocol 2.3 (31 October 2026)

**Do not pool these scores with 2.1 or 2.2.** Memory-item counts, stimulus lists, time limits, and scoring order have changed. Existing data remain stored with their earlier `protocol_version` values, and the analysis CLI selects only version 2.3.

## Research question

Can warm, cool and nearly black **CSS screen backgrounds** influence recall of recently learned pseudoword–object associations in remote, within-participant testing? CSS color values are **not** calibrated Kelvin, illuminance or spectral-power measurements. In particular, DARK is lower luminance than the other two backgrounds, so color and brightness are confounded.

## Controlled procedure

* Three within-subject conditions WARM, COOL, DARK, balanced across three order groups (A/B/C).
* Each group rotates across six possible word-list permutations.
* Per round, a 60-second color-only adaptation stage, 75 seconds to learn eight pseudoword–object pairs, a 30-second arithmetic distraction, and up to 120 seconds to recall eight objects.
* Each participant's learning order is securely shuffled and persisted on the server. The recall order is independently shuffled and guaranteed not to have any item in its earlier position. The answer key is grade-scored against the **recall order**, never the original canonical list position.
* Participants can see their graded word-by-word review and total arithmetic attempts/correct **only after all three rounds have been submitted**. The submit response does not leak scores earlier.
* Math totals are **client-reported and not independently verified**. They are offered as participant feedback and exploratory engagement indicators, **not** as a validated cognitive outcome.
* 12 pilot study languages with manually prepared short noun labels; UI translations are fully maintained for Norwegian/English/Swedish/German/French/Spanish, with an English fallback for Italian/Portuguese/Dutch/Danish/Polish/Romanian. These added language answers require review by native-speaking pilot participants before cross-language comparisons.

## Endpoints and study integrity

* Participant sessions use a random secret stored as a hash. Other users cannot retrieve a review by guessing a participant UUID.
* The correct answer keys never appear in learning- or recall-phase JSON. A completed-session response includes the review; no public scoreboard is available.
* All conditions use a constant neutral study panel and changing background. This reduces but cannot eliminate differences in actual luminance or reading experience.
* This is a **pilot** until the pseudoword lists are normed for difficulty and device-dependent visual presentation is validated.

## Interpretation and practical screening

A score of 3–5 out of 8 can be perfectly normal for this task. Avoid implying intelligence or ability from a score. Before broad recruitment, conduct a short pilot with people from different language groups and devices; inspect score distributions for floor/ceiling effects and three-list difficulty differences. Define exclusion rules, language stratification and the primary contrast analysis before data collection. Do not encourage retries; a new attempt is not an independent participant.
