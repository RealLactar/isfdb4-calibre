# Phase 9E development checkpoint and live validation — 2026-11-05

Owner authorized testing/installing against the actual Calibre installation,
with verified original-plugin and ISFDB4 preference backups. No sandbox,
firewall, ACL, VM or Windows security changes are part of this phase.

## Pre-install checkpoint

Repository main, starting HEAD 759c404b7ac93b499ff0c1b2ecc4ab657c6b6b20.
Complete offline suite: 145 executed; 144 passed, 0 failures/errors/skips,
one existing advanced-search expected failure. Camoufox fixtures: 24 passed,
0 failures/errors/skips. Runtime confirmed live: Calibre 9.17.0 / embedded
Python 3.14.8. No actual Calibre application/library worker was running.

Original installed ZIP:
C:\Users\apt\AppData\Roaming\calibre\plugins\ISFDB4.zip
Static identity ISFDB4, version 1.4.14, correct import marker.
Original SHA-256:
9be3ce2cce7d3cd666b040757883e1791b55cb78e64ed9fda2836cceab38a760

Verified byte-for-byte backup directory:
C:\Users\apt\Documents\ISFDB4-Phase9E-Backup-20261105-084400
Original ZIP stored as ISFDB4-original.zip. ISFDB4-specific preferences copied
as metadata_sources/ISFDB4.json, SHA-256
aab259b846970f31b620a4126935c2bdcbe46e45ea8b7cb0fdc13052050e758c.
plugins/ISFDB4.json was not present. Backup preceded all live Calibre startup.
Calibre subsequently confirmed the expected active configuration path.

Only intended source, test, fixture and documentation changes are staged for
the checkpoint. No generated ZIP, backup, configuration, .codex artifact,
credential file, library or temporary runtime log is included. Existing tracked
IDE files are unchanged. No version, transport or security policy is changed.

Checkpoint SHA, candidate hash, installation/live outcomes and rollback status
will be appended after those operations; this pre-install record does not claim
they have already succeeded. No push or tag is authorized or performed.

## Final outcome

Development checkpoint completed. Candidate installed and exercised in the
actual profile. **Live validation did not fully pass; the original plugin has
been restored.** Keep the original installation for continued personal use.
Do not promote the candidate on the strength of the offline suites alone.

Checkpoint: `8c37b852c41748f65b9b03a6cca1c28b8f312d26`

Message: `Checkpoint ISFDB4 metadata correctness and reliability remediation`

The checkpoint contains 29 intended source/test/documentation files (including
the pre-install portion of this report), 5572 insertions and 232 deletions.
Earlier Git line-ending warnings concerned normal LF/CRLF conversion, not lost
files. This final report update is deliberately left uncommitted for review;
the candidate's production inputs are exactly the checkpoint's Git blobs.

Candidate:
C:\Users\apt\Documents\ISFDB4-Phase9E-Backup-20261105-084400\candidate\ISFDB4-checkpoint.zip

SHA-256:
`d07f49f97e2c1b894e318c9d867cbda1918fac3dbc9d2162852cfaecb4997132`

The Phase 9C allowlist/fixed timestamp/order/mode procedure was applied to the
committed blob bytes in a separate staging directory. Working files matched
the committed content, allowing Git's CRLF normalization. Two ZIP builds were
byte-identical; CRC and exact entry checks passed. Because this build uses Git
blob line endings, its hash differs from the earlier working-tree Phase 9C
archive despite unchanged program behavior. manifest.json records each entry
hash and source commit. ZIP entries:

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

No tests, backups, libraries, configuration, credentials or generated artifacts
were committed or included in the runtime ZIP. Existing notices/provenance and
plugin identity/version/configuration format were retained.

## Installation and rollback

The original ZIP and preferences were backed up and verified before the first
live Calibre startup. Active config_dir was then confirmed from Calibre itself.
No Calibre GUI, ebook conversion or library worker was running at either
installation or rollback. All live invocations were command-line, without a
library argument or database operation.

1. `calibre-customize -a <candidate>` failed with ImportError for UnsupportedQuery:
   Calibre had imported the old installed objects.py before reloading the new
   package. The original installed ZIP still matched its backup after this
   failed update. This was an actual installation-loader issue, not an HTTP
   failure or a request to disable a safeguard.
2. Backed up customize.py.json outside the repository. Used the supported
   `calibre-customize -r ISFDB4`, then `calibre-customize -a <candidate>` in a
   separate process. Candidate installation succeeded. Installed ZIP SHA-256
   exactly matched the candidate. No manual plugin-file overwrite, unrelated
   plugin removal, interactive confirmation bypass or process termination.
3. After the unsuccessful title/author preview below, stopped further live
   requests and used the same supported remove/add mechanism to restore
   ISFDB4-original.zip. Both commands succeeded.
4. Verified the restored active ZIP byte-for-byte against the backup and its
   original SHA-256. A fresh Calibre process discovered/loaded ISFDB4 1.4.14
   and its objects module from the restored active ZIP. No network request was
   made for rollback verification. No GUI restart was required because no GUI
   instance was running. The next normal launch uses the restored plugin.

