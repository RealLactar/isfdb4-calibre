# Phase 9B reliability and execution — 2026-11-05

Status: complete for the scoped corrections and offline verification, with
explicit limitations below. Phase 9A corrections are preserved. No Phase 9C,
release, live installation, external request, dependency installation, user
configuration/library mutation, commit, push or destructive Git operation.

## Review and confirmed corrections

All 23 Phase 8 findings were reviewed with PHASE9A.md, UPSTREAM_PROVENANCE.md
and CAMOUFOX_FEASIBILITY.md. The original audit remains unchanged; later
corrections/errata are recorded separately. Current repository HEAD remains
759c404b7ac93b499ff0c1b2ecc4ab657c6b6b20, branch main.

### Canonical requests/results (F06)

Root cause: a set of (URL,relevance) pairs admits multiple entries for the same
record when search strategies disagree about relevance or URL spelling.
RecordMatches now keys by canonical record URL, retains the best relevance,
and enumerates deterministically by relevance then URL. Known numeric title/pl
URLs normalize HTTP/HTTPS, www/no-www, leading zeros and view/fragment suffixes.
Unrecognized URLs retain their spelling; no arbitrary host is treated as ISFDB.
Titles and publications are distinct identities; publication 202 and 203 remain
distinct editions. Existing publication-to-title relationship caches are kept.

ISBN plus linked-title expansion now creates one publication worker rather
than two. Duplicate links do not consume additional result allowance. Worker
completion results are sorted before collision qualification/public forwarding,
so network completion timing does not determine final equal-relevance order.
Date-based candidate selection before the limit remains in place. Equal worker
results now have a stable URL tie-break rather than historical completion order.
This is an intentional ordering improvement, not a promise of complete results
across server pagination limits. It does not add retries or page downloads.

### Cooperative cancellation and lifecycle (F07)

Public identify/download_cover return before dispatch if already cancelled.
Each request carries its own abort Event in an in-memory settings snapshot.
ISFDBObject.root_from_url checks before and after the unchanged fetch helper;
the auxiliary archive request also has explicit boundaries. Nested parsing
handlers propagate SearchCancelled rather than treating it as a parse failure.
Worker preparation/start loops stop on cancellation; 0.1-second request spacing
uses Event.wait so cancellation need not wait out that delay. Worker errors
remain logged and successful sibling workers remain usable.

Workers check cancellation before parsing, metadata/cache publication and final
queue output. Cancelled invocations discard private pending results. The old
misleading 'all workers ended' message now reports the number still alive.
Calibre's cover downloader can enqueue bytes after cancellation; a small output
queue adapter drops those late completions. No Calibre implementation is copied
or modified, and the inherited cover scheduling/transport remains in use.

Important limitation: blocking urllib/mechanize operations are NOT forcibly
interrupted. Identify can return on cancellation while an already active daemon
thread finishes its read or encounters its existing timeout. On completion,
root cancellation checks prevent subsequent requests/parsing/results. Tests
gate a live Python thread on a mocked read, cancel, verify prompt invocation
return and then release/join the thread without late output. This proves the
cooperative boundary, not native socket interruption. Already-dispatched
Calibre cover jobs may also continue; late public output is suppressed.
Cancellation is cooperative, not an atomic barrier against an operation that
has already passed its boundary check. Existing per-cache locks are retained.

No thread pool redesign, native process, Camoufox integration or overall
deadline is introduced. Large request counts, finite socket inactivity rather
than total deadlines, and native resource cleanup remain future policy risks.

### Persistent preferences (F11)

Calibre JSONConfig stores defaults separately from saved keys. Identify/cover
snapshots merge defaults and saved values without saving either. exact_search
is a request flag; max_results/max_covers no longer become 300 on restricted
advanced-search fallback. Workers each receive a separate mutable dictionary
(sharing only the Event intentionally), and Publication.from_url copies its
working preferences even when invoked directly. Notes issue detection uses a
local effective option instead of changing series_index_options.

This deliberately changes the old defective behavior: fallback respects the
user's existing result/cover ceilings instead of persisting a larger ceiling.
Exact-search prefix behavior still applies to the current query. Existing
defaults, JSON format, saved legacy keys and intentional obsolete-AI-key
migration are unchanged; there is no new configuration migration.
Tests compare dictionaries/files after exact/normal/error/cancel/fallback
paths and run concurrent exact and normal lookups against the same plugin.

### Covers and caches

