# Phase 9F search selection/ranking — 2026-11-05

## Outcome

Confirmed root cause and implemented a narrow correction in the working tree.
At max_results=1, exact title #2009 now survives candidate selection before
older partial matches. Excerpts, short stories, essays and editions remain
eligible; no generic NOVEL-over-SHORTFICTION weighting was added.

Original installed plugin, original backup, Phase 9E candidate and checkpoint
8c37b852c41748f65b9b03a6cca1c28b8f312d26 remain unchanged. No new installation,
commit, tag, push, preference update, book modification or security-policy
change occurred. The pre-existing uncommitted final PHASE9E.md update is kept.

## New live discovery evidence: two requests only

Used the frozen Phase 9E candidate in a fresh disposable Calibre profile, with
settings applied before process startup, without registering/installing it.
Captured the ordinary advanced-search request and its existing public simple
fallback. Both returned HTTP 200. The advanced response was the registration
restriction notice, not a result table; no bypass or fabricated advanced layout.
No live title/publication detail requests, images or installed-plugin comparison
requests were needed. Later comparisons used captured bytes only, with network
connection/DNS blocked by their offline Python audit hook.

Input: The End of Eternity / Isaac Asimov; no identifiers; exact_search=False,
max_results=1, max_covers=1, search_titles=True, search_publications=False.
These reproduce Phase 9E's relevant request-local configuration. Other defaults
were supplied by Calibre in the disposable profile; no owner settings were saved.

Requests:

```
https://www.isfdb.org/cgi-bin/adv_search_results.cgi?ORDERBY=title_title&START=0&TYPE=Title&USE_1=title_title&OPERATOR_1=contains&TERM_1=The+End+of+Eternity&USE_2=author_canonical&OPERATOR_2=contains&TERM_2=Isaac+Asimov&CONJUNCTION_1=AND
https://www.isfdb.org/cgi-bin/se.cgi?arg=The+End+of+Eternity&USE_2=author_canonical&OPERATOR_2=contains&TERM_2=Isaac+Asimov&CONJUNCTION_1=AND&type=All+Titles
```

Raw response SHA-256:

- Registration notice: a8628fddfc209244261643cc440471ee18d9dec8b04095f2bd1c172c097eb280.
- Public simple search: ef6f1c6228f6d74fb84f19d2b83d5739e181049f6edc0849cde7583cf87d9380.

After existing type/language/author filtering, source discovery order is:

| Order | Title ID | Title | Type | Date | Exact-title relevance |
|---|---|---|---|---|---:|
| 1 | 954264 | Afterword (The End of Eternity) | ESSAY | 1986-01-03 | 2 |
| 2 | 72841 | Foreword (The End of Eternity original version) | ESSAY | 1986-01-03 | 2 |
| 3 | 2009 | The End of Eternity | NOVEL | 1955-08-25 | 0 |
| 4 | 691469 | The End of Eternity (excerpt) | SHORTFICTION | 1955-00-00 | 2 |
| 5 | 954263 | The End of Eternity (novella) | SHORTFICTION | 1986-00-00 | 2 |

All five rows credit Isaac Asimov. The complete novel IS present in discovery.
The search returns title IDs, not publication/edition IDs; no edition IDs for
this novel were obtained or invented. Edition expansion is tested separately
with explicitly controlled publication fixtures/dictionaries.

Date-only order before limiting was excerpt 691469, novel 2009, novella 954263,
afterword 954264, foreword 72841. Unknown month/day components sort earlier
lexically; that is existing date behavior, not necessarily an earlier real date.
The old code assigned relevance only AFTER this ordering and while adding
matches. Thus at an effective limit of 1 the novel could never reach a worker,
RecordMatches or Calibre's later comparator.

## Original versus checkpoint: controlled offline comparison

Both exact preserved archives were loaded separately in fresh Calibre processes:

- Original ZIP SHA 9be3ce2cce7d3cd666b040757883e1791b55cb78e64ed9fda2836cceab38a760.
- Checkpoint candidate SHA d07f49f97e2c1b894e318c9d867cbda1918fac3dbc9d2162852cfaecb4997132.

Same inputs and same captured discovery responses. Real discovery/identify/
worker orchestration ran; detail metadata retrieval used controlled dictionaries
for those title IDs, not new live requests. This establishes selection behavior,
not full live metadata equality or GUI rendering.

