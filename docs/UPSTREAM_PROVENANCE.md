# ISFDB4 upstream provenance and Phase 5 compatibility review

Review date: 2026-11-03.
Target: Windows 10 Pro, Calibre 9.17.0, embedded Python 3.14.8.
Historical Phase 5 status: provenance and planning only; no upstream changes
were incorporated during that review. **Phase 6A was subsequently authorized
and implemented on 2026-11-04. Phase 6B isolated feasibility research was
subsequently authorized and completed; see the final sections. Production
Camoufox integration remains unauthorized.**

## Scope and reproducibility

The reviewed ISFDB4 checkout has HEAD
`759c404b7ac93b499ff0c1b2ecc4ab657c6b6b20` plus the existing uncommitted
Phase 2/4 production corrections and Phase 1-4 test harness. HEAD alone does
not identify the reviewed source. Its production input SHA-256 values are:

- `__init__.py`: `0951cefb189f12eb3c2b0e58a3ff571a97c58670d5880366ca679920625d6c2d`.
- `objects.py`: `a95eab9eca0a8095188be8e73327085ae27d042bf3a289723c0030c1f7a782d5`.
- `myglobals.py`: `a14c7cd7f33c1e1ad37a5de17db91d5dfce5243e01eab705efc8c20401d5ab51`.

All ISFDB3 and Calibre source links below identify immutable revisions.
Line references describe those revisions or this reviewed local snapshot.

