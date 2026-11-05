# ISFDB4 Phase 8 independent audit — 2026-11-04

## Executive decision

The offline baseline is reproducible, but it is not sufficient evidence for a
production replacement or public release. Eight correctness failures were
reproduced with additional disposable probes; several other defects are
established by source inspection. No Critical finding was established.

| Proposed action | Decision | Conditions |
|---|---|---|
| A. Create a Git commit | GO as an explicitly labelled development checkpoint | Stage reviewed source, tests, fixtures and provenance together; record the known defects and expected failure. Do not call this a release-ready commit. This audit performs no commit. |
| B. Install a disposable build into isolated Calibre | GO for controlled diagnosis | Start Calibre with configuration/cache/temp redirected before process startup; use no production library or copied live preferences; inspect the ZIP manifest; keep offline fixtures as the first gate. Installation is not performed here. |
| C. Replace live ISFDB4 | NO-GO | Resolve F01–F08 and the configuration/packaging concerns, exercise covers and controlled cancellation, then validate a reviewed artifact in isolated Calibre. Explicitly decide TLS policy before live replacement. |
| D. Public release | NO-GO | Satisfy C; resolve or explicitly scope/document remaining parser, query, pagination and identity limitations; validate declared minimum/platform support; make reproducible license-bearing packaging; complete attribution/release documentation and separately authorized controlled network validation. |

The advanced-search expected failure is not proof of a live-site parser defect.
Camoufox remains NO-GO for production; no browser integration is recommended.

## Baseline, inventory and change attribution

Repository: `C:\Users\apt\Git\Calibre-ISFDB4\isfdb4-calibre`.
Branch: `main`. HEAD and locally stored `origin/main` are both
`759c404b7ac93b499ff0c1b2ecc4ab657c6b6b20`. No fetch was performed, so this
does not certify the remote server's current tip.

There are 20 tracked files and 18 untracked files (38 total in inventory.json).
No tracked deletion, missing inventoried file, or lost baseline test/document
was found. Earlier phase-to-phase preservation cannot be reconstructed as
commits because those additions are still untracked; inventory and the current
test counts provide present-state evidence, not an immutable phase history.

Production Python consists of __init__.py (1,600 lines, 20 function definitions),
objects.py (3,062 lines, 42 definitions including nested helpers), and
myglobals.py (431 lines, one dummy translation function). There is no config.py;
Calibre Source options provide the configuration UI. Imports, entry points,
search/record/series/cover paths and shared constants were reviewed, along with
all test modules, fixtures, launchers and the tracked working-tree diff.
No formal branch-coverage measurement or proof of every possible HTML layout
is claimed. The commented ISFDBWebAPI sketch is not an implemented transport.

Tracked modifications are exactly README.md, __init__.py and objects.py.
Untracked inventory:

```
docs/CAMOUFOX_FEASIBILITY.md
docs/UPSTREAM_PROVENANCE.md
tests/README.md
tests/author_edges.py
tests/camoufox_feasibility.py
tests/http_diagnostics.py
tests/phase4_cases.py
tests/run.ps1
tests/run_calibre.py
tests/run_camoufox_feasibility.ps1
tests/unicode_correctness.py
tests/fixtures/author_bibliography.html
tests/fixtures/author_search.html
tests/fixtures/publication.html
tests/fixtures/restricted_search.html
tests/fixtures/search.html
tests/fixtures/simple_search.html
tests/fixtures/title.html
```

Tracked IDE files (.idea), Git attributes/ignore rules, three batch launchers,
import-name marker, GPL LICENSE and German translations are present.
The __pycache__ directory is empty; no bytecode file was introduced by the
successful isolated tests/probes. There is no release build script that makes
an audited standalone distribution without also installing it.

Cumulative phase mapping supported by the diff and documentation:

- Phase 1: disposable ZIP/Calibre loader tests and fixtures.
- Phase 2: genuine author-only bibliography dispatch and missing-title handling.
- Phase 3: edge-case characterization and unresolved advanced-table evidence.
- Phase 4: explicit author identity/provenance, candidate bounds, coauthors,
  atomic unsupported-query rejection and empty-body handling.
- Phase 5: provenance ledger and upstream comparison, not production integration.
- Phase 6A: original-exception-preserving open/read diagnostics.
- Phase 6B: separate fixture-only Calibre browser contract experiments.
- Phase 7: exact-spelling priority, diagnostic detail and ordered credit IDs.