Confirmed inherited defect: ISBNs live inside pub['identifiers'], while the
worker checked only pub['isbn'] before caching. ISBN-only subsequent cover
lookups therefore missed a successfully cached publication image. The worker
now caches validated ISBN/ISBN-10/ISBN-13 aliases from the identifier dictionary
(or the old top-level representation) to that publication. The accidental
duplicate cache call is removed. Explicit publication IDs still take priority
and do not fall back to another publication's ISBN cache if their image is absent.

Cover candidates retain order, remove duplicate exact URLs/blank entries and
honor max_covers before dispatch. Cached publication images, title-based list
fallback, author-only identify-to-title fallback, multiple/empty responses,
lookup cancellation and raw-download cancellation are covered offline. An
in-memory valid PNG exercises the installed Calibre downloader without network.

Source.download_multiple_covers transports RAW bytes, even non-image bytes.
An initial test incorrectly assumed image decoding occurred there; inspection
and execution established the boundary, so the final test asserts byte fidelity
for both PNG and malformed data. No production behavior was changed merely to
satisfy that assumption. Final consumer image decoding, real image-server
availability/redirects and library cover application remain unverified. No new
URL allowlist, MIME policy or image-decoding dependency is introduced here.
ISBN-only cover association remains inherently ambiguous when different books
share an ISBN; explicit publication IDs protect that case, but cannot make an
ISBN alone uniquely identify an edition. This is an existing documented policy.

### Narrow, independently reproduced parser defects

- F09: Notes expected capture group 4 from a three-group regex and missed the
  explicit Issue 22 in 'Vol. 4, No. 3. Issue 22'. A separate explicit issue match
  now takes precedence; otherwise existing vol.no or no-only choice applies.
  No-only without explicit issue uses the available No. value instead of zero.
  Effective preference remains local. Existing volume/issue tests still pass.
- F10, ASIN subcase: missing local country raised before its fallback handler;
  taking the final ten URL characters also parsed affiliate query text as ASIN.
  Select local country, then US, then first; extract a validated ten-character
  ASIN from /dp/ or /gp/product/ path. Invalid paths are diagnosed and omitted,
  not converted into an invented identifier. Single-link/other catalog formats
  and the full external-ID matrix are not comprehensively redesigned.
- F14, Current Tags: detail_nodes stores values, not iterable HTML nodes;
  accessing e.tag on strings discarded tags. Retain the actual label element
  and collect its linked tags up to the next field boundary. Existing type tags
  and author parsing remain intact. Variant-title note parsing is still deferred.
- F15: the only direct lxml Element truth test now uses root is None in the
  simple fallback's presence guard. XPath list length tests remain unchanged.
  A childless response test runs with FutureWarning promoted to an error.
  Advanced result-table column parsing and its expected failure are unchanged;
  no invented registered-user result format or access bypass was used.

## Before/after evidence and coverage

New reproduction logs in system TEMP:
isfdb4-phase9b-before.txt (core failures),
isfdb4-phase9b-parser-before.txt (Notes/ASIN/tags), and
isfdb4-phase9b-after.txt (final full suite).
New regressions were run before their corresponding fixes, including the
later ISBN-cache and late-image-result defects. Failures caused by test-double
API assumptions were investigated rather than patched in production blindly:
browser properties return clones, worker is_alive must return bool, and raw
cover bytes are not validated by Source. No skip or expected failure was added.

reliability.py adds 26 tests. Two existing characterization tests were updated
to assert preservation instead of intentional writes: exact_search's preference
file stays unchanged, and restricted fallback respects result/cover limits.
These changes strengthen the approved new requirement. All Phase 9A tests pass.

Final results under Calibre 9.17.0 / embedded Python 3.14.8, Windows 10 Pro:

| Suite | Executed | Passed | Failures/errors | Skipped | Expected failure |
|---|---:|---:|---:|---:|---:|
| Ordinary isolated regression | 145 | 144 | 0 | 0 | 1 |
| Separate Camoufox fixture feasibility | 24 | 24 | 0 | 0 | 0 |

The sole expected failure remains the unverified advanced-search column layout.
No native browser or metadata worker process was launched. Existing launchers
set disposable configuration/cache/temp BEFORE Calibre starts, build a ZIP from
the exact checkout and verify module origins/hashes. No live profile is loaded.
Tests use mocks, controlled Events and Calibre-bundled Pillow; no installation.

## Phase 8 finding status (all 23)