The upstream comparison is
[1.4.12 release commit through 1.5.0](https://github.com/bertholdm/isfdb3-calibre/compare/3a2965f406217507fff193744f3047a5d2d7f806...b8ff4a0fd4175b64843334bb787b62f8151e1146).
It contains two commits and changes exactly README.md (+3/-1), __init__.py
(+11/-5), and objects.py (+44/-5). No translations, build scripts, dependency
manifests or tests changed. The repository has no version tags or GitHub
releases establishing separate release artifacts; these are source revisions.

## Authorship and provenance ledger

Git author/committer records establish recorded contributors, not exclusive
copyright ownership or proof that every added line was independently written.
No Co-authored-by trailers appear in the specific introducing commits below.
Absence of a trailer does not prove absence of other contributors.

| Contribution | Recorded author and commit | Attribution treatment |
| --- | --- | --- |
| ISFDB3 1.5.0: version/minimum-version declarations, browser flag, HTTP diagnostics, exceptions, response stripping and release documentation | Git author/committer `bertholdm`; plugin metadata credits Michael Detambel. [`b8ff4a0fd4175b64843334bb787b62f8151e1146`](https://github.com/bertholdm/isfdb3-calibre/commit/b8ff4a0fd4175b64843334bb787b62f8151e1146), 2026-10-30. | Credit Michael Detambel / bertholdm for the ISFDB3 adaptation. Some definitions match earlier Calibre code; do not assign sole original authorship of the whole block to ISFDB3. |
| ISFDB3 final February regex escaping/spacing correction and shorter debug message in Publication.from_url | `bertholdm`, [`fa5ecfbe9a17880484d3045183bb2723cfa20548`](https://github.com/bertholdm/isfdb3-calibre/commit/fa5ecfbe9a17880484d3045183bb2723cfa20548), 2026-02-09. | Equivalent corrected behavior is already in ISFDB4; distinguish upstream authorship from local import/formatting. |
| Initial 1.4.12 release and preceding regex changes | `bertholdm`, [`3a2965f406217507fff193744f3047a5d2d7f806`](https://github.com/bertholdm/isfdb3-calibre/commit/3a2965f406217507fff193744f3047a5d2d7f806), 2026-02-09. | This precedes the same-day correction above. |
| Earlier tooltip/title parsing revision inherited by this codebase | `bertholdm`, [`03752c4f50a4c078fd6e4eb3a0146ab120d75284`](https://github.com/bertholdm/isfdb3-calibre/commit/03752c4f50a4c078fd6e4eb3a0146ab120d75284), 2026-01-15. | The upstream changelog thanks RealLactar. That acknowledgment is not a Git coauthor trailer. |
| UrlNotFound and UrlTimedOut definitions and messages | Kovid Goyal, [Calibre `e004b057ed8b5491770c35dd1ad7c39cdd2191e0`](https://github.com/kovidgoyal/calibre/commit/e004b057ed8b5491770c35dd1ad7c39cdd2191e0), 2022-08-04. | Verified introduction in Calibre's amazon.py. Definitions match those later added to ISFDB3. Preserve Calibre provenance if copied/adapted. |
| Initial Calibre API for driving Camoufox | Kovid Goyal, [`32a29185a669ec2a4f4e1a00ba58d24fa8859f10`](https://github.com/kovidgoyal/calibre/commit/32a29185a669ec2a4f4e1a00ba58d24fa8859f10), 2026-09-06. | This is Calibre functionality, not an ISFDB3 or ISFDB4 browser engine. |
| Calibre shared metadata browser worker, Source participation flag and Amazon integration | Kovid Goyal, [`21014ee93c6014e37461b7c77923665bd4156924`](https://github.com/kovidgoyal/calibre/commit/21014ee93c6014e37461b7c77923665bd4156924), 2026-10-15. | Use its supported interfaces where suitable; do not copy the internal worker merely to claim integration. |
| Calibre Google Images integration | Kovid Goyal, [`9944924f78de467546037d546f731c737f44f28c`](https://github.com/kovidgoyal/calibre/commit/9944924f78de467546037d546f731c737f44f28c), 2026-10-15. | A reference implementation, not an ISFDB implementation. |

Calibre's later file history also includes edits by `un-pogaz`, including
`106e78ed1567aa6f70d616e186c2566741e5d78e` and
`b55eaf43a0d00e80b1ddd6cfbfa6d69a84e9ac95`. These are separate contribution
commits, not coauthor trailers on the original Kovid Goyal commits. Preserve
complete notices and history when adapting a later file, rather than treating
its initial author as its only contributor.

### ISFDB2 lineage and other projects

ISFDB3 derives from Adrianna Pińska's
[ISFDB2](https://github.com/confluence/isfdb2-calibre). Its
[Contributors.md](https://github.com/confluence/isfdb2-calibre/blob/master/Contributors.md)
credits Grant Drake (Barnes & Noble plugin), Xtina Schelin (original ISFDB
plugin), Adrianna Pińska (ISFDB v2), and Brian Schweitzer (v2 title lookup).
Retain these lineage acknowledgments for inherited work. They do not establish
that every present file contains code from each person.

Calibre API use, Calibre implementation copying, and external Camoufox browser
distribution are separate provenance questions. API calls do not make
Calibre's implementation original ISFDB4 work. Bundling a browser or other
third-party components would require reviewing their own notices/licenses;
this review does not authorize or perform such bundling.

### ISFDB4-specific work

The author provenance/ambiguity annotations, stable author-ID input, candidate
scan policy, coauthor repair/merge behavior, strict query rejection and offline
regression harness are local ISFDB4 modifications to an inherited GPL codebase.
They are not ports of ISFDB3 1.5.0. This description credits the local changes
without claiming original authorship of the inherited plugin or Calibre APIs.
Uncommitted changes do not yet have provenance commit IDs.

The pre-existing urllib fetch change has local history at
`85cd8a5`, recorded under RealLactar, before ISFDB3 1.5.0. Local commit
`7324124175d6d3c36151f1bf2fe587a128a6a3c3` is recorded under RealLactar with an
ISFDB3-update message. Later blame points at the formatting commit
`1616d1696f3250e755c38b851c583b8a1d34811e`. Neither alone proves the exact
upstream SHA used for the February regex import.

## Licensing and distribution requirements

ISFDB4's existing LICENSE and the reviewed ISFDB3/ISFDB2 licenses contain the
GNU GPL version 3 text. Relevant Calibre files have explicit GPLv3/Kovid Goyal
notices: Source base and Amazon code identify 2011; Camoufox and metadata
worker code identify 2026. Preserve the notices as supplied; do not replace
their dates with the date of an ISFDB4 adaptation.

The existing GPL text, sections 4-6, requires preserving applicable copyright,
license and warranty notices; providing the license with distributions;
prominent modified-work notices and relevant dates; GPL licensing of the
covered derivative; and applicable Corresponding Source when conveying
non-source forms. See [LICENSE](../LICENSE), especially sections 4, 5, 6,
10 and 14. Acknowledgments do not replace these obligations. Private local
modification does not by itself require public publication of the repository.

The Free Software Foundation notice in LICENSE concerns the license document,
not ownership of the plugin. The appendix's example "or later" language is
not, by itself, proof of an express project-wide GPL-3.0-or-later grant.
Preserve existing terms and verify any more specific SPDX designation before
publishing one.

For every future copied or adapted block, record repository, file/method,
immutable commit, credited contributor(s), applicable notices/license,
modification date and what ISFDB4 changed. For the proposed exception-derived
diagnostics, record both ISFDB3 b8ff4a0 and Calibre e004b057. Prefer existing
exception/APIs over copying implementation where that avoids unnecessary code.

## Exact implementation comparison

| Area | ISFDB3 1.5.0 | Current ISFDB4 | Assessment |
| --- | --- | --- | --- |
| Browser activation | __init__.py:156 sets `users_camoufox_worker`. | Inherits Source.browser; no Camoufox integration. | Calibre expects `uses_camoufox_worker`. Neither spelling replaces the inherited transport. Do not port the misspelled attribute. |
| ISFDB fetching | objects.py:133-167 calls browser.open_novisit. | objects.py:195-223 calls urllib with ISFDB_HTTP_HEADERS. | Upstream does not demonstrate a working browser replacement. |
| Browser initialization/headers | No new initialization override; inherited browser chooses a user agent. | Fixed Chrome-style headers for urllib; Source browser has separate settings. Dormant apply_isfdb_headers at __init__.py:51 references undefined ISFDB_REQUEST_HEADERS. | Do not wire that helper into a new path unchanged. A transport change must explicitly define ownership of headers/cookies. |
| HTTP 403 | New error message attributes denial to bot detection and suggests trying later. | Underlying HTTPError propagates; workers log failures. | Clearer neutral diagnostics are useful; bot causation and a successful retry are not established. There is no automatic upstream retry. |
| Other exceptions | Adds UrlNotFound/UrlTimedOut/DownloadDenied. Non-403/404 branch reads attr before assignment; socket is not imported. DownloadDenied is unused. | Preserves standard HTTP/network exceptions. | Do not copy the broken handler. Preserve useful original exception types. |
| Read/empty errors | The try covers open_novisit, not response.read; whitespace is stripped before parsing but empty data still fails. | Empty/whitespace bodies log and return an empty HTML root. | Retain Phase 4 behavior. Cover read-time errors if adding diagnostics. |
| Timeout | Forwards caller timeout without a 90-second floor. | max(timeout, 90) for ISFDB urllib calls. | A direct replacement would change behavior; preserve the floor and distinguish startup/queue deadlines. |
| TLS | ignore_ssl_errors=True affects inherited mechanize browser. | Same Source setting plus explicit unverified urllib context. | Camoufox defaults to verification; Source's flag is not automatically transferred. No TLS change is authorized. |
| Cloning/threading | Worker.__init__:891 clones a mechanize browser. | Worker.__init__:1264 also clones; ISFDB fetching bypasses it. | Camoufox is asynchronous and has no mechanize clone_browser/open_novisit contract. Not a drop-in object. |
| Response encoding | Reads bytes and decodes Latin-1. | Same base encoding plus strict query handling and coauthor corrections. | Camoufox returns Unicode DOM HTML; blindly applying this decode pipeline would corrupt it. |
| February regex | Publication.from_url includes corrected escaping/spacing and shorter debug message. | Equivalent code at objects.py:1554-1555 and 1622. | Already present; no re-port. |
| Configuration metadata | Raises declared minimum Calibre to 9.17.0. | Still declares minimum 5.0.0, while this review targets 9.17.0. | Raise it only if required by the selected implementation; this review does not certify older versions. |
| Series fetch | Unchanged override at objects.py:2074 returns an element, but from_url:2109 expects a location/root pair. | Uses shared location/root contract. | Do not restore the upstream override. |
| Other metadata behavior | Does not contain our Phase 2/4 author, query, coauthor, empty-response and collision corrections. | Those corrections and tests are present. | Do not replace whole files. |

New executable upstream methods in the comparison are the two exception
constructors; changed methods are ISFDBObject.root_from_url and the same-day
February Publication.from_url correction. DownloadDenied is a new empty class.
No existing executable method body in __init__.py changed: its executable
changes are class attributes. The worker comment spelling correction is not
new behavior.

## Calibre 9.17 compatibility findings

The [Source participation flag](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/ebooks/metadata/sources/base.py#L238)
controls worker prelaunch and extended waiting. Its
[browser property](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/ebooks/metadata/sources/base.py#L299)
still creates a clonable mechanize browser. The shared metadata worker
[registers only Amazon and Google Images handlers](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/metadata.py#L744).
Merely correcting the flag does not create an ISFDB handler or route requests.

Actual Calibre integrations call
[run_in_browser](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/metadata.py#L978).
Requests for a source are serialized and the deadline includes time waiting
for earlier requests. The [Camoufox browser API](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/camoufox.py#L3513)
is asynchronous; its clone/open interface, lifetime, cookies, Unicode HTML and
error model differ from mechanize/urllib. No safe replacement or supplement
has been verified. The previous optional embedded-runtime probe was blocked
by execution policy; no successful browser launch or network comparison is
claimed. The existing Phase 4 suite did run in Calibre's embedded runtime.

A real integration may need a downloaded Camoufox executable, browserforge
data and other resources, worker processes and a profile. Do not assume an
additional pip Camoufox/Playwright install is required: Calibre has its own
implementation. Do not assume existing resources are provisioned, either.
On Windows, [bin_install_dir](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/constants.py#L535)
normally uses %LOCALAPPDATA%/calibre-dbin, independent of redirected config and
cache paths. A test must explicitly control dependency provisioning, not
simply enable network access in the existing harness.

## Ranked recommendations and implementation plans

### Priority 1: neutral HTTP diagnostics using existing exceptions

- Purpose/benefit: identify the failing URL and HTTP status or transport error
  without masking the cause or asserting that every 403 is Cloudflare.
- Upstream source: ISFDBObject.root_from_url, objects.py:133-167; ISFDB3
  b8ff4a0, credited to bertholdm/Michael Detambel; earlier exception definitions
  and timeout diagnostic pattern from Calibre e004b057/Kovid Goyal.
- Dependencies: existing urllib.error exceptions and Calibre logging methods.
  No new browser API, package or copied Calibre exception classes are needed.
- Required modification if approved: narrowly log failures around open AND
  read in ISFDB4 fetch_isfdb_url, then re-raise the original exception.
  Keep 403/404/500 types, headers, TLS context, max(timeout, 90), response
  encoding, empty-response behavior and worker result handling unchanged.
- Conflicts: upstream's generic 403 exception would break callers/tests
  expecting HTTPError; its handler masks non-403/404 errors. Do not adopt it.
- Tests: open-time/read-time HTTPError 403/404/500, URLError, direct/wrapped
  timeout, exception without getcode, empty body, and original-exception
  identity; all existing metadata tests remain enabled.
- Risks: duplicated logging at transport and worker layers; keep logs concise.
  No retries, header rotation or changed timing should be introduced.

### Priority 2: offline Camoufox contract/feasibility prototype

- Purpose/benefit: establish whether a separately reviewed ISFDB-specific
  adapter can preserve our parser and concurrency contracts.
- Source/credit: Calibre Source.browser and uses_camoufox_worker, metadata
  run_in_browser/handlers, and Camoufox Browser/Page interfaces. Credit Kovid
  Goyal and Calibre contributors; use commits 32a29185 and 21014ee9. Record
  ISFDB3 b8ff4a0 as the reviewed upstream motivation, not a working engine
  implementation or source of Calibre's API.
- Dependencies: Calibre 9.17 APIs. The shared worker does not offer a generic
  ISFDB fetch action. A supported extension path or separate adapter/worker
  must be established before selecting an implementation. Do not copy or
  monkey-patch the global internal handler registry as a shortcut.
- Required work if approved: test-only adapter contracts with fake workers,
  explicit final-URL/Unicode-HTML/error results, bounded concurrency,
  cancellation and deterministic cleanup. No production activation initially.
- Conflicts: clone_browser assumptions, cookie/headers separation, Latin-1
  decoding, minimum socket timeout versus request deadline, TLS defaults and
  dependency-install locations. None may change silently.
- Tests: prove actual routing rather than flag-only activation; fake startup
  failure, unavailable API, unknown source, queue deadline, cancellation,
  Unicode DOM, redirect, missing resources and worker termination.
- Risks: private API stability, binary downloads and Windows process/profile
  cleanup. Raising the minimum version is necessary only when a chosen
  production implementation actually depends on those APIs.
- Gate: do not replace/supplement the urllib path until the design is approved
  and controlled integration establishes a benefit. A flag-only port fails
  this gate.

### Priority 3: release-facing attribution and compatibility notices

- Purpose/benefit: keep inherited contributions and local adaptations visible.
- Source/credit: the provenance ledger above, existing GPL notices and ISFDB2
  Contributors.md.
- Required changes in a later authorized phase: acknowledge lineage in README;
  add a dated changelog entry only for changes actually implemented; attach
  source/method/commit/license records to any adapted block. Do not claim a
  Camoufox migration before one exists.
- Dependencies: none beyond preserving existing license text and notices.
- Tests/checks: ensure the release includes LICENSE and applicable source and
  notices; inspect the documented minimum version against used APIs.
- Risks: overstating original authorship or describing a reviewed proposal as
  shipped functionality. These are documentation proposals only in Phase 5.

## Changes not to incorporate

Do not copy the misspelled users_camoufox_worker flag, broken attr/socket
handler, generic 403 rethrow, speculative bot-causation explanation, unused
DownloadDenied stub, or retry advice as a recovery guarantee. Do not import
whole upstream files or restore the Series return-contract defect. Do not
discard ISFDB4's Phase 4 fixes. Do not strip an empty body and assume it is
parseable. Do not change TLS, the timeout floor, query encoding, preferences,
result ordering or advanced-search columns as incidental migration work.

## Proposed acknowledgments (not yet applied)

README wording:

> ISFDB4 derives from Michael Detambel's ISFDB3, which derives from Adrianna
> Pińska's ISFDB2. ISFDB2 also acknowledges Grant Drake, Xtina Schelin and Brian
> Schweitzer. Calibre supplies the metadata-source and browser APIs, including
> Camoufox integration developed in the Calibre project by Kovid Goyal and
> contributors. Existing copyright and GPLv3 notices remain applicable.

Identify the inherited first-person history in README as upstream history,
rather than implying it describes the ISFDB4 maintainer.

Prospective changelog wording, ONLY after the diagnostics are implemented:

> Adapted HTTP-error diagnostic ideas from ISFDB3 commit b8ff4a0 by bertholdm
> (Michael Detambel), with ISFDB4-specific corrections. Relevant exception
> definitions/diagnostic patterns predate that adaptation in Calibre commit
> e004b057 by Kovid Goyal. Existing transport, TLS and timeout behavior retained.

A future browser adapter must credit Calibre's actual APIs and separately
describe ISFDB4-specific glue, rather than calling the engine original ISFDB4
work.

## Unresolved questions and evidence gates

- The exact copying route of the matching Calibre exception definitions into
  ISFDB3 is not stated in b8ff4a0. Preserve the earlier Calibre credit and flag
  direct-route authorship as unverified.
- DownloadDenied is a generic stub also found elsewhere; its original source
  cannot be established confidently from name/shape alone.
- The March 1.4.13 changelog date does not establish a separate Git commit.
- The exact upstream SHA used for the local February regex import is not
  recorded in the examined local commit messages.
- No exclusive copyright-ownership assertion follows from a Git author name.
  No project-wide GPL-3.0-or-later grant is established by boilerplate alone.
- Canonical/alternate-author equivalence without stable-ID/redirect evidence
  remains unresolved; retain explicit ambiguity instead of guessing.
- Full non-Latin-1 name-query support still needs a verified encoding contract.
- Advanced Title search needs permitted captured table headers/data or
  authoritative rendering source before its expected failure can be fixed.
  Do not reconstruct a table from the unverified synthetic fixture.
- A successful Camoufox/ISFDB integration, resource readiness and legal site
  access have not been verified. Do not bypass registration or challenges.

## Proposed Phase 6 instructions

1. Require separate user authorization. Start from this unchanged production
   snapshot and preserve all Phase 4 corrections/tests.
2. Implement only Priority 1 diagnostics first, with provenance and focused
   offline tests; prefer standard exceptions over copied exception classes.
3. Run the complete suite in Calibre 9.17.0 / Python 3.14.8 using disposable
   settings/cache/temp paths and the explicit checkout ZIP. Keep ordinary tests
   offline and preserve the advanced-search expected failure.
4. If separately included in authorization, build the Priority 2 test-only
   feasibility prototype. Report unsupported API/handler gaps before any
   production browser switch or broad architectural change.
5. Controlled integration is a further gate: explicitly provision test-owned
   dependencies, isolate the binary install location and worker environment,
   use local HTTP/TLS fixtures first, then only permitted low-volume ISFDB
   checks. No unapproved downloads, live-plugin installation, challenge bypass,
   user-settings/library writes, TLS changes or timeout changes.
6. Review actual implemented provenance notices and README/changelog wording,
   report regressions, configuration effects and Git diffs, then stop. Do not
   commit, push or begin another phase without instructions.

## Phase 5 verification

Only this document is authorized to be created. Read-only checks include the
pinned upstream comparison, current code/line inspection, Python AST parsing,
protected parser/network-setting comparison against HEAD, Git diff --check,
and a before/after hash inventory of existing repository files. The last
executed Phase 4 baseline is 77 tests: 76 passed, none failed/errored/skipped,
one advanced-search expected failure. The suite is not rerun for this
documentation-only phase, and no new runtime/integration result is claimed.

## Phase 6A implemented adaptation: HTTP diagnostics (2026-11-04)

Scope: the Priority 1 diagnostic plan only. ISFDB4's objects.py
fetch_isfdb_url now logs failures while opening the response, reading its final
URL or reading its body, then uses a bare raise to preserve the original
exception and traceback. Logs include HTTP status when available, operation,
requested/known-final URL, effective timeout, exception representation and
transport reason/explicit cause/exception-valued argument where present.
Diagnostic errors cannot replace the original transport exception.

This adapts diagnostic intent from ISFDB3 ISFDBObject.root_from_url in
b8ff4a0fd4175b64843334bb787b62f8151e1146, recorded under bertholdm and credited
in the plugin to Michael Detambel. The earlier exception/timeout diagnostic
patterns originate in Calibre's Amazon source, Kovid Goyal's commit
e004b057ed8b5491770c35dd1ad7c39cdd2191e0. Both origins are recorded adjacent to
the adaptation in source. No UrlNotFound, UrlTimedOut or DownloadDenied class
was copied. This is an ISFDB4 adaptation to its existing urllib fetch path,
not a claim of original authorship of upstream diagnostic ideas or Calibre
functionality. Existing copyright/GPLv3 notices are retained.

The root README has an unreleased, dated development changelog acknowledgment.
The provenance ledger and all earlier uncertainty findings remain applicable.
No browser/Camoufox activation, new dependencies, TLS changes, timeout changes,
retry changes, parser changes or preference changes are part of Phase 6A.
Empty-body logging now formats the actual URLs; its Phase 4 empty-root return
policy remains unchanged. Caught network errors are never converted to empty
results by the fetch helper.

Verification uses the isolated checkout ZIP and Calibre 9.17.0 / embedded
Python 3.14.8. Eleven added offline tests cover HTTP statuses, connection
errors, direct/wrapped timeouts, read failures, absent HTTP methods, empty
bodies, original exception identity/traceback/cause, logging failure and
successful fetch/decode/header/TLS/timeout behavior. Complete result:
88 tests, 87 passed, no failures/errors/skips, one unchanged advanced-search
expected failure. No live requests, plugin installation, user-settings or
library changes were performed. Phase 6A stops here; Phase 6B is not started.

## Phase 6B isolated research (2026-11-04)

Separate user authorization permitted installed-API inspection and an offline
prototype only. See [CAMOUFOX_FEASIBILITY.md](CAMOUFOX_FEASIBILITY.md) for the
evidence matrix, risks and NO-GO production recommendation. The earlier Phase
6A stop statement above records that phase's boundary, not current authorization.

The test-only fixture adapter uses Calibre's installed State, SourceHandler,
TabPool, Deadline, SessionWorker and run_in_browser implementations with fake
browser/process I/O. It does not copy Calibre implementations or defective
ISFDB3 integration code. Credit for Calibre APIs remains Kovid Goyal and
contributors, as documented in the ledger; the new fixture driver is ISFDB4
test scaffolding, not a browser engine or production integration.

Installed Calibre 9.17.0 / embedded Python 3.14.8 executed 24 feasibility tests
successfully. The ordinary suite also passed 87 tests with one expected failure.
No real browser/child worker was launched. An existing browser executable was
located read-only, but native resource, networking and cleanup behavior remain
unverified. Production files were unchanged; no external network, downloads,
installations, live settings/plugins/libraries, TLS/timeout/retry changes,
commits or pushes occurred. Production integration remains unauthorized.

## Phase 7 local correctness changes (2026-11-04)

Phase 7 adds parameter/codepoint diagnostics to the existing atomic Latin-1
query rejection, gives exact normalized author spellings priority over loose
punctuation variants, and preserves ordered author IDs when merging title and
publication credits. These are local ISFDB4 modifications to the existing
fork, not copied or adapted ISFDB3 1.5.0 implementations. No additional
external implementation was introduced. Python's standard unicodedata and
urllib APIs remain in use. Existing upstream attribution, copyright notices
and GPLv3 obligations above remain applicable. UTF-8 CGI query support remains
unverified; no claim of new server-side Unicode support is made.

## Phase 9A local remediation (2026-11-05)

The Phase 8 audit has been copied byte-for-byte to PHASE8_AUDIT.md; its original
temporary report is preserved. PHASE9A.md records corrections and an explicit
erratum withdrawing F05 after inspecting/exercising Calibre's actual source
rating consumer. The preserved audit is historical evidence, not silently
rewritten to match later findings.

Container credit/series gating corrects regressions in our recent local merge
work; optional-field/template and explicit-number handling correct inherited
limitations. These are local ISFDB4 changes to the inherited GPLv3 fork. No
ISFDB3 1.5.0 implementation, Calibre internal implementation or new dependency
was copied. Tests call the installed Calibre ISBNMerge API to verify its source
rating contract; that consumer remains Calibre work credited to its original
contributors. Existing authorship acknowledgments and license notices remain.

## Phase 9B local reliability changes (2026-11-05)

RecordMatches canonical deduplication, request-local settings, cooperative
cancellation boundaries/result guards, cache repairs and the focused Notes,
ASIN and tag corrections are local ISFDB4 modifications to the inherited GPLv3
fork. They are not ports of ISFDB3 1.5.0 and do not integrate Camoufox.
Calibre still supplies Source, browser cloning, raw cover-byte downloading,
metadata/cache APIs and its own consumers. Tests call those installed APIs;
their implementations were not copied. Bundled Pillow is used only to create
an in-memory test image. No new external code or dependency was incorporated.
Existing notices and the historical Phase 8 audit remain intact. PHASE9B.md
records inherited defects, intentional changes and deferred security policy.