The existing urllib transport, SSL bypass, 90-second minimum, collision title
qualification and some search preference changes predate these uncommitted
phases. Do not attribute all HEAD-relative behavior to Phase 7. The additions
match the described phase scope; no unrelated production module modification
was found. Functional review nevertheless found the newer merge regression F02.

## Verified correctness findings

All paths/line numbers below refer to the current checkout. Block labels mean
recommendations for live replacement/public release, not a ban on an honest
development checkpoint or a diagnostic isolated installation.

### F01 — High — custom templates can discard usable metadata

- Location/component: __init__.py:599, ISFDB4.clean_downloaded_metadata.
- Evidence/reproduction: set title_template to `{title} - {authors}` and retrieve
  the existing standalone title fixture by ID. The template unconditionally
  calls replace('{series}', mi.series), even without that placeholder. With
  series=None this raises TypeError; Worker logs the error and returns no result.
- Expected/actual/impact: a valid custom title should be returned; actual queue
  length is zero. This affects any non-default template on such records.
- Origin/coverage: inherited from HEAD; the baseline tests use the default
  template and do not detect it. Advertised main_series/series_code placeholders
  are also not implemented in this method.
- Correction/tests: handle optional fields as strings, validate numeric format
  specs, document supported placeholders; test standalone/series records,
  absent optional fields, each placeholder and invalid user format.
- Gate: blocks live replacement and public release.

### F02 — High — contained-work authors become publication authors

- Location/component: __init__.py:1374, Worker.run credit merge.
- Evidence/reproduction: link a Story Writer title to an anthology edited by
  Ada Example. The disposable probe returns title `Offline Anthology` and
  authors `['Ada Example (editor)', 'Story Writer']`.
- Expected/actual/impact: anthology credits should describe the publication;
  membership of a contained story in its publications list does not establish
  that its author is an author/editor of the whole anthology. The append-all
  merge silently changes authorship of a different work.
- Origin/coverage: introduced by cumulative Phase 4 credit merging and retained
  by Phase 7; baseline credit tests model matching works, not containment.
- Correction/tests: distinguish same-work editions from containers and preserve
  roles. Do not remove valid homonymous coauthors or same-ID alias suppression.
  Add anthology/magazine/collection containment tests and matching-work tests.
- Gate: blocks live replacement and public release. This requires a narrowly
  specified metadata merge policy before coding, not a blanket reversal.

### F03 — Medium — decimal series indices are corrupted

- Location/component: objects.py:2568, Title.from_url; analogous publication
  conversion at objects.py:1420 (digit-filter branch).
- Evidence/reproduction: change Series Number in the existing series fixture
  from 2 to 1.5. Actual parsed value is 15.0. Code removes all non-digits before
  int conversion, also destroying signs. The slash/Roman cases are intentional
  separate policies and should remain explicit.
- Expected/impact: preserve a valid Calibre numeric value 1.5 rather than 15;
  otherwise metadata sorts into the wrong series position.
- Origin/coverage: inherited; tests check integer indices only.
- Correction/tests: parse validated decimal numeric forms first; separately
  document combined-issue and Roman conversion. Test 1.5, -1, integers, Roman,
  61/62, unnumbered and malformed values in both record parsers.
- Gate: blocks live replacement/public release until corrected or the affected
  functionality is explicitly removed from the release scope.

### F04 — Medium — publication merge loses title series but retains its index

- Location/component: __init__.py:1368 and 1391; objects.py:2054 (publication
  fallback initializes series to the empty string).
- Evidence/reproduction: publication fixture without series plus a matching
  title fixture with Offline Cycle #2 yields series='' and series_index=2.0.
  Checking key existence rather than a meaningful value prevents the title
  series fallback; tit.update(pub) overwrites it with ''.
- Expected/impact: series and index should come from one coherent source;
  current output silently drops useful metadata and leaves an orphan index.
- Origin/coverage: inherited; series tests do not cover this combined path.
- Correction/tests: define empty/missing precedence and merge series/index as a
  pair; test publication absent/present/conflicting/unknown series and indices.
- Gate: blocks live replacement/public release.

### F05 — Medium — ratings are halved on Calibre's metadata scale

- Location/component: objects.py:2644, Title.from_url User Rating.
- Evidence/reproduction: fixture rating 9.00 becomes Metadata.rating=4.5.
  The code converts to five stars even though this field uses a ten-point
  internal scale (the adjacent production comment itself explains this).