| Version | Requested max | Effective max after fallback | Results | Source comparator first |
|---|---:|---:|---|---|
| Restored original | 1 | 300 | all five titles | novel 2009 |
| Restored original | 3 | 300 | all five titles | novel 2009 |
| Frozen checkpoint | 1 | 1 | excerpt 691469 only | excerpt 691469 |
| Frozen checkpoint | 3 | 3 | novel, excerpt, novella | novel 2009 |
| Corrected working copy | 1 | 1 | novel 2009 only | novel 2009 |
| Corrected working copy | 3 | 3 | novel, excerpt, novella | novel 2009 |

The original's fallback incorrectly inflates the configured limit to 300. That
lets the novel reach the result queue, where its relevance 0 can outrank partial
results at relevance 2. Phase 9B deliberately corrected the preference/limit
mutation, exposing the pre-existing date-first selection defect. Classification:
an inherited ranking defect with a newly visible low-limit behavior regression
from the intentional limit correction; NOT evidence to restore preference
corruption or blame canonical deduplication.

The backed-up owner preferences actually contain max_results=300 and German
as the additional language; the other relevant search settings match these
probes. Phase 9E intentionally restricted its preview to one result. The failure
is therefore not proof that normal owner searches at their saved ceiling of
300 would lose the novel. The frozen candidate already returns it at max=3;
the correction is still necessary for an intentionally supported small limit.
No owner preference was changed to obtain the reproduction.

An original comparison repeated in a second fresh process produced different
raw queue order, consistent with its set-based dispatch/thread timing. The
novel still ranked first under the installed Source identify_results_keygen
comparator. Checkpoint max=1 excludes the novel before any worker timing can
matter. This is not a nondeterministic-worker explanation for the lost novel.

Source discovery order, selection order, raw worker queue order, source-comparator
order and final GUI display are distinct stages. The installed Calibre Source
comparator was executed offline; full GUI/global multi-source merging/display
was not tested and is not asserted identical in every owner configuration.

## Minimal correction and architecture boundaries

Production file: __init__.py only.

- New title_relevance helper: exact title spelling gets existing score 0;
  other matches retain score 2. Comparison normalizes canonical Unicode NFC,
  case via lower(), and whitespace; it preserves digits and punctuation.
  The older stripped comparison discarded digits/punctuation, incorrectly
  equating e.g. Volume 1 and Volume 2. No transliteration, compatibility folding,
  author-name change, query encoding change or work-type weighting is introduced.
- _identify sorts normal title candidates by (relevance, date) and publication
  candidates by (relevance, year) BEFORE the result limit, then assigns that same
  relevance to title results and linked publication expansion. Dates still order
  peers. Missing-title author-only searches have constant relevance 2, preserving
  their existing chronology/identity safeguards.
- RecordMatches canonical deduplication, strategy priority (explicit IDs/ISBN
  before name strategies), edition IDs, worker creation and deterministic
  completion sorting are unchanged. No extra network strategy or pagination is
  added. This is not a global reranking of records from strategies never run.
- Partial matches are not removed. If no exact title exists, prior date ordering
  applies. An explicitly requested excerpt is itself an exact work. A novel is
  preferred in the reported case because its TITLE is exact, not because all
  novels should outrank all stories or excerpts.
- Multiple distinct works with the same exact title still tie at relevance 0;
  this change does not invent a preferred work type or resolve that ambiguity.
- Magazine keyword search keeps its separate historical path. Advanced-table
  parser, transport, retries, headers, TLS, timeout floor, version and preference
  persistence are unchanged. No Calibre internals were modified.

## Fixture provenance and tests

tests/fixtures/eternity_simple_search.html retains five verbatim public table-row
fragments from the captured simple response, wrapped in a minimal main/table
container. It is not a reconstructed advanced-search table. Fixture SHA-256:
e87ed94f8681b2fb13cfb5d0012031e66d1c2ed5f387bf6e499b8bce8524b4ee.
Rows/metadata are credited to ISFDB and its contributors; the HTML is not
claimed as original ISFDB4 work or relicensed by this note. This is local
regression material, with no public distribution action. Detail dictionaries
in tests are synthetic and labelled as such. No upstream implementation was
copied; the ranking correction is local work in the inherited GPLv3 plugin.

Nine tests in tests/ranking.py cover:

1. Actual discovery IDs/order and the earlier excerpt date.
2. Exact novel at max=1.
3. Title-only exact selection.
4. Larger limits retaining excerpt/novella and their relevance.
5. Explicit excerpt requests remain valid.
6. Distinct numeric titles stay distinct.
7. Publication-only exact selection before older partial publications.
8. No-exact fallback keeps date ordering.
9. Mixed title/publication IDs and duplicate publication links preserve editions.

