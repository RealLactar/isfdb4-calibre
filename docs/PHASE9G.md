# Phase 9G corrected candidate live validation — 2026-11-05

## Outcome: GO for ongoing owner-local use

All eight required live cases passed. The corrected candidate remains installed
in the owner's actual Calibre profile. Rollback was not required. The verified
original backup remains available. No existing book record was opened/updated,
no library database was used, and no commit, push or tag was created.

This is a bounded local-adoption result for Windows 10 Pro / Calibre 9.17.0 /
embedded Python 3.14.8, not a public release, universal compatibility claim or
security-policy certification. Production plugin version stays 1.4.14.

## Candidate source and package identity

Repository: C:\Users\apt\Git\Calibre-ISFDB4\isfdb4-calibre; branch main.
Base checkpoint remains 8c37b852c41748f65b9b03a6cca1c28b8f312d26.
Source is that checkpoint plus the reviewed uncommitted Phase 9F correction,
including exact-title relevance before result limiting. No new commit was
authorized. Review found only intended source/test/documentation changes;
generated packages, logs, owner configuration/backups, credentials and libraries
are outside the repository. The pre-existing PHASE9E.md final report is retained.

Artifact/evidence directory:
C:\Users\apt\Documents\ISFDB4-Phase9G-Validation-cc69e9d6-5696-4a83-a24c-91fa093d7f07

Candidate: ISFDB4-corrected.zip

SHA-256:
`87b22e5d54779214f6de21ab301d438e49bad51b4db207d1c682c1a6831f8821`

Production source byte hashes:

| File | SHA-256 |
|---|---|
| __init__.py | 79a8ee618daccac42f3602955cc8ab48ee89856ae73574f99aee6d9e0543f431 |
| objects.py | c1efdf1a4a4f390b9611e40b54b2b209074c0b21e5ea2b52b9570656e72967a5 |
| myglobals.py | a14c7cd7f33c1e1ad37a5de17db91d5dfce5243e01eab705efc8c20401d5ab51 |

candidate-manifest.json records all entry hashes, base commit and tracked patch
SHA-256 9a990569ff324b0040edd0c62fd3e4fa564e07dbebb4c0b478971cf9f8de8df4.
working-tree.patch records that pre-build tracked delta; untracked ranking
fixture/test/report are inventoried separately in the final repository state.
The runtime package uses the exact validated working-tree bytes, not a claim
that the base checkpoint alone contains this correction. No Phase 9E archive
was reused. Building twice gave identical bytes; ZIP CRC and entry/hash checks
passed. All packaged source still matches its recorded input hashes.

Established allowlist/fixed-order/fixed-1980-timestamp/fixed-mode packaging:

```
LICENSE
README.md
__init__.py
docs/UPSTREAM_PROVENANCE.md
myglobals.py
objects.py
plugin-import-name-isfdb4.txt
translations/de.mo
translations/de.po
```

No tests, fixtures, temporary scripts, logs, .git/.idea, configuration, backup,
credential or library files are in the ZIP. GPL notices, original acknowledgments
and provenance are preserved. README's Phase 9F correction was packaged; this
new validation report is repository documentation, not a runtime dependency.

## Rollback gate and supported installation

Verified before installation:

- C:\Users\apt\Documents\ISFDB4-Phase9E-Backup-20261105-084400\ISFDB4-original.zip
  exists, is a valid ISFDB4 archive with its marker, and matches SHA-256
  9be3ce2cce7d3cd666b040757883e1791b55cb78e64ed9fda2836cceab38a760.
- Active installed ISFDB4.zip matched that restored original byte-for-byte.
- Original preference backup remains in the Phase 9E directory. Fresh copies
  of active ISFDB4 preferences and customize.py.json were also saved in the
  Phase 9G evidence directory before installation.
- No Calibre GUI, library worker, calibredb or ebook-convert process was active.
- Offline suites passed before the installation gate.

Used only supported commands, in separate completed processes:

```
calibre-customize -r ISFDB4
calibre-customize -a <Phase9G artifact directory>\ISFDB4-corrected.zip
```

Removal/addition succeeded, reporting ISFDB4 (1, 4, 14). This avoids the known
same-process old/new objects-module collision without changing Calibre internals
or manually replacing ZIP files. No interactive confirmation or forced GUI
termination was needed. A fresh Calibre process subsequently loaded the candidate
from C:\Users\apt\AppData\Roaming\calibre\plugins\ISFDB4.zip, verified its exact
hash and module origin, and found the corrected title_relevance helper.