- Expected/impact: preserve 9.0 internally; otherwise displayed rating is too low.
- Origin/coverage: inherited; no rating assertion in baseline.
- Correction/tests: agree on numeric scale, validate range and no-vote/integer
  representations; assert actual Metadata.rating and isolated UI display.
- Gate: blocks live replacement/public release of advertised rating retrieval.

### F06 — Medium — one publication can spawn duplicate workers/results

- Location/component: __init__.py:663, 735, 1006 and 1105, _identify.
- Evidence/reproduction: ISBN yields publication 202 at relevance 1; title
  expansion finds that same URL at relevance 0. matches stores (URL,relevance)
  pairs, so both remain. Probe returns title 101 and TWO copies of pub 202.
- Expected/impact: one worker/result per stable record ID, best relevance kept;
  actual duplication wastes requests and consumes useful result allowance.
- Origin/coverage: inherited; tests deduplicate within bibliography candidates
  but not across search strategies. Collision qualification does not deduplicate
  identical IDs and must preserve distinct edition IDs.
- Correction/tests: use canonical record identity to retain best relevance;
  test ISBN/title overlap, multiple titles sharing a publication, ordering and
  distinct editions. Assert request counts as well as resulting IDs.
- Gate: blocks live replacement/public release.

### F07 — High — cancellation is incomplete and workers outlive identify

- Location/component: __init__.py:669, 1126 and 1133; objects.py:532,
  TitleList.from_author; Worker has no abort argument.
- Evidence/reproduction: a pre-set abort with a title identifier still makes
  one fetch and delivers one metadata result. The search-only pre-abort test
  passes because it exercises a different branch. Source confirms workers all
  start with 0.1-second spacing without cancellation checks; an abort exits the
  join loop, not the daemon workers. The log then incorrectly says all ended.
- Expected/impact: no new work after cancellation; clear reporting of in-flight
  work. Actual workers can continue fetching and updating shared caches after
  the invocation returns. Candidate enumeration has no abort checks either.
- Origin/coverage: inherited worker lifecycle plus newer author path using the
  same contract; baseline covers search-only pre-abort, not these cases.
- Correction/tests: check cancellation on all dispatch/start/forward boundaries,
  pass a cancellation signal through page loops and stop scheduling new work.
  Preserve the intentional 90-second request floor; do not promise immediate
  interruption of blocking urllib by merely setting an Event. Test controlled
  blocked requests, pre-cancelled IDs, mid-scan abort, no late cache/queue writes
  and bounded worker startup. Do not use live stalled network tests.
- Gate: blocks live replacement/public release; diagnostic isolated install GO.

### F08 — Medium — malformed-but-usable records are dropped for missing tags

- Location/component: __init__.py:1483–1492, Worker.run; objects.py:2383/2449.
- Evidence/reproduction: remove the Type field entirely from title.html while
  retaining title, author, date and language. Worker raises KeyError('tags') and
  queues no result. An empty Type value also produced zero results.
- Expected/impact: keep valid core metadata with an empty optional tag list;
  current handling turns a missing optional field into total record loss.
- Origin/coverage: inherited; existing malformed tests cover different shapes.
- Correction/tests: explicit parser result schema/defaults, validation of core
  fields and defensive worker access; test missing Type/Length/Tags independently
  for titles/publications and mixed successful/failed workers.
- Gate: blocks live replacement/public release.

## Additional source-established defects and intentional limits

### F09 — Medium — publication Notes regex/issue-number branch is inconsistent

- Location: objects.py:1590–1622, Publication.from_url Notes.
- Evidence/conditions: pattern has THREE capture groups but code refers to
  group(4) after group(3). If that branch is reached it must raise IndexError;
  greedy optional grouping can also skip issue detection. issue_no_only with
  no separately captured issue uses initialized zero, not the No. value.
- Expected/impact: documented `Vol. 4, No. 3. Issue 22` policy should produce
  the explicit issue number; current branch cannot read the intended group.
- Coverage/origin: inherited; no direct notes/issue correctness tests found.
  This is source-established; reachability and exact realistic layouts require
  focused fixtures, not a claim of an observed live failure.
- Fix/tests/gate: define captures and precedence, then test both preferences,
  explicit issue, absent issue, Roman volume and large issue. Blocks public
  release of the advertised periodical-number feature; no block on checkpoint
  or diagnostic installation.

### F10 — Medium — ASIN locale fallback is outside its exception handler