Before the fix, three focused failures were recorded (novel max=1, title-only,
numeric title distinctions). Full final suite under Calibre 9.17.0 / embedded
Python 3.14.8: **154 executed; 153 passed; 0 failures; 0 errors; 0 skipped;
1 expected failure**, the unchanged advanced-search limitation. Separate
Camoufox fixture suite: **24 passed**, no errors/failures/skips or real browser
processes. All prior metadata, identity, series, cancellation, preference and
duplicate tests remain passing. No assertions were weakened or skips added.

## Installation cache-error investigation

Reproduced offline, without changing the installed plugin: in one fresh process,
loader.load(original ZIP) followed by loader.load(checkpoint ZIP) raises
ImportError for UnsupportedQuery. The error's objects.__file__ still points
to the original archive. Root package reload does not imply that its already
imported child objects module has been replaced. The mixed module generation
causes the new root import to request a symbol absent from old objects.py.

Fresh candidate-only processes load/initialize successfully, as do the fixed
working-copy processes. A restart clears mixed in-memory modules AFTER a new
archive is installed. Restarting while the old ZIP remains installed is not a
demonstrated cure for the direct updater: it can preload the old objects again
before validating/reloading the candidate. Supported remove, exit, then add in
a separate fresh process worked in 9E. It was NOT repeated on the live profile
in 9F. No internal reload patch, sys.modules surgery, manual ZIP overwrite or
Calibre modification was introduced. This is a confirmed hot-update workflow
compatibility issue in the observed version, not fresh-runtime import failure.
No claim is made about untested Calibre versions or all GUI update workflows.

## Retained artifacts, safeguards and readiness

Investigation artifacts outside the repository:
C:\Users\apt\AppData\Local\Temp\isfdb4-phase9f-9de1bcaf-cfa2-4c43-acca-50875e17690a

capture.py, discovery-0/1.html, discovery.json/log, compare.py, original.json,
original-repeat.json, candidate.json, fixed.json and corresponding logs,
cache-probe.json, fixed-offline.zip and disposable process profiles are retained.
The fixed ZIP is an offline probe artifact, not an installed release candidate.
Before/after suite logs are in system TEMP as isfdb4-phase9f-before.txt and
isfdb4-phase9f-after.txt. No credentials, owner configuration or library files
were copied into repository fixtures.

Final active original ZIP SHA remains
9be3ce2cce7d3cd666b040757883e1791b55cb78e64ed9fda2836cceab38a760;
active ISFDB4 preference SHA remains
aab259b846970f31b620a4126935c2bdcbe46e45ea8b7cb0fdc13052050e758c.
Original backup and frozen candidate were not changed. No live book data,
installation, version, TLS, HTTP headers, timeout policy, commit, push or tag
was changed. No further isolation/firewall/ACL/VM work was pursued.

Readiness: fix is verified offline against real discovery data, but has NOT
been installed or subjected to the remaining Phase 9E live matrix. Keep the
restored original installed. A later authorized checkpoint/build/backup/install
and bounded live retest must precede adoption. Author-only, coauthor and cover
live checks still remain; this phase does not claim their completion. Other
Phase 8/9B limitations remain as documented, including advanced search and
inherited network security policy. No further phase or commit is begun.

## Final working-tree inventory

Modified tracked files: __init__.py (only production change), README.md,
tests/README.md, tests/run_calibre.py, plus the pre-existing final PHASE9E.md
update which this phase did not discard or rewrite. New untracked files:
docs/PHASE9F.md, tests/ranking.py and tests/fixtures/eternity_simple_search.html.
No checkpoint or release archive was overwritten. HEAD is still
8c37b852c41748f65b9b03a6cca1c28b8f312d26.

Relevant source locations: title_relevance at __init__.py:58; title candidate
sorting/scoring at 950/966; linked publication relevance at 1030; publication
candidate sorting/scoring at 1086/1096. No objects.py production change.

Tracked git diff --stat against checkpoint (includes the earlier Phase 9E report
update; excludes the three untracked additions):

```
 README.md            |   4 ++
 __init__.py          |  31 +++++-----
 docs/PHASE9E.md      | 160 +++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/README.md      |  25 +++++++-
 tests/run_calibre.py |   3 +-
 5 files changed, 205 insertions(+), 18 deletions(-)
```

git diff --check passes with no errors. Git emits ordinary LF/CRLF conversion
warnings for some text files; no file content was discarded. The new fixture,
test and report also have no trailing whitespace.
