# Phase 9A metadata correctness — 2026-11-05

Target: Calibre 9.17.0 / embedded Python 3.14.8, Windows 10 Pro.
No version change, live plugin installation, external requests, preference or
library changes, commit or push. Phase 9B/9C have not begun.

## Evidence and scope

PHASE8_AUDIT.md is an exact copy of the original temporary audit (SHA-256
26cf8f3ba56d9297ee7f7887de292732775783d2b0dab1d27ac0545f0892a7ac).
All 23 findings were reviewed. The seven initial failures map to four methods:
container credits (one), decimal indices (two), optional Type/templates (three),
and title-only series merging (one). No original reproduction was removed,
skipped, weakened, or changed to expected failure. Additional pre-fix coverage
exposed missing publication decimal handling, optional combinations and custom
template errors. Before/after logs are disposable files in the system TEMP
directory, isfdb4-phase9-before.txt and isfdb4-phase9-after.txt.

## Corrections and precedence

- Worker.run: publication membership alone does not establish that a title is
  the same work as its container. Only equal whitespace/case-normalized titles
  with equal types (where both are available) supply missing title authors or
  title series. If this evidence is absent, retain publication credits and
  publication series only. This is intentionally conservative: alternate edition
  titles/types may now retain fewer inferred credits rather than add a contained
  story's author. Stable author IDs, publication order, aliases and homonymous
  coauthors retain the existing ordered-credit merge for matching works.
- Worker.run: a nonempty publication series takes precedence as a whole pair,
  including a missing index. Otherwise matching-work title series/index are
  used together. An index with no source series is discarded; indices never
  cross between conflicting names. Nested series strings are retained as-is.
  A missing index stays None rather than being borrowed from another source.
- objects.parse_series_index and both record parsers: explicit ASCII signed
  integer/decimal numbers are parsed numerically, with finite-value validation.
  1.5 and 2.25 remain those values rather than 15 and 225. Unsupported forms such
  as 1.2.3/nonsense leave no numeric value and use existing diagnostics/notes.
  Missing explicit indices are absent/None, not fabricated zero. Existing Roman,
  slash-combined issue and Notes volume/issue policies remain separate, including
  the documented first-issue reduction for 61/62. Roman/slash grammar validation
  has not been comprehensively redesigned; inherited periodical Notes defects
  remain outside this phase. An authoritative numeric zero is not overwritten
  by the publication date fallback.
- Worker.run: absent optional tags become an empty list with a diagnostic;
  otherwise valid title/author/identifier metadata is retained. Existing Unknown
  author policy remains when all author credits are absent. Title.from_url now
  tolerates absent tail text in optional field labels instead of raising before
  section handling. Missing required title still prevents a fabricated result.
- ISFDB4.clean_downloaded_metadata: render only supported named placeholders,
  support normal numeric format specifications, and substitute empty strings for
  absent optional values. series_code/main_series use available metadata or an
  empty value, not a fabricated code/parent. Invalid, unknown or empty-result
  templates retain the original cleaned title and log from the normal worker
  path. Missing authors/series do not render literal None or discard the record.
  Existing case cleanup and default title behavior are retained. Templates are
  not executable expressions; unsupported syntax safely falls back.

F02 is a recent local merge regression; F04 was inherited but was coupled to
that merge. F01/F03/F08 are inherited optional-field/template/numeric defects.
Corrections extend no external implementation; GPLv3 and existing attribution
remain applicable. Advanced search, URL encoding, transport and worker lifecycle
are not changed by these fixes.

## Rating correction to the audit, not to production

F05 incorrectly inferred the plugin contract from Calibre's library storage
scale. Installed calibre.ebooks.metadata.sources.identify.ISBNMerge.merge accepts
source ratings only when 0 < rating <= 5, and rounds their mean. Execution with
the plugin's 4.5 source result returns merged rating 4. ISFDB's 9.00 -> 4.5
conversion is therefore intentional and remains unchanged. Changing it to 9
would violate the source consumer's contract. The regression test exercises the
actual installed merger, with Calibre's normal plugin/relevance annotations.
The original audit remains intact; this document explicitly withdraws F05.

## Verification and limitations

Complete ordinary suite: 119 executed, 118 passed, 0 unexpected failures,
0 errors, 0 skipped, 1 expected failure (unverified advanced-search table).
All previous passing tests remain passing. Separate fixture-only Camoufox suite:
24 passed, no errors/failures/skips; no native browser/worker launch. Both use
the existing PowerShell launchers, setting disposable paths before process
startup and loading the exact checkout ZIP. New tests cover real parser and
worker paths alongside focused synthetic merge dictionaries.

Phase 8 snapshot comparison confirms fetch_isfdb_url, encode_query,
TitleList.from_author and plugin/worker constructors are unchanged. HTTP
headers/TLS/minimum timeout/retries/diagnostics, browser cloning, worker
threading, preferences and defaults, Unicode policy and Camoufox NO-GO remain.

Remaining audit work includes F06 cross-strategy deduplication, F07 cancellation,
F09 periodical Notes, F10 external identifiers, F11 persisted request settings,
F12/F13 TLS/URL/resource policy, F14 tags/linked-field parsing, F15 FutureWarning,
F16 dormant helper, and release/test/packaging/compatibility/documentation gates
F17–F20. F21 advanced-search evidence, F22 Unicode limits and F23 unlinked-credit
identity limitations remain. No release-readiness approval is implied. Same-work
matching is deliberately conservative, not a complete bibliographic relationship
model; no live HTML verification or new access capability was established.

## Working-tree inventory

Tracked modifications: README.md, __init__.py, objects.py. Untracked files
(including earlier phases, not all newly created in Phase 9A):

```
docs/CAMOUFOX_FEASIBILITY.md
docs/PHASE8_AUDIT.md
docs/PHASE9A.md
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
tests/run.ps1
tests/run_calibre.py
tests/run_camoufox_feasibility.ps1
tests/unicode_correctness.py
```

No pre-existing files were deleted. Git diff statistics are cumulative against
HEAD and exclude all untracked files. git diff --check passes without output;
the new Phase 9A test/documentation files also have no trailing whitespace.