- Location: objects.py:1877, Publication.from_url External IDs.
- Evidence/conditions: catalog_countries.index(LOCALE_COUNTRY) precedes the
  try intended to fall back to US/first link. If the country is absent,
  ValueError escapes to the whole-section handler and skips the intended fallback.
  Taking the final ten characters of an affiliate URL is also not a reliable
  ASIN extraction rule when query parameters exist.
- Expected/impact: choose a valid available link and parse its /dp/<ASIN> path;
  actual code can lose external IDs or derive an incorrect ASIN.
- Coverage/origin: inherited; untested locale/affiliate cases; confirmed control
  flow defect, not a newly verified live ASIN incident.
- Fix/tests/gate: narrow exception scope, validate identifiers and locale
  fallback; test missing country, US-only, affiliate URLs, multiple catalogs.
  Public-release blocker; permit isolated diagnosis and checkpoint.

### F11 — Medium — parser-local state is persisted into user preferences

- Location: objects.py:853–854, TitleList.from_url; __init__.py:653 exact_search;
  objects.py:1622 series_index_options; __init__.py:392 obsolete AI-key deletion.
- Evidence/conditions: advanced-search restriction fallback sets max_results and
  max_covers to 300. Existing test_simple_fallback_parsing_and_existing_preference_writes
  explicitly expects this; it is characterization, not correctness. exact_search
  is also stored on every lookup, and parsed data may alter series preference.
- Expected/impact: distinguish per-request policy from user settings. Current
  code can increase network load and change later searches/covers, including
  shared-worker races. Caches use cache_lock, but prefs is shared with workers.
- Origin: inherited behavior preserved during prior phases, not an unexpected
  Phase 7 change. AI preference migration is intentional existing behavior.
- Fix/tests/gate: obtain agreement on compatibility before moving temporary
  state to per-invocation values; retain user defaults and approved migration.
  Test unchanged preference files across concurrent queries and fallback.
  Blocks live replacement/public release pending explicit policy decision.

### F12 — High — inherited TLS authentication is disabled

- Location: objects.py:208, fetch_isfdb_url; __init__.py:152 ignore_ssl_errors.
- Evidence/conditions: _create_unverified_context accepts an untrusted server
  certificate; inherited mechanize settings also ignore SSL errors. A network
  attacker able to intercept traffic could replace metadata or linked URLs.
- Expected/impact: TLS normally authenticates the peer; current intentional
  compatibility policy does not. No exploitation or certificate failure was
  tested, and this was not introduced by Phase 6A/7.
- Coverage: tests explicitly preserve the unverified context, not its security.
- Recommendation/tests/gate: separate authorized TLS policy review; do not
  silently change it in correctness fixes. Test trusted/untrusted/expired
  certificates on a controlled local endpoint and assess compatibility. Public
  release needs a documented, approved resolution; live replacement needs an
  explicit informed policy decision. No TLS changes made by this audit.

### F13 — Medium — unbounded I/O and insufficient URL boundaries (risk)

- Location: objects.py:219–244 fetch_isfdb_url; 1360 Series.from_url call;
  1456 auxiliary archive fetch; __init__.py:1110 worker creation.
- Evidence/conditions: no response byte cap or total deadline; urllib follows
  redirects without a plugin host/scheme validator. HTML-derived series and
  cover URLs are trusted; archive fetching checks the displayed link name.
  max_results up to 300 can create that many metadata threads. A default author
  scan can examine up to 500 empty candidates, each with a minimum 90-second
  socket timeout. Socket timeout is not an overall operation deadline.
- Impact/status: potentially excessive memory, latency and unintended URL
  access from malicious/changed HTML, especially with F12. No demonstrated
  exfiltration, exploit, native resource leak or real timeout duration is claimed.
- Coverage/origin: inherited architecture plus bounded author scan; no stress,
  redirect/scheme or total-budget tests. Current tests mock bytes and timing.
- Recommendation/tests/gate: after separate approval, define URL policy,
  bounded concurrency, response limits and overall scheduling budget while
  preserving request timeout semantics. Test local redirects, forbidden schemes,
  large bodies, slow streams and cancellation. Public-release risk decision
  required; not a barrier to offline isolated diagnosis or checkpoint.

### F14 — Medium — title tags and some linked fields are not parsed as elements

- Location: objects.py:2391, 2656–2660, Title.from_url Current Tags.
- Evidence/conditions: detail_nodes entries are lists such as ['Current Tags',
  text]. The later comprehension iterates those strings and accesses e.tag,
  which raises AttributeError whenever the non-'None' Current Tags branch runs.
  Variant Title of handling similarly mixes list strings with .tail at 2674.
