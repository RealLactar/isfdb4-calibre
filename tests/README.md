# Isolated Calibre 9.17 regression baseline

Current Phase 9B result: **145 tests: 144 passed, 0 failed/errors, 0 skipped,
1 expected failure**. Earlier phase results below are historical evidence.

From the repository root in PowerShell:

```powershell
.\tests\run.ps1
```

Prerequisite: `calibre-debug.exe` from Calibre 9.17.0 must be on PATH. The
runner deliberately rejects other Calibre versions. No standalone Python,
pip packages, pytest, plugin installation, GUI, or book library is required.
Do not run `run_calibre.py` directly against a normal Calibre configuration.

## Isolation and source identity

The PowerShell launcher allocates a unique temporary root with config, cache,
and temp subdirectories before starting Calibre. It sets
`CALIBRE_CONFIG_DIRECTORY`, `CALIBRE_CACHE_DIRECTORY`, `CALIBRE_TEMP_DIR`,
`TEMP`, and `TMP` for the child; disables Python bytecode writes; selects
English for deterministic translation behavior; and removes any inherited
`CALIBRE_DEVELOP_FROM` override. It restores the parent environment in a
finally block and deletes only its verified generated temporary root.

The child checks the actual resolved configuration/cache paths. Each test
starts with fresh ISFDB4 preferences in the disposable config directory.
Writes made by normal plugin initialization and lookup therefore remain
isolated, including obsolete AI-key deletion and exact-search/fallback updates.

The child builds a disposable ZIP containing the three production Python
modules, import-name marker, and translations from this checkout. It loads
that exact ZIP with `calibre.customize.zipplugin.loader.load`, constructs its
returned plugin class, and calls initialize(). It never invokes add_plugin,
calibre-customize, or the installed-plugin registry to select ISFDB4.
Assertions verify module origins, plugin path, ZIP entry SHA-256 hashes,
and unchanged checkout input hashes after the suite. Tests are excluded
from the plugin ZIP.

A Python audit hook blocks network connections/DNS, subprocess execution,
SQLite connections, and ordinary file writes/removal/rename/mkdir outside
the disposable root. Tests deliberately exercise the write/network guards.
Network responses are mocked at `objects.urlopen`; the production TLS-context
creation, headers, URL construction, and timeout calculation are untouched.

This is a regression harness, not an OS security sandbox. The audit hook starts
when the test script executes, after Calibre startup. Environment redirection
protects normal startup settings/cache/temp activity; native extensions and
unaudited system calls are outside the audit hook's guarantees. No library
paths are supplied and the GUI is never started. Abnormal process termination
can leave a disposable directory behind; normal completion cleans it up.

## Coverage

- Exact checkout ZIP loading, initialization, translations, and capabilities.
- Real Calibre Metadata objects and public result queues.
- Title/author query construction, surname ordering, initials, Latin-1 encoding.
- Direct title-ID and publication-ID lookup, precedence, publication/title merge.
- Synthetic title/publication HTML extraction, dates, language, tags, comments,
  publisher, search stubs, and publication search results.
- Offline title/author lookup through the existing advanced-to-simple fallback,
  including author filtering and the current preference updates to 300.
- Collision qualification of distinct records with identical titles/authors.
- Existing headers and 90-second timeout floor (5/30 seconds become 90;
  120 seconds remain 120), without sleeping.
- HTTP 403/404/500, URL errors, timeout exceptions, missing ContentBox, empty
  and malformed HTML, worker failures, and pre-set cancellation.
- Actual installed test helper signature compared with the checkout invocation.

Fixtures are minimal, synthetic HTML authored for the tests, not downloaded
ISFDB pages. Some orchestration cases mock higher-level parsers deliberately;
separate end-to-end cases retain the real parsers and mock only transport.
Uncovered areas include cover downloading, all series/external-ID variants,
real server redirects/cookies, actual socket timing, concurrent cancellation,
GUI behavior, and live-site HTML changes. Offline success does not prove that
ISFDB currently accepts the plugin's requests.

## Baseline: 2026-11-01

Calibre **9.17.0**, embedded Python **3.14.8**:

```text
3.14.8 (main, Oct  3 2026, 20:00:05) [MSC v.1950 64 bit (AMD64)]
Executable: C:\Program Files\Calibre2\calibre-debug.exe
29 tests: 27 passed, 0 failed/errors, 0 skipped, 2 expected failures
```

The two expected failures are executed, not skipped. They document desired
behavior that the unchanged production code does not satisfy. Unexpected
success makes unittest fail, so a future repair requires reviewing these tests.

1. `test_known_author_only_lookup`: identify(authors=[...]) with no title or
   IDs raises TypeError at `keyword in title`.
2. `test_known_advanced_search_language_column`: TitleList.from_url reads
   language from td[5], while Title.stub_from_search reads the title link from
   that same cell. The synthetic row demonstrates an internal inconsistency:
   a normal title such as "The Offline Star" is rejected as a language. This
   does not establish the current live site's exact column layout.

Observed warning: lxml emits FutureWarning for truth-testing an element in
the existing simple-search fallback (`objects.py:731`). It is not suppressed.

### Correction: legacy test helper

The previous assessment incorrectly reported a keyword mismatch. The installed
function accepts `(name, tests, modify_plugin=<lambda>, fail_missing_meta=True)`.
The checkout calls it with `fail_missing_meta=False`. Signature binding passes:
**there is no keyword mismatch**. The harness checks this without executing
the legacy helper, which selects registered plugins by name and may access
the network. The new harness explicitly selects the disposable checkout ZIP.

### Existing behavior and security concern

HTTP 403 is propagated, not converted into an HTML registration-message
fallback. Worker-level failures log an exception and yield no result. Empty
response bytes raise lxml ParserError at the fetch boundary; malformed but
recoverable HTML is accepted. These are characterization tests, not repairs.

Production fetches currently use `ssl._create_unverified_context()`, disabling
certificate verification. This concern is documented for later review; no TLS
override, certificate change, or production-code modification is introduced.
The intentional minimum 90-second timeout and existing browser-style request
headers remain unchanged.

## Optional future live smoke test

No live test is implemented or run automatically. A separately approved,
explicitly invoked smoke test could use the same disposable environment and
one known title-ID request with the existing request behavior, reporting
server rejection separately from regression failures. It must not retry with
alternate identities/headers or attempt to bypass ISFDB restrictions. The
ordinary offline runner must retain its network guard.

## Phase 2: author-only lookup and advanced-search investigation

### Author-only behavior

The Phase 1 author-only expected failure reproduced a TypeError at
`keyword in title` when title was None. Merely replacing None with an empty
string was insufficient: the title-search registration fallback would treat
the author TERM_1 as a title, and downstream comparisons assumed a string.

The fix normalizes absent titles within the non-direct-ID search path and uses
public `se.cgi?arg=<author>&type=Name` plus summary author bibliographies for
author-only input. `TitleList.from_author` produces existing title stubs;
identify retains its date sort, linked-publication expansion, workers,
metadata extraction, collision qualification, and public result queue.

The helper follows a direct author-page redirect or extracts author candidates
from Name results. It prefers exact displayed names when available, otherwise
uses partial-name candidates in site order, requesting no more author pages
than max_results. Duplicate title URLs are removed. Explicit translation
languages and the author's original language use the existing English plus
selected-language policy. No preference defaults are changed.

Author-only title/publication toggles remain effective. Publication-only
queries expand bibliography titles to their publication IDs without emitting
title records. A guard before the next author-only candidate prevents linked
publication expansion from overflowing the result limit. This guard applies
only to author-only lookups; normal title/author result selection is unchanged.
The existing worker scheduling and result completion order are unchanged.
An ISBN lookup with no title still passes its selected records to the workers.

Added tests demonstrate real Metadata results for absent/empty titles,
publication-only and combined selection, exact/partial names, direct redirects,
language preferences, duplicate filtering, date-based selection and result
limits. Existing normal-title and direct-ID tests remain in the full suite.
No-name/no-title input performs no unbounded search.

### Live HTML evidence and remaining uncertainty

Ordinary GET requests used the plugin's existing header dictionary, without
cookies, login, changed TLS handling, retries, or anti-restriction measures.
These were manual investigation requests, separate from the offline suite:

- [Advanced author-constrained title query](https://www.isfdb.org/cgi-bin/adv_search_results.cgi?ORDERBY=title_title&START=0&TYPE=Title&USE_1=author_canonical&OPERATOR_1=contains&TERM_1=Isaac+Asimov)
  returned HTTP 200 with the registration-restriction message, not result rows.
- [Public Name search](https://www.isfdb.org/cgi-bin/se.cgi?arg=Isaac+Asimov&type=Name)
  returned HTTP 200 with a generic_table, an Author first column, tooltip-wrapped
  and plain ea.cgi links, and an exact Isaac Asimov candidate at ea.cgi?5.
- [Summary bibliography](https://www.isfdb.org/cgi-bin/ea.cgi?5) returned HTTP 200
  with ContentBox blocks, an original Language field, a bibliolinks table,
  nested lists of title.cgi links, bold years, and bracketed translation languages.
- [Alphabetical bibliography](https://www.isfdb.org/cgi-bin/ae.cgi?5) also returned
  HTTP 200 and confirmed the same list conventions; the implementation uses
  the summary page, not this additional view.

The new author fixtures are synthetic examples of those observed structures,
not snapshots or comprehensive copies of live bibliographies. The restriction
fixture now contains the observed h3 message structure. The advanced-search
fixture is explicitly labeled an unverified synthetic contradiction case.

There is an internal title/language td[5] contradiction in production, but the
live advanced-search table was not obtainable without registration. Evidence
does not establish which column should change, or whether the fixture reflects
any current real layout. **No advanced-search parser column was changed.**
Its expected failure remains as an unresolved diagnostic, not proof of a
specific live-site repair. No access restriction was bypassed.

Author name ambiguity is intentionally bounded rather than exhaustively
resolved. Very large bibliographies still require downloading the author page;
only metadata result processing is limited. Language behavior and author-only
results are covered offline, but the new complete lookup was not run live under
Calibre. The observed lxml element-truthiness warning remains unrelated and
unmodified. TLS verification remains disabled in production and unchanged.

Current runtime: Calibre 9.17.0, Python 3.14.8 (main, Oct 3 2026, 20:00:05),
MSC v.1950 64-bit AMD64. Configuration, cache, temp paths, ZIP identity, network
blocking and cleanup continue to use the Phase 1 isolated launcher.

## Phase 3: author edge cases and parser evidence

No production source was changed during this phase. `author_edges.py` adds
22 offline cases through a test mixin in the existing isolated runner. Its
small HTML builders produce synthetic variants of the observed author-page
structures, encoded with numeric references when needed. No new dependencies
or live smoke-test runner were introduced.

### Confirmed author behavior and defects

| Area | Observed result |
| --- | --- |
| Exact versus similar names | An exact case-insensitive displayed name excludes similar names. Comma/surname ordering works. |
| Identical names at different author IDs | Both bibliographies contribute records, without an ambiguity warning. The title identifiers remain distinct, but author identity is not preserved in returned stubs. |
| Multiple partial-name matches | Multiple distinct authors' works are combined without an ambiguity warning. This is candidate aggregation, not reliable selection of one identity. |
| Punctuation/Unicode equivalence | `Ada J Example` does not exactly match `Ada J. Example`; composed/decomposed Unicode names are not normalized. An earlier similar candidate can consume the author-page cap. |
| Coauthored title records | Confirmed defect: Title.from_url resets `properties["authors"]` for each author detail, retaining only the last coauthor. The new expected-failure test requires both authors. |
| Coauthored publication records | Publication.from_url keeps both authors in the test. The loss is specifically in the title-record parser, which is shared with normal lookups. |
| Duplicate author/title links | Repeated author URLs are fetched once; the same title shared by multiple candidate bibliographies is processed once. |
| Multiple editions | Distinct publication IDs are deliberately retained and title-qualified; repeated publication IDs do not produce extra records. Semantic edition deduplication is not attempted. |
| Series | Series names/index and standalone metadata survive the existing parser/worker pipeline. |
| Large bibliography | With 200 reverse-dated works and max_results=3, only the earliest three selected title records are processed. The bibliography itself is still downloaded and parsed in full. |
| Equal/missing dates | Stable date sorting preserves bibliography order for ties. Empty/unknown dates sort before known dates and yield null publication dates. Final result queue order remains worker-completion dependent. |
| Author-page cap | The first empty candidate can exhaust max_results author-page requests, even when a later candidate has usable works. The cap bounds candidates, not successful results. |
| Empty response bytes | lxml ParserError escapes the author-search path; it is not converted to an empty result. |
| Malformed/empty structure | A valid page without titles or malformed HTML without the expected structure produces no results; recoverable unclosed lists still parse. |
| Latin-1 names | A name such as Jose with an accented e is encoded and returned correctly. |
| Non-Latin-1 names | Confirmed defect/limitation: the inherited URL encoder replaces unsupported characters and truncates at the first replacement. A name beginning with Japanese characters produces `se.cgi?arg=` and loses `type=Name`; this is logged but cannot be a reliable author search. |

Characterization tests intentionally assert existing behavior, including the
undesirable cases in this table; passing them is not a claim that those cases
are correct. The coauthor contract is an expected failure, alongside the
previous unresolved advanced-search diagnostic. Neither is skipped. The
normal title/author and direct-ID tests remain in the complete suite.

Resolving ambiguous identities reliably would require a policy for author IDs
or explicit disambiguation, rather than arbitrarily picking the first name.
That design work was not implemented here. Likewise, deduplicating editions
by semantic work identity would conflict with the plugin's intentional
preservation of separate publication IDs. Suggested later work, in priority
order: repair title coauthor accumulation; establish a verified Unicode query
contract; define ambiguity/provenance behavior; then review candidate caps and
empty-response error reporting. None was changed in Phase 3.

### Advanced-search evidence

An ordinary GET to the same advanced author-constrained title query used in
Phase 2 again returned HTTP 200 and only the registered-user restriction
inside `div#main`, not a result table. No login or alternate access method was
attempted. The request was manual investigation outside the offline suite.

Repository evidence reviewed includes current selectors and comments, tracked
files, history of td[5]/td[4] selectors, and all-branch HTML/test/fixture path
history. No captured advanced-result HTML was found in tracked history.
The original commit `6b2f3a8` already parsed title links at td[5] and authors at
td[6]. Before `4339b62` (2022-07-13), language filtering used td[4]; that commit
introduced the simple-search branch and changed advanced language filtering
to td[5], while leaving advanced title extraction at td[5]. This strongly
suggests a historical indexing regression, but it is source history rather
than evidence of the current live table.

The synthetic fixture places language at td[4] and title at td[5], consistent
with that earlier source expectation. It is still **not a verified live ISFDB
table format**: its headers are abbreviated and it was authored locally.
Neither the fixture nor source history alone justifies a production column
change. The parser and its expected-failure diagnostic remain unchanged.

To resolve this, obtain a permitted advanced Title search response containing
the table's complete header row and representative data rows, with URL,
capture date, response encoding, and relevant display/login options recorded.
Include ordinary and tooltip-wrapped title/author links, language cells, and
any explicit tbody structure. A user-provided authorized capture or authoritative
server rendering source could establish the mapping without bypassing access
restrictions. Validate selectors against that evidence before changing them.

Verification: Calibre 9.17.0, embedded Python 3.14.8 (MSC v.1950, 64-bit AMD64);
61 tests, 59 passed, no unexpected failures/errors, no skipped tests,
2 expected failures. TLS, HTTP headers, 90-second timeout, live settings,
installed plugins, libraries and production source remain unchanged in Phase 3.

## Phase 4: focused production remediation (2026-11-03)

All tests run through the same disposable Calibre configuration/cache/temp
launcher and explicit checkout ZIP. No live requests were made in Phase 4.
The ordinary suite remains offline. `phase4_cases.py` adds 16 focused cases,
and the applicable Phase 3 characterization tests now assert corrected
behavior. The title coauthor test is a normal passing test; only the unchanged
advanced-search column diagnostic remains an expected failure.

### Author identity and provenance

Candidate identity is keyed by ISFDB author URL/ID, including the final URL
after an ordinary redirect. Two alternate-name pages that resolve to the same
author ID are treated as one bibliography. Distinct IDs are not collapsed
merely because their displayed names match. Name comparison normalizes NFC,
case, whitespace and punctuation for candidate preference, while stable IDs
remain the identity boundary.

Where multiple plausible IDs remain, useful results are retained. A warning
lists the candidate IDs; each result's comments explicitly mark the ambiguity
and identify its source bibliography link(s). This annotation also covers
unexamined candidates when the scan allowance stops further requests. Shared
title IDs remain deduplicated and retain all observed source IDs. Candidate
names are HTML-escaped. Existing metadata titles/authors are not replaced by
the search name or chosen arbitrarily as a disambiguation policy.

An optional input identifier `isfdb-author:42` selects that stable author ID
directly for author-only searches, including when the author name is absent
or cannot be represented in the legacy query encoding. It is validated as
ASCII digits and bypasses Name search. Book title/publication identifiers
keep their existing priority. This is lookup input, not a new book identifier
written onto every returned result, and introduces no saved preference.

Unrelated author IDs cannot be proven equivalent without a redirect or other
reliable relationship evidence. They therefore remain explicitly ambiguous;
the plugin does not infer canonical/alternate-name equivalence from spelling.
If a scan stops before a possible alias is fetched, ambiguity is conservatively
reported. A future disambiguation UI is outside this phase.

### Coauthors and metadata merge

Title credit fields are read in DOM order, supporting linked credits,
tooltip-wrapped/nested names, repeated credit labels, strong/bold labels,
unlinked spans/plain text and mixed linked/unlinked fields. Tooltip explanation
text and markers are excluded. Each credited name is accumulated instead of
resetting the author list. Plain names use explicit `and`, ampersand or
semicolon separators; commas are preserved to avoid splitting surname-first
names. Unusual unlinked comma-separated lists remain inherently ambiguous.

Publication/title merging retains publication credit order and spelling,
then adds missing title coauthors. When author links provide the same stable
ID under different credited names, the publication spelling is retained
without adding a duplicate identity. Without author-ID evidence the merge
compares credited names conservatively. Other publication/title field
precedence and separate-edition preservation are unchanged.

### Unicode safety and evidence limit

Both query builders now share strict ISO-8859-1 encoding after NFC
normalization. Existing Latin-1 query bytes and all required parameters
(including `type=Name`) are preserved. Decomposed Latin-1 names normalize
losslessly. The old replacement/truncation path is removed.

Full non-Latin-1 query support is **not claimed**. There is insufficient
server-side evidence to switch these legacy CGI requests to UTF-8 or numeric
character references safely. Unsupported input raises a specific
UnsupportedQuery diagnostic; identify catches it, logs that the search was
not sent, and emits no incomplete/broadened request. Direct book-ID and
author-ID lookups remain usable for those names. No transliteration, query
truncation or speculative encoding fallback is performed. A verified server
encoding contract is needed to enable full Unicode name searches later.

### Candidate limits and empty responses

`max_results` still bounds returned records. In author discovery it now bounds
useful distinct bibliography pages, not empty pages: empty or filtered
candidates do not consume that allowance. A separate deterministic scan cap,
`max(20, max_results * 5)`, bounds candidate-page attempts, with a warning when
candidate pages remain unexamined. Site candidate order, existing date-based
record selection, result collision handling and duplicate suppression remain
in force. Whole bibliography pages are still downloaded before selection.

Empty or whitespace-only HTTP response bodies log the requested/final URL
and return an empty HTML root to the existing parsers. They no longer throw
lxml ParserError. This allows search paths to return no matches and record
workers to reject missing metadata normally. HTTP errors, connection failures,
request headers, TLS context and minimum 90-second socket timeout are unchanged.

### Configuration, verification and remaining defects

No new options, defaults or preference migrations were introduced. The earlier
exact_search and fallback max_results/max_covers preference writes still exist
in production; tests confine them to disposable settings. Ambiguity notices
are result comments/log messages, and scan counters are invocation-local.

Runtime: Calibre 9.17.0, Python 3.14.8 (main, Oct 3 2026, 20:00:05),
MSC v.1950, 64-bit AMD64. Result: 77 executed; 76 passed; no unexpected
failures/errors; none skipped; one expected failure. Existing normal title,
identifier, publication, edition, series and author-only tests remain included.

The advanced-search parser and unverified fixture are unchanged in Phase 4.
Its column mismatch remains unresolved pending permitted real table evidence.
Other known limitations include full Unicode name queries, unresolved distinct
author identities, the explicit candidate scan bound, unspecified final worker
completion order, and the existing lxml element-truthiness warning. TLS
verification remains disabled as before; changing it is outside this phase.

## Phase 6A: HTTP diagnostics (2026-11-04)

The new http_diagnostics.py mixin adds 11 tests, with parameterized cases for
HTTP 403/404/429/500 at open and read time, direct socket/request timeouts,
nested URLError/argument/cause-wrapped exceptions, refused/reset connections,
response URL/read failures, empty responses and successful Latin-1 decoding.
Assertions verify exception identity, the original traceback object/frame,
preserved explicit causes and a single request attempt. A broken logger is
also tested: diagnostic failure must not mask the transport exception.
Rendering is checked with Calibre's real logger as well as mocks.

Production changes are confined to the existing fetch helper plus its HTTPError
import. The open/geturl/read operations are guarded only to log and bare-raise;
standard exceptions are not replaced. Messages identify the operation, URL,
known final URL, effective timeout, HTTP status where applicable, and wrapped
reason. Empty-body messages now render actual URL values with Calibre logging.

The pre-existing Phase 4 empty/whitespace-body policy is retained: log an error
and provide an empty HTML root for downstream parsers. This policy applies to
successful HTTP responses with no usable body, not to caught transport errors;
those errors always escape the fetch helper unchanged. No retries are added.

Provenance credits are in the source, root README development changelog and
docs/UPSTREAM_PROVENANCE.md. The upstream defective exception logic and custom
exception definitions were not copied. Headers, TLS, minimum 90-second timeout,
browser cloning, threading, parsing, selection and preferences are unchanged.

Complete offline result: Calibre 9.17.0, embedded Python 3.14.8, 88 executed,
87 passed, no failures/errors, none skipped, one advanced-search expected
failure. No Camoufox work or Phase 6B was started.

## Phase 6B: separate offline feasibility probe

```powershell
.\tests\run_camoufox_feasibility.ps1
```

This separate runner executes camoufox_feasibility.py in Calibre 9.17.0 /
Python 3.14.8 with disposable paths. It is not imported by the ordinary suite.
It uses installed dispatch/lifecycle methods with fixture browser responses
and mocked worker/process startup. External network and non-disposable writes
are blocked; loopback is allowed for asyncio's own control facilities. Real
browser launch and dependency acquisition are forbidden. No global handler
registry is changed and no plugin is installed.

24 tests pass. Fixture fetching, redirects, Unicode parser handoff, controlled
errors, serialization/concurrency, deadlines, async cancellation and fake
session cleanup are covered. Native browser networking, JavaScript, actual IPC,
Windows process cleanup and real performance are NOT established. No child
browser/worker process is created, so the tests cannot prove native orphan
prevention. See docs/CAMOUFOX_FEASIBILITY.md for the evidence distinctions and
NO-GO production recommendation. The ordinary suite remains 88 tests:
87 pass and one advanced-search diagnostic is an expected failure.

## Phase 7: Unicode and metadata correctness

`unicode_correctness.py` adds 14 offline tests to the ordinary runner. The
complete suite now executes 102 tests: 101 pass, no failures/errors or skips,
and the unchanged advanced-search parser test remains an expected failure.
Runtime: Calibre 9.17.0 / embedded Python 3.14.8. The separate feasibility
suite was also rerun because the existing parser handoff is shared: 24 pass.

Coverage includes Latin-1 round trips and exact parameter ordering, NFC
composition without compatibility transliteration, atomic rejection of
unsupported scripts/punctuation with parameter and codepoint diagnostics,
mixed-script identity separation, explicit ambiguity for partial pseudonyms,
stable-ID Unicode metadata, ordered linked/unlinked credits, homonymous
coauthors, and publication spelling/order preservation across NFC differences.
Existing tests continue to cover missing dates, duplicate IDs, distinct
editions, series, malformed/empty responses, result limits and identifier
lookups. All network responses are mocked; no live ISFDB request is made.

Encoding evidence remains the historical UTF-8-to-Latin-1 change documented in
the root README and the form examples in SearchResults URL builders. This
does not establish current server UTF-8 query support. No new server evidence
was obtained and the query encoding is deliberately unchanged. Cyrillic,
Greek, Chinese, Japanese, curly apostrophes, em dashes, fullwidth forms and
combining sequences that remain outside Latin-1 after NFC are rejected before
the query is sent. A composable Latin accent is accepted. No transliteration,
punctuation substitution, NFKC or confusable-script folding is performed.
Known ISFDB IDs can retrieve non-Latin metadata without a name query.

Name selection prefers NFC/lowercase/whitespace-normalized exact spelling;
only absent such a match does punctuation-variant matching apply. Multiple
stable author IDs remain separate with existing explicit ambiguity reporting.
Stable IDs also govern credit merging; missing IDs retain name fallback, so
unlinked homonyms cannot be disambiguated reliably. No new preferences or
defaults, transport policies, plugin version or Camoufox integration change.

## Phase 9A: metadata correctness

`metadata_correctness.py` contributes 17 tests (including the four original
reproduction methods). The seven initially reported failures were subtest
failures across those four methods, not seven independent production defects.
The original assertions remain. Expanded coverage exercises publication and
title decimal indices, malformed/empty numeric fields, Roman and combined
issues, existing vol/no Notes, container authorship with both matching and
different names, optional-field combinations, series precedence/conflicts and
nested names, complete/missing template inputs and logged fallback.

Rating coverage calls the installed Calibre ISBNMerge consumer with the same
relevance/plugin annotations Calibre normally adds. ISFDB 9.00 produces source
rating 4.5; Calibre's merger accepts 0..5 stars and rounds the average to 4 in
this case. The library's 0..10 storage scale is a different contract. Phase 8
finding F05 is therefore withdrawn, not fixed by doubling source ratings.

All 119 ordinary tests execute from a disposable checkout ZIP under Calibre
9.17.0 / embedded Python 3.14.8. Result: 118 passed, no failures/errors/skips,
one unchanged advanced-parser expected failure. Separate Camoufox fixture
tests: 24 passed. No real browser or worker process is launched. Existing
homonymous coauthor, alias, ordering, series/edition/ID and transport tests
remain passing. See docs/PHASE9A.md for policy and evidence limitations.

## Phase 9B: execution and reliability

`reliability.py` adds 26 offline tests. Complete result: 145 executed, 144
passed, no failures/errors/skips, one unchanged advanced-search expected
failure. Calibre 9.17.0 / embedded Python 3.14.8; separate Camoufox fixture
suite: 24 passed, no real browser/worker process launched.

Coverage includes canonical URL aliases, distinct editions/title IDs, duplicate
limits and cross-strategy worker counts; pre-cancelled IDs/covers, cancellation
while preparing workers, during response reads, during a gated active request,
and after image bytes arrive; partial worker failure and worker-local settings;
concurrent exact/normal preferences, errors/fallback/cancel persistence; cached
publication covers, ISBN-10/13 cache relationships, title/author fallback,
multiple/empty/duplicate covers and limits; explicit Notes issue numbers, ASIN
locale/affiliate paths, title tags, and childless lxml fallback responses.

The gated active-request test demonstrates that identify returns after cancel,
the blocked thread remains active until its read completes, then terminates
without a late result or extra request. It does not demonstrate forcible socket
interruption. The cover test similarly proves late raw image bytes cannot enter
the public queue after cancellation through the plugin entry point.

The inherited Calibre downloader's actual raw-byte contract is tested with an
in-memory PNG from Calibre's bundled Pillow and non-image bytes. Both are
transported by Source; image decoding is a later consumer boundary. No Pillow
installation or new testing dependency was added. Do not infer image validation
or live CDN/ISFDB availability from these tests.

Two old characterization tests were replaced with stronger persistence
assertions: exact_search no longer writes the disposable preferences file, and
advanced-search fallback no longer overwrites max_results/max_covers. This is
an intentional approved Phase 9B behavior correction, not weakened coverage.
No new skips/expected failures were added. All Phase 9A correctness tests pass.