The candidate remains installed after testing. With no pre-existing GUI process,
no GUI restart was necessary; the next ordinary Calibre launch uses this ZIP.
No unrelated plugin was removed, installed or configured. Existing Fantastic
Fiction/Kobo invalid-escape SyntaxWarnings appeared at normal Calibre startup;
they were not ISFDB4 failures and their source was not changed.

## Offline regression results (fresh execution)

Calibre 9.17.0 / embedded Python 3.14.8:

| Suite | Executed | Passed | Failures | Errors | Skipped | Expected failures |
|---|---:|---:|---:|---:|---:|---:|
| Complete ordinary regression | 154 | 153 | 0 | 0 | 0 | 1 |
| Camoufox fixture-only feasibility | 24 | 24 | 0 | 0 | 0 | 0 |

The sole expected failure remains the unverified advanced-search table layout.
No assertions were weakened, no new expected failures/skips were added, and no
real Camoufox process was started. The ranking fixture/tests are present and
all prior metadata, identity, series, cancellation, preference and duplicate
coverage remains passing.

## Live methodology and request bounds

Used installed-plugin discovery in a fresh Calibre process against the actual
owner configuration. Each test collected Metadata previews in queues; no GUI
book dialog, database connection, metadata save or library argument was used.
The helper explicitly forbade SQLite connections and subprocess launches after
startup. No Windows sandbox/ACL/firewall/VM work was pursued.

ISFDB4 preferences were copied to an in-memory session dictionary. Normal name
searches used search_titles=True and search_publications=False to bound
publication expansion; max_results was 1 or 3 and max_covers=1. This alters no
saved user settings. Original preference object was restored in finally.
Record requests kept the existing headers, TLS and minimum 90-second timeout.
Existing Calibre browser transport downloaded the image; no browser replacement
or network policy override was made. Requests were spaced by the helper, with
a hard main-session ceiling of 32 top-level opens and stop-on-failure behavior.

Main matrix consumed 22 top-level opens. Supplemental exact-prefix/decimal
checks and one source inspection consumed seven more: **29 total**, still below
the overall ceiling of 32. Existing transport redirects can involve additional
underlying exchanges; these are counts of top-level record/browser open calls.
Twenty-eight recorded statuses were HTTP 200; the one source inspection used
the unchanged fetch helper and completed without HTTP error. No 403, 429, timeout,
retry storm, bypass or unexpected HTTP failure was observed.

Advanced search returned its restriction notice and the plugin used its existing
public simple-search fallback. No authenticated result table or access-control
workaround was introduced. Live observations are time-specific, not a promise
of future site availability.

## Required live cases

| Case | Result and assertions | Opens |
|---|---|---:|
| A. Publication #262210 | The Silver Locusts, Ray Bradbury; isfdb=262210, title ID 918018, catalog GS7185; date 1965-01-01. Series The Martian Chronicles with absent index; cover URL cached. | 3 |
| B. Title #41896 | In the Vault, H. P. Lovecraft; correct title ID; date 1925-11-01; absent series/index handled without invented values or crash. | 1 |
| C. Exact-title ranking, max=1 | The End of Eternity, Isaac Asimov; full novel title ID **2009**, not excerpt 691469. | 3 |
| D. Expanded ranking, max=3 | Novel #2009 first; excerpt #691469 and novella #954263 retained, no duplicate identities or exceeded limit. | 5 |
| E. Author-only, max=1 | Isaac Asimov name query followed author bibliography **ea.cgi?5**; returned The Club of the Black Widowers #3184549, credited to Isaac Asimov, series Black Widowers. Missing date/index retained as absent; plausible author bibliography, not a merged identity. | 3 |
| F. Coauthors | Good Omens: The Nice and Accurate Prophecies of Agnes Nutter, Witch #6543; **Neil Gaiman, then Terry Pratchett**. Output order matched parsed source credit order; both credited author identities retained. | 3 |
| G. Series | The Colour of Magic #2208, Terry Pratchett; **Discworld, 1.0**. | 3 |
| H. Publication cover/cache | Existing cached URL for publication #262210 used without refetching record HTML; JPEG decoded/verified, **368 × 600**, 93,049 bytes. | 1 |

Every required case passed. Publication and title identities remained distinct;
each returned result set contained unique (publication ID,title ID) pairs.
This sample does not assert every edition/ambiguity case has been tested live.