- Expected/impact: real tags/variant notes should survive; exceptions are logged
  and fields silently omitted. Type-derived tags can mask missing real tags.
- Coverage/origin: inherited; fixtures have no positive Current Tags case.
- Fix/tests/gate: use a consistent node/value representation and verified field
  fixtures; test actual tag links, none/empty, tooltips, variant links. Public
  release blocker; allow checkpoint and isolated investigation.

### F15 — Low — one lxml Element truth test changes meaning in future lxml

- Location: objects.py:859, TitleList.from_url fallback, `if not root`.
- Evidence: baseline emits FutureWarning here. Current Element falsiness depends
  on child count; future truthiness will always be true for existing elements.
  This is the only direct Element truth-test pattern identified in production.
  `if not cb`, rows/links/detail_nodes/notes_nodes tests operate on XPath lists;
  prev_node is None and root is None elsewhere are already explicit.
- Expected/fix: use root is None for absence; use len(root)==0 only if intentional
  childlessness is the criterion. These are not equivalent: <p>text</p> is valid
  yet childless. Add absent, childless-with-text, and empty-document cases.
- Origin/coverage/gate: inherited, warning detected but not made test-fatal.
  Not a checkpoint/isolated-install blocker; fix before broad compatibility
  claims. Advanced parser must remain unchanged pending separate authorization.

### F16 — Low — unused helper would fail if activated

- Location: __init__.py:51, apply_isfdb_headers.
- Evidence/conditions: ISFDB_REQUEST_HEADERS is undefined. No production call
  was found; urllib correctly uses objects.ISFDB_HTTP_HEADERS instead.
- Expected/impact: a future caller would get NameError; current metadata fetches
  are unaffected. Browser headers and urllib headers are separate transports.
- Coverage/origin: inherited dormant code, no test.
- Recommendation/tests/gate: remove or define only in an explicitly scoped
  cleanup; never wire it into Camoufox. No current installation/commit blocker.

## Test, packaging and documentation findings

### F17 — Medium — a passing baseline omits important advertised behaviors

- Location: tests/run_calibre.py:66, tests/phase4_cases.py:121 and
  tests/camoufox_feasibility.py:153–223.
- Evidence: all baseline tests pass despite F01–F08. Few fixtures represent
  independent real-world layouts. Many orchestration tests bypass parsing by
  mocking parsed dictionaries. No ordinary cover retrieval/download assertion,
  rating, decimal-number, real template or cross-strategy dedup test was found.
  Exact-header equality compares requests to the current production constant,
  so a changed constant can pass; it is not an immutable header snapshot test.
- Positives: exact ZIP hashes and module origins are checked; fresh plugin and
  preferences per test; exception identity, traceback and real Calibre logger
  tests are strong; mock context managers restore patched functions.
- Reproducibility: ordinary suite is synchronous and offline; worker completion
  order can still vary. Camoufox tests use gates and fake pages, but some depend
  on async timing and are not proof of native browser behavior.
- Isolation: launchers set disposable paths BEFORE Calibre starts; ordinary
  hook blocks sockets/DNS/processes/SQLite and audited writes. Feasibility allows
  loopback control sockets and forbids actual browser/worker launch. Hooks are
  not OS sandboxes and do not cover arbitrary native/unaudited filesystem APIs.
  Ordinary runner does not clear inherited CALIBRE_METADATA_BROWSER_WORKER,
  unlike feasibility runner; no use of that endpoint was observed here.
- Action/tests/gate: add correctness tests for findings, explicit cover fixtures
  and download boundaries, shuffled test order/multi-worker cases and malformed
  positive fields. Public-release blocker, not a development checkpoint blocker.

### F18 — Medium — build/install commands do not provide a safe release artifact

- Location: plugin_install.bat:1, dev_install_and_restart.bat:4/8/12;
  tests/run_calibre.py:48–54; installed calibre.customize.ui.build_plugin:943–959.
- Evidence: both batch builds use calibre-customize -b ., which installs.
  Restart script force-kills calibre.exe and launches the GUI; debug.bat launches
  calibre-debug -g. None were executed. Read-only disassembly of the installed
  build_plugin confirms recursive add_dir and add_plugin; the supplied filter
  excludes only .git/.svn/.hg/.bzr. Thus tests, docs and .idea are not excluded
  by that filter. This conclusion does not require executing the installer.