| ID | Status after 9B |
|---|---|
| F01 | Corrected in 9A: safe custom templates. |
| F02 | Corrected in 9A: conservative container credit merge. |
| F03 | Corrected in 9A: explicit decimal indices. |
| F04 | Corrected in 9A: coherent series/index pair. |
| F05 | Withdrawn in 9A: source 0..5 rating conversion is intentional. |
| F06 | Corrected: canonical cross-strategy deduplication. |
| F07 | Corrected at cooperative boundaries; active blocking I/O limitation documented. |
| F08 | Corrected in 9A: optional Type/tags preservation. |
| F09 | Explicit issue capture/preference defects corrected; seasonal/date grammar and broader Notes cases deferred. |
| F10 | Multi-country ASIN fallback/path defects corrected; other external-ID cases deferred. |
| F11 | Corrected: request-local state, defaults included, no persistent search mutation. |
| F12 | Deferred intentional TLS policy; no change authorized. |
| F13 | Deferred URL/resource/deadline/concurrency policy risk; no exploit claimed. |
| F14 | Current Tags corrected; variant-title notes remain for focused evidence/tests. |
| F15 | Corrected presence guard with regression; no advanced table changes. |
| F16 | Deferred dormant undefined header helper; no live caller, unrelated cleanup. |
| F17 | Coverage expanded substantially; real response/image-consumer/platform coverage still incomplete. |
| F18 | Deferred packaging/build-install separation; release work not authorized. |
| F19 | Target runtime passes; minimum-version/other-platform claims still unverified. |
| F20 | Development/test docs updated; release metadata/help/lineage presentation remain release work. |
| F21 | Unverified advanced table; unchanged expected failure. |
| F22 | Intentional Latin-1 query limitation; unchanged. |
| F23 | Unlinked homonym/credit-role ambiguity still needs evidence/policy, not name-based guessing. |

Remaining parser items are explicitly scoped out rather than declared fixed:
broader Notes/date inference, single-link or malformed external-ID variants,
variant-title notes and unlinked credits require focused independent cases.
Do not replace them with broad rewrites or invent advanced-search HTML.

## Safeguards, provenance and readiness

Transport remains urllib for record HTML and inherited Calibre transport for
images/auxiliary pages. fetch_isfdb_url, headers, unverified TLS policy, minimum
90-second record timeout, retry count and Phase 6A error diagnostics are not
changed. Browser cloning is preserved. Unicode query encoding, author identity
and Phase 9A metadata precedence are preserved. Cancellation checks wrap the
transport; they do not replace it. Camoufox remains NO-GO.

F12's unauthenticated TLS and F13's unrestricted redirects/large bodies/thread
counts remain security/reliability risks, not newly demonstrated exploits.
Require separate authorization and controlled local trust/redirect/resource
tests before changing those policies. Native cancellation/deadline guarantees
would require transport/lifecycle design beyond cooperative checks.

Changes are local ISFDB4 repairs to inherited GPLv3 code; none are copied
ISFDB3 1.5.0 or Calibre implementations. Calibre supplies the APIs exercised by
tests. Retain existing credits/license notices and the provenance ledger.

Readiness: GO for a clearly labelled development checkpoint and controlled
isolated diagnostic installation; NO-GO for replacing the live plugin or public
release until remaining security, parser, packaging, consumer and compatibility
gates are resolved or explicitly scoped/approved. No commit/install performed.
Phase 9C is not started.

Repository inventory: tracked modifications remain README.md, __init__.py and
objects.py. Earlier docs/tests remain untracked; this phase adds PHASE9B.md and
tests/reliability.py and updates development/provenance/test documentation and
the runner. Git diff statistics are cumulative against HEAD and exclude all
untracked files. No existing file was discarded. git diff --check passes.

Final cumulative tracked diff:

```
 README.md   |  29 +++++
 __init__.py | 407 ++++++++++++++++++++++++++++++++++++++++--------------------
 objects.py  | 365 ++++++++++++++++++++++++++++++++++++++---------------
 3 files changed, 569 insertions(+), 232 deletions(-)
```

Untracked inventory (23 files; includes preserved earlier phases):

```
docs/CAMOUFOX_FEASIBILITY.md
docs/PHASE8_AUDIT.md
docs/PHASE9A.md
docs/PHASE9B.md
docs/UPSTREAM_PROVENANCE.md
tests/README.md
tests/author_edges.py
tests/camoufox_feasibility.py
tests/fixtures/author_bibliography.html
tests/fixtures/author_search.html
tests/fixtures/publication.html
tests/fixtures/restricted_search.html
tests/fixtures/search.html
tests/fixtures/simple_search.html
tests/fixtures/title.html
tests/http_diagnostics.py
tests/metadata_correctness.py
tests/phase4_cases.py
tests/reliability.py
tests/run.ps1
tests/run_calibre.py
tests/run_camoufox_feasibility.ps1
tests/unicode_correctness.py
```