Image URL: https://www.isfdb.org/wiki/images/3/35/THSLVRLCST1965.jpg
Image SHA-256: 4f492a94887ee41840abb5e3fae17791af80595702bd3121f29cc97c87d72c21.
Raw bytes were verified with Calibre's already-bundled Pillow and retained only
outside the repository; no dependency was downloaded or installed.

### Supplemental checks and honest limits

- `=The End of Eternity` / Isaac Asimov returned #2009 using the explicit exact
  query path (three opens). Persistent exact_search remained False. This tests
  request-local exact behavior in addition to normal contains/ranking queries.
- Tried Home: Habitat, Range, Niche, Territory / Martha Wells as a possible
  fractional-series record (three opens). It returned title #2867474 with no
  series/index. One bounded detail inspection found no Series label in the
  title content. It was therefore NOT a suitable live decimal-index validation;
  no decimal was invented or claimed verified. Integer series behavior passed;
  decimal behavior remains covered by the offline 1.5/2.25 regressions.
- An initial one-line source-inspection command had a shell quoting/SyntaxError
  before executing its code, so it sent no request. The equivalent saved helper
  then completed the single inspection. This was a helper failure, not a plugin
  regression; it did not require source or installed-plugin patches.

## Configuration and final installation verification

Active ISFDB4 preference file remained byte-for-byte identical to the before
snapshot and Phase 9E backup:
SHA-256 aab259b846970f31b620a4126935c2bdcbe46e45ea8b7cb0fdc13052050e758c.

Fresh-process readback: max_results=300, max_covers=300, language=ger,
exact_search=False, identity ISFDB4, version 1.4.14. Small live-test limits and
exact flags did not persist. customize.py.json is semantically unchanged,
including enabled/disabled plugin set membership; serialization order is not a
configuration change. All normal configuration fields/format are preserved.

Active plugin ZIP matches candidate SHA
87b22e5d54779214f6de21ab301d438e49bad51b4db207d1c682c1a6831f8821.
Original backup still matches its expected original hash. No rollback was
required or performed during Phase 9G. No backup was deleted.

## Evidence, limitations and adoption

Evidence directory retains candidate/repeat ZIPs, staging, manifest/patch,
pre-test preference/registration copies, validate_live.py, live-results.json,
live-diagnostics.txt, publication-cover.bin, decimal/exact probe results/logs,
decimal-source-inspection.json and final-verification.json. Offline output is
also in system TEMP as isfdb4-phase9g-regression.txt. Helpers/logs/owner data are
not repository inputs or part of the candidate ZIP.

Known limitations persist: advanced-table expected failure; controlled rejection
of unsupported non-Latin-1 searches; unlinked author ambiguity; cooperative-only
cancellation of blocking requests; inherited disabled TLS verification and
resource/redirect policies; broader untested parser, periodical and external-ID
cases. No live decimal index was verified. This phase does not fix those
policies or certify the lower declared minimum/platform matrix.

Within the tested owner's Windows 10 / Calibre 9.17 environment and unchanged
existing network policy, **local adoption is supported and the corrected plugin
is left installed**. The corrected full-novel ranking and the remaining core
paths have now been exercised live. Keep the original backup for recovery and
report any newly observed failures; this remains a bounded validation, not a
guarantee about all ISFDB records or future availability.

## Git finalization recommendation — no automatic commit

Review and include exactly these pending files in the final local release
commit (the Phase 9E report update predates this phase):

```
README.md
__init__.py
docs/PHASE9E.md
docs/PHASE9F.md
docs/PHASE9G.md
tests/README.md
tests/run_calibre.py
tests/ranking.py
tests/fixtures/eternity_simple_search.html
```

Suggested message: `Adopt validated ISFDB4 exact-title ranking for local use`.
No ZIP, backup, owner config, live log or image should be committed. No push
or release tag is recommended/performed by this phase. The installed artifact
is already identified by its manifest; if a later build uses Git-normalized line
endings, record its new hash rather than claiming it is byte-identical to this
working-tree-byte candidate. Do not reinstall merely to change documentation.

HEAD remains 8c37b852c41748f65b9b03a6cca1c28b8f312d26. No staging or commit
operation was performed. git diff --check passes; ordinary CRLF-conversion
warnings are not whitespace failures. Phase 9G added only this repository
report; Phase 9F production/test changes remain pending for owner review.