- Harness ZIP: explicit six-file manifest (three Python files, marker,
  translations/de.mo and de.po) loads successfully from this checkout. Tests,
  credentials and development files are absent; LICENSE and provenance are
  also absent. It is a disposable test artifact, not a distributable release.
- Reproducibility: test ZipFile.writestr uses current timestamps, so input hash
  identity does not imply bit-for-bit reproducible ZIP bytes. No manifest-driven
  license-bearing public package was verified.
- Action/tests/gate: add a separately authorized non-installing allowlist builder,
  include license/notices and appropriate attribution, fix timestamps/order and
  reject unapproved entries; compare two ZIP hashes and test loader against the
  exact artifact. Block public release and unreviewed live build scripts; allow
  isolated diagnostic install only after explicit manifest inspection.

### F19 — Medium — declared compatibility exceeds the evidence

- Location: __init__.py:59–65, platforms and minimum_calibre_version.
- Evidence: declares Calibre >=5.0 and Windows/Linux/Mac; tests pin 9.17.0 on
  Windows/Python 3.14.8. All current imports load there, without new third-party
  dependencies. No 5.0 runtime or Linux/macOS execution was tested.
- Risk/status: this is an unsupported compatibility claim, not proof that old
  Calibre fails. Ordinary tests are intentionally version-pinned; feasibility
  tests use newer APIs/annotationlib but are excluded from the plugin ZIP.
- Action/tests/gate: validate the claimed matrix or narrow supported versions
  in a separately approved change. Exercise config widget, cover capabilities,
  caches and installation in isolated 9.17 first. Public-release blocker for
  broad compatibility claims; target-runtime isolated install GO.

### F20 — Low — user-facing docs and release metadata are stale/incomplete

- Location: tests/README.md:3, __init__.py:60/212, README.md:37 and
  docs/UPSTREAM_PROVENANCE.md:14.
- Evidence: test README's top 'Current Phase 6A' count is 88, while Phase 7
  appended section correctly says 102. Config help refers to missing isfdb4.md.
  Version is 1.4.14; release field says 02-09-2026 while README says 05-18-2026.
  Older first-person README narrative describes creating ISFDB3, not this fork.
  Provenance snapshot hashes/line references are explicitly historical, not
  hashes of the present Phase 7 tree.
- Action: retain historical evidence but add a clear current entry, reconcile
  release metadata when release work is authorized, fix help reference and make
  fork lineage explicit. Do not bump version in this audit. Verify modified-file
  notices/dates are appropriately carried in distribution, not only test docs.
- Gate: no development/isolated-install block; public-release documentation gate.

## Known limitations retained without speculative fixes

### F21 — Medium — advanced-table contradiction, live format unverified

- Location: objects.py:1091 language filter and 2192 title stub;
  tests/run_calibre.py:208 expected failure.
- Evidence: the synthetic table places title and language differently from
  one parser's assumptions; both title access and language filter use td[5].
  The expected failure demonstrates internal inconsistency, not the authorized
  ISFDB HTML format. No live HTML or registration bypass was attempted.
- Required evidence/tests: a permitted, dated, redacted real result table with
  headers and row, matching request/response charset and registration context.
  Then decide whether code, fixture or both are wrong; retain simple-search
  regression coverage. Do not invent layout or fix production from this test.
- Gate: not a diagnostic-install/checkpoint blocker; public release must scope
  advanced search as unverified or resolve it with evidence. Preserve xfail.

### F22 — Informational — supported query encoding is intentionally limited

- Location: objects.py:53–64 encode_query, __init__.py:617 wrapper.
- Verified: Latin-1 parameters/order and NFC composition work; unsupported
  Cyrillic/Greek/CJK, curly punctuation and non-composing combining marks fail
  atomically with parameter and U+codepoint diagnostics before transmitting.
  No UTF-8 CGI support was established. ID retrieval can preserve non-Latin
  metadata via numeric HTML references; that is different from name searching.
- Tests: fourteen Phase 7 tests plus prior query/ID cases. The wrapper logs the
  controlled failure and returns no metadata; callers see a logged unsupported
  search, not an invented broader query. No truncation fallback remains.
- Recommendation/gate: document the limit in user-facing release notes, preserve
  explicit IDs and avoid transliteration/NFKC/confusable folding. No blocker
  for a release explicitly scoped this way; full Unicode search is not ready.

### F23 — Medium — unlinked homonyms/roles cannot be reliably disambiguated