ISFDB4 preference bytes remain identical to the pre-test backup; no preference
restore was needed. customize.py.json changed the serialized ordering of its
enabled/disabled sets, but set membership and all other top-level configuration
values match the backup. No plugin was semantically enabled/disabled by the
rollback. Do not restore the whole shared registry file over unrelated state.

## Controlled live previews

Real installed plugin, active owner profile, Calibre 9.17.0 / Python 3.14.8.
No book records were created/opened/saved. Queues collected Metadata previews.
Per-session settings were an in-memory copy: max_results=1, max_covers=1,
title searching enabled and linked-publication expansion disabled for name
searches. The original persistent preference object was restored in finally.
No HTTP headers, TLS, timeout, retry or production source changes were made.

The planned matrix included publication/title IDs, title/author, author-only,
coauthors, series and practical cover retrieval. A hard ceiling of 18 top-level
record-open calls applied across attempts (the resumed attempt had 14 remaining).
Actual use: **8 top-level record-open calls**, all returned HTTP 200. Existing
transport redirects may involve additional underlying HTTP exchanges; the count
is of recorded open calls. There were no 403/429 responses and no retry or
access-control bypass attempt. Existing restricted advanced search fell back
to the public simple search normally.

| Case | Observation | Outcome |
|---|---|---|
| Publication ID 262210 | The Silver Locusts; Ray Bradbury; isfdb=262210, catalog GS7185, title ID 918018; date 1965-01-01; series The Martian Chronicles, missing series index; cover URL detected | Expected title/author and stable identifiers returned. Three record fetches including auxiliary series/title pages. Cover image bytes were not downloaded. |
| Title ID 41896 | In the Vault; H. P. Lovecraft; title ID retained; date 1925-11-01; no series/index | Expected metadata returned. |
| Title + author: The End of Eternity / Isaac Asimov | The End of Eternity (Excerpt); Isaac Asimov; title ID 691469; date 1955-01-01 | Did not meet the intended exact-work expectation. Live validation stopped. |
| Author-only | Not attempted after stop condition | Unverified live; offline coverage still passes. |
| Multiple-author work | Not attempted after stop condition | Unverified live. |
| Dedicated series case | Not attempted after stop condition | Publication preview supplied incidental series data only. |
| Cover retrieval | No image download after stop condition | Detected publication cover availability only; live image bytes/cache behavior not validated here. |

The title/author request used normal contains matching with the deliberately
small one-result limit. An excerpt is a related work, but not the requested
novel. It is not established that this is a newly introduced regression or that
the owner's normal larger result limit has the same failure. Candidate selection
currently sorts by date before limiting, so exact-work prioritization is a
plausible explanation requiring an independent focused reproduction. No new
production fix was attempted during this validation phase. Rollback was the
conservative response to an unsuccessful validation, not proof of new code blame.

No duplicate metadata entries were returned in these previews; this limited
sample does not certify all edition/duplicate cases. Missing series/index fields
were represented without a crash. No unexpected HTTP error was observed in
the executed cases. The broader matrix remains incomplete.

### Validation-harness issues, separated from plugin behavior

- The first helper invocation omitted metadata_plugins' required capabilities
  argument. It stopped before any live request; the helper was corrected.
- Attempt 1 successfully fetched the publication and title preview, but its
  report serializer assumed every Metadata object had has_cover. Title-only
  results legitimately lack that attribute. This reporting exception stopped
  the attempt after four requests. The helper was corrected with getattr(...,
  False), and the first attempt's JSON/log were preserved. Publication was not
  fetched again; the title preview was repeated once, then the title/author
  lookup encountered the selection issue. These corrections affect only the
  external helper, not repository/plugin code.
- Calibre startup printed invalid-escape SyntaxWarnings from existing Fantastic
  Fiction and Kobo Metadata plugins. Their code was not modified and those
  warnings were not treated as ISFDB4 HTTP or metadata defects.

## Evidence retained and recommendation

The backup directory retains original ZIP/preferences, plugin-registration
snapshot, candidate/staging/manifest, original identity JSON, live_validation.py,
live-results-attempt1.json, live-diagnostics-attempt1.txt, live-results.json,
live-diagnostics.txt and rollback-verification.json. No backup was deleted.
The helper's result counts/budgets in its individual reports must be read with
the aggregate eight-call history described above, not as extra permitted calls.
Offline regression output is also retained in system TEMP as
isfdb4-phase9e-regression.txt. No owner metadata was saved to book records.

Keep the restored original plugin for continued local use. The development
checkpoint and candidate remain available for focused exact-work ranking tests,
followed by a separately authorized bounded rerun of the unexecuted live cases.
Do not promote this candidate to the normal installation yet. Inherited TLS
verification, timeout and other previously documented limitations remain
unchanged; this phase introduces no Camoufox or Windows security modifications.

Final repository state: checkpoint committed locally; only this report's final
outcome update is modified/uncommitted. No untracked test artifacts/backups/ZIPs
remain inside the repository. git diff --check passes. No push or tag was made.