- Location: __init__.py:1376–1385; objects.py:67 and 1259.
- Evidence/conditions: ordered linked credits distinguish stable IDs, preserve
  order and aliases, as the Phase 7 tests show. Name fallback collapses equal
  unlinked names when one/both IDs are absent; publication parser only gathers
  linked authors, so unlinked coauthors can be omitted there. Partial-name
  bibliography ambiguity is annotated, but credit-level ambiguity is not.
- Risk/status: identity is unknowable from name equality alone; do not treat
  equal display strings as established equal persons. No live misattribution
  was observed; missing-link behavior follows directly from parser/merge code.
- Action/tests/gate: preserve credit provenance/roles, explicitly flag ambiguity
  and test linked/unlinked mixed credits, same-name distinct IDs and aliases.
  Public release needs documented policy and coverage; not a checkpoint or
  offline diagnosis blocker. Do not undo Phase 4 stable identity separation.

## Attribution, licensing and upstream review

LICENSE contains the complete GPL version 3 text. Existing tracked copyright
and attribution content was not removed by this diff. The provenance ledger
correctly separates Michael Detambel/bertholdm's ISFDB3 b8ff4a0 contribution,
earlier ISFDB3 changes, Kovid Goyal's Calibre exception/API work and local
ISFDB4 modifications. Phase 6A source comments credit diagnostic intent;
Calibre exception classes were not copied. No Camoufox integration claim was
found in current implementation documentation. The feasibility document
explicitly says NO-GO and theoretical benefit, not demonstrated site access.

The ISFDB2 lineage acknowledgments include Adrianna Pińska, Xtina Schelin,
Brian Schweitzer and Grant Drake in the provenance file; README should link
these clearly and also explicitly identify the ISFDB3 intermediate fork.
Keep RealLactar's documented contributions separate from upstream Git authors.
No new external source was incorporated during this audit, and no upstream
network history was fetched. Earlier verified ledger findings were reviewed
for consistency; exclusive ownership, absent coauthors and exact February
import provenance remain unresolved as stated there. A Git author is not
proof of sole authorship. Do not call inherited/adapted code original ISFDB4.

Before distribution, carry GPL text, applicable notices, modification dates
and corresponding source/access with the actual release artifact. The test
ZIP alone does not establish distribution compliance. This is an engineering
readiness review, not a new legal interpretation of uncertain ownership.

## Network, covers, dates and architectural assessment

No transport code was changed. Existing Chrome-style urllib headers, TLS
bypass, minimum 90-second timeout, zero automatic retry additions, original
exception diagnostics, browser cloning and thread design remain as inspected.
403 messages report status without asserting Cloudflare causation. Connection,
wrapped timeout and read errors preserve exception identity/traceback. Empty
successful bodies deliberately produce an empty HTML root, whereas transport
failures propagate from the fetch helper and are logged at the worker boundary.

Covers use the inherited Calibre download path and cached URLs, while record
HTML uses urllib. Browser clones therefore do not make the record transport a
cookie-aware mechanize session. Covers/auxiliary archive requests have separate
transport semantics and need their own tests; do not assume the record fetch's
90-second floor applies there. A 403 in one path does not establish a 403 in
all paths. No live availability, 403 workaround success or cover image content
was tested, and no Camoufox benefit was demonstrated.

Missing title dates are tolerated; placeholders are converted to Jan 1 and
02:00 on naive datetime objects. This is inherited policy. Publication Notes
may infer dates from seasons/months; case-insensitive regex captures are fed
to case-sensitive name lists, and accesses to missing pubdate can skip later
note extraction. These are additional fragile paths to cover alongside F09,
not a demonstrated universal date failure. The date_text variable is reset
per detail row, making the intended year/month series fallback dependent on
field order. Add tests for unknown/absent dates, seasons, month case and series
appearing before/after Date before changing these rules.

HTML comments use sanitize_comments_html in selected publication sections,
but not every subsequently concatenated text/URL field passes through it.
The new ambiguity links do escape URL and display text. No executable-HTML
exploit was established; test final comments sanitization with controlled
markup rather than claiming all response HTML is uniformly sanitized.
Diagnostic URLs/preferences can contain search titles, author names or proxy
error details. No active credential leakage was found; do not publish raw logs
or historical configuration/commit contents without redaction. Current code
does not activate the abandoned AI enrichment; existing migration deletes
obsolete AI settings on initialization.

Result selection prioritizes early bibliography dates and preserves ties in
that input list, including the intentional undated-first policy. Queue output
still depends on unordered matches and worker completion. Pagination is not
implemented, so server first-page caps and language defaults can omit results;
max_results is a ceiling, not evidence that the best or all matches were found.
Full author searches with known stable IDs avoid name encoding but still filter
languages. Retain this distinction in release documentation.

## Executed validation and safeguards

- `.\tests\run.ps1`: 102 executed, 101 passed, 0 failures, 0 errors, 0 skipped,
  1 expected failure, 0 unexpected successes; 9.597 seconds reported by unittest.
- `.\tests\run_camoufox_feasibility.ps1`: 24 passed, 0 failures/errors/skips;
  zero real browser or worker processes launched. It tests installed dispatch,
  fake-page lifecycle and failure conversion, not native browser/IPC behavior.
- Both ran with Calibre 9.17.0, embedded Python 3.14.8, MSC v.1950 AMD64,
  calibre-debug.exe at C:\Program Files\Calibre2\calibre-debug.exe.
- Additional disposable probes reproduced F01–F08. Positive control: a properly
  populated single-title redirect DID return one record; an earlier incomplete
  audit fixture returned zero, and is not counted as a redirect defect.
  Nested linked-credit extraction also passed. See probe-results.json.
- Installed build_plugin was disassembled read-only because inspect.getsource
  is unavailable in the frozen installation. It was never called.

Audit caveat: the first auxiliary probe set config environment variables inside
the Python script, too late for Calibre startup. Installed plugin modules were
loaded read-only and the attempt failed due to the already-loaded old objects
module. A temporary certificate resource cleanup was blocked by the later audit
hook. The launcher was corrected to set every disposable variable before
calibre-debug started; all successful probes used that setup. No install,
configuration-write operation or library access was invoked by the probe.
The initial attempt is NOT counted as evidence of successful isolation. There
was no before/after snapshot of live configuration for that failed startup,
so absence of all automatic startup side effects cannot be certified. The
probe itself issued no live configuration writes; this narrower statement
must not be read as proof about every installed plugin's startup behavior.

No repository source, test or documentation file was edited. All generated
audit files and successful probe config/cache/temp/ZIP artifacts are under
this clearly identified disposable audit directory. The simple source index
is at %TEMP%\isfdb4-phase8-index.txt. No live ISFDB or external HTTP request,
dependency download, native browser launch, plugin installation, library access,
commit, push, reset, stash or cleanup/discard operation was performed.

## Ranked proposed Phase 9 plan — not started

1. Add focused correctness tests reproducing F01/F02/F04/F06/F08 before fixes.
   Decide same-work versus contained-work credit/series precedence first; retain
   stable IDs, legitimate aliases, author order and edition distinctions.
2. Correct optional template values, optional metadata defaults, deduplication,
   rating scale and numeric series parsing (F01–F06/F08). Each correction should
   be a separately reviewable patch with failing-before/passing-after evidence.
3. Repair cancellation/scheduling (F07) without silently reducing per-request
   timeouts. Add gated worker tests and immutable per-request state proposal for
   F11; obtain agreement for intentional preference behavior changes.
4. Address field/periodical/external-ID parsing (F09/F10/F14/F23) with truthful
   fixtures. Add cover/caching and mixed success/failure tests. Keep the advanced
   parser untouched until permitted real-table evidence is available.
5. Conduct a separately authorized TLS/URL/resource policy review (F12/F13).
   Do not bundle networking policy changes into correctness remediation.
6. Build a non-installing deterministic, license-bearing artifact pipeline;
   inspect manifests/hashes, exercise loader and isolated installation, verify
   config migration and update accurate help/lineage/compatibility documentation.
7. Only after a new review: authorize controlled real transport/cover smoke
   tests with disposable configuration, documented request budget and permitted
   endpoints. No access-control bypass. Then revisit live/public release gates.

## Final Git evidence

```
 README.md   |  18 ++++++
 __init__.py |  75 +++++++++++++++++++---
 objects.py  | 210 +++++++++++++++++++++++++++++++++++++++++++++++++-----------
 3 files changed, 257 insertions(+), 46 deletions(-)
```

These are cumulative tracked differences against HEAD, not Phase 8 edits;
untracked docs/tests are excluded by git diff --stat. git diff --check exits 0
with no output. Status remains M README.md, M __init__.py, M objects.py and the
18 untracked files listed above. No Phase 9 implementation was begun.
