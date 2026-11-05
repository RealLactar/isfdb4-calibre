# Phase 9C local release validation — 2026-11-05

## Outcome

**PARTIAL / runtime validation blocked at the pre-start isolation gate.**
Static packaging succeeded. No Calibre component/process was imported or
started during Phase 9C, and neither test suite was rerun in this phase.
The user explicitly required: "If reliable isolation cannot be established,
stop before starting Calibre." That instruction takes precedence over completing
the later runtime steps without the requested safeguards.

This assessment is for the owner's personal Windows 10 / Calibre 9.17.0
installation. Public announcement, third-party distribution and plugin-repository
submission are not goals or release conditions here. Broader minimum-version,
Linux/macOS and public-release requirements are not imposed on this local build.

## Candidate identity and working tree

Repository: C:\Users\apt\Git\Calibre-ISFDB4\isfdb4-calibre.
Branch: main. HEAD: 759c404b7ac93b499ff0c1b2ecc4ab657c6b6b20.
The candidate is HEAD plus the current uncommitted Phase 1–9B work, not HEAD
alone. This phase changes no production code or version numbers. Its only
repository addition is this report. Prior changes/untracked files are preserved.

Production input SHA-256 values:

| Module | SHA-256 |
|---|---|
| __init__.py | d961b59a3b0f52df263f7381106d2760e51b0185062c5ba026c1a45fc6e586f2 |
| objects.py | c1efdf1a4a4f390b9611e40b54b2b209074c0b21e5ea2b52b9570656e72967a5 |
| myglobals.py | a14c7cd7f33c1e1ad37a5de17db91d5dfce5243e01eab705efc8c20401d5ab51 |

Static plugin metadata: name ISFDB4; version 1.4.14; declared minimum Calibre
5.0.0; declared platforms Windows/Linux/Mac; author credits Michael Detambel
and Adrianna Pińska's ISFDB2. Capabilities are identify and cover. touched_fields
includes title, authors, series/index, language, rating, publisher, date,
comments, tags and ISFDB/external identifiers. This describes declarations;
runtime discovery/defaults/initialization were not exercised during this phase.
File metadata for the installed calibre-debug.exe reports version 9.17.0.
Embedded Python 3.14.8 remains previously established Phase 9B evidence, not a
new interpreter execution in Phase 9C.

The functioning plugin requires the three production Python modules, root
plugin-import-name-isfdb4.txt marker and available translations. There is no
config.py: Source options supply the configuration UI. AST import inspection
finds standard-library modules, Calibre APIs, Calibre-bundled lxml and the two
packaged calibre_plugins.isfdb4 submodules. The optional __main__ live examples
are not a release validation mechanism and were not executed. No dependency
was installed or downloaded.

## Packaging audit and artifact

Existing scripts were read, never executed:

| Script/command | Side effects |
|---|---|
| plugin_install.bat: calibre-customize -b . | Builds AND installs/registers into the active configuration; unsuitable as a build-only command. |
| dev_install_and_restart.bat | Same install/build, force-kills calibre.exe, then starts the live GUI. Not safe for this validation. |
| debug.bat: calibre-debug -g | Starts the GUI against the selected/default configuration. Not a package check. |

Those scripts do not explicitly edit a library, but a launched GUI can open the
configured library; that indirect exposure is enough to exclude them here.
No existing install script has a verified build-only switch in this repository.

Artifact root (disposable, outside the repository):
C:\Users\apt\AppData\Local\Temp\isfdb4-phase9c-bca93c68-9b56-448f-ba38-aeb865b5adc9

Candidate: ISFDB4-local-candidate.zip in that directory.

**Build SHA-256:**
`892e3ced4200030a0a3ec827de8f099b449d8fa1864cef785983697b647d538f`

Exact nine-entry ZIP manifest:

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

package_candidate.py, retained in the artifact root, copies an explicit allowlist
into stage/, then writes sorted entries with fixed 1980 timestamps, fixed file
mode and compression settings. It builds a second archive and compares bytes.
No directory-wide build or installer was invoked. The temporary stage and ZIP
contain no tests, fixtures, .idea, .git, bytecode, batch scripts, live configuration,
credential files, environment dumps or user libraries. README/provenance are
intentional notices, not accidentally included development directories. They
contain historical development links/snapshot paths; some referenced review
documents are intentionally not part of the runtime ZIP. Read those references
in the repository; they are not runtime dependencies.

Checks executed successfully:

- ZIP CRC/integrity test and exact entry-set comparison.
- Every entry's SHA-256 equals its corresponding checkout file.
- Repeated build byte-for-byte equality.
- Static AST parsing of each production Python file, without executing imports.
- Import-name marker present at ZIP root (its CRLF contents are not code).
- Source inputs unchanged after packaging; detailed inventory hashes retained.

The static packager used standalone Python 3.15.0 only for copying, ZIP creation,
AST inspection and hashing. It did NOT substitute that interpreter for Calibre
plugin/runtime tests. Static parsing does not prove Python 3.14 compatibility.
The root layout matches the previously tested Calibre plugin layout, but this
exact nine-entry ZIP has NOT been loaded through Calibre yet.

Retained evidence files: manifest.json (entry sizes/hashes, candidate identity,
metadata, status and archive hash), input-sha256.json (all 43 pre-report tracked
and untracked files), isolation-plan.json, the build script, both archives and
stage/. None is stored in the repository or installed into Calibre.

## Isolation preflight — failed, no Calibre startup

The existing runners correctly set CALIBRE_CONFIG_DIRECTORY, cache/temp paths
and no-bytecode flags before launching calibre-debug. Their Python audit hooks
then block sockets, DNS, subprocesses, SQLite and ordinary non-disposable writes
after their scripts begin. The feasibility runner also prevents actual browser
and dependency launch. These are useful secondary guards, but neither hook
exists before Calibre executable startup or constrains arbitrary native calls.
Thus they do not alone establish the stronger Phase 9C pre-start network rule.

Read-only Windows firewall checks returned:

- Effective ActiveStore Domain, Private and Public profiles: enabled, outbound
  default **Allow**.
- Query for enabled outbound application block rules: **Access is denied**.
  This does not prove no block rule exists; it means no effective per-application
  block could be verified with the current access. No network probe was sent.

No firewall rule or OS policy was changed. A pre-start, effective external-network
block for Calibre was therefore NOT established. I stopped before running either
Calibre launcher, plugin loader, metadata integration or Camoufox fixture suite.
There was no repeat of Phase 8's late-environment startup mistake.

Prepared (but not activated in a Calibre process): empty profile/config/plugins,
profile/cache and profile/temp under the artifact root. No plugins.json or user
ZIP exists there, and no live user plugins/config were copied. An empty-library
directory is merely reserved; it is not a Calibre library and has no database.
Metadata-only validation needs no library or GUI.

isolation-plan.json records settings that must be applied by the parent BEFORE
future startup: CALIBRE_CONFIG_DIRECTORY, CALIBRE_CACHE_DIRECTORY,
CALIBRE_TEMP_DIR, TEMP, TMP, PYTHONDONTWRITEBYTECODE and deterministic language;
clear inherited development source, database override, metadata-browser-worker,
PYTHONPATH and PYTHONHOME overrides. All configured paths are under the disposable
root. The plan is NOT a successful isolation certificate or a runnable bypass.

After network containment is established, verify actual config/cache paths and
plugin module origins at runtime, confirm no installed user plugin modules are
present, prohibit GUI/library access, and load only the candidate ZIP. Empty
directories are preparation evidence, not proof about an unexecuted process.

## Load, integration and regression status

| Validation | Phase 9C result |
|---|---|
| Static package inventory/integrity/repeated hash | PASS |
| No production input changes | PASS |
| Pre-start external-network containment | NOT ESTABLISHED |
| Exact candidate ZIP through Calibre loader | NOT RUN — isolation gate |
| Runtime discovery/imports/defaults/initialization | NOT RUN — isolation gate |
| Offline metadata/cover integration matrix | NOT RUN — isolation gate |
| Complete ordinary regression suite | NOT RUN — isolation gate |
| Camoufox fixture-only suite | NOT RUN — isolation gate |

There are no new passed/failed/error/skipped/expected-failure counts to report
for unexecuted suites. They were not silently skipped by unittest, and prior
results must not be relabelled as new Phase 9C results.

Last confirmed Phase 9B results (historical):

| Suite | Passed | Failed | Errors | Skipped | Expected failures |
|---|---:|---:|---:|---:|---:|
| Ordinary: 145 executed | 144 | 0 | 0 | 0 | 1 |
| Camoufox fixtures: 24 executed | 24 | 0 | 0 | 0 | 0 |

That ordinary suite covers identifiers, title/author and author-only lookup,
publication/title merging, coauthors, series/decimals, canonical duplicate
suppression, cancellation, local preferences, missing fields, templates, covers,
worker errors and Unicode metadata. No tests were modified or weakened in 9C.
The advanced-search test is still the sole documented expected failure, but
this phase cannot independently reconfirm its execution. Camoufox production
integration remains absent; no real browser or worker process was launched.

When the isolation gate is resolved, validate this artifact rather than silently
rebuilding a different ZIP. Existing test launchers build their own six-entry
checkout ZIP; rerunning them alone does not prove this nine-entry candidate was
loaded. A disposable validation adapter should first load the exact artifact
with calibre.customize.zipplugin.loader.load, check module __file__/plugin_path
and all ZIP hashes, initialize the returned class, inspect capabilities/defaults,
then run the existing offline suite against that same ZIP. No add_plugin call
or live registration is needed for that loader/integration step.

## Security and target compatibility

The static artifact has the same production modules as the Phase 9B tree;
no new executable code or network dependency was added. Previously verified
9.17/Python 3.14.8 compatibility is encouraging but does not replace the blocked
runtime validation. Other operating systems/minimum Calibre 5.0 are outside
this owner's target and are not additional local release gates.

Inherited disabled TLS verification means a network attacker able to intercept
traffic could substitute metadata, covers or URLs. Unrestricted redirects,
unbounded bodies, substantial concurrency and cooperative-only cancellation
remain risks. No exploit or unacceptable new packaging vulnerability was
demonstrated here. Those inherited policies should not be labelled safe merely
because this is personal use; nor is public-release hardening automatically
required for an owner who knowingly retains the existing policy.

For online personal adoption, the owner must explicitly decide whether the
inherited unauthenticated transport is acceptable on their network, or authorize
a separate TLS/security remediation. No such acceptance is inferred from an
offline packaging request. This audit changes no TLS, timeout floor, headers,
retries, diagnostics, browser implementation or Unicode behavior.

Advanced-search layout remains unverified, non-Latin-1 name queries deliberately
fail in a controlled manner, unlinked author identities can be ambiguous, and
some parser/cover-consumer cases remain deferred as documented in PHASE9B.md.
These are owner-facing limitations to assess for local use, not invented public
distribution requirements. No live ISFDB availability or 403 success is claimed.

## Attribution verification

GPLv3 LICENSE is included unchanged. README and the complete provenance ledger
preserve ISFDB2/ISFDB3 lineage, Michael Detambel/bertholdm's 1.5.0 commit
b8ff4a0fd4175b64843334bb787b62f8151e1146, Calibre API/diagnostic attribution
and the distinction from local ISFDB4 work. The ledger acknowledges Adrianna
Pińska, Xtina Schelin, Brian Schweitzer and Grant Drake without claiming all
lines were written by each contributor. Unresolved history questions remain
labelled unresolved. No upstream code was incorporated during packaging.

The development changelog accurately describes 9A/9B, including the intentional
0..5 source rating conversion and the absence of Camoufox integration. Existing
historical version/date/help inconsistencies are not rewritten here; no version
number is changed. The ledger's historical input hashes are not asserted to be
the current candidate hashes; use the manifest above for this candidate.

## Local release recommendations

| Action | Decision | Exact path to GO |
|---|---|---|
| A. Development Git checkpoint | GO | Review/stage the intended code, tests and docs together and label remaining gates honestly. No commit performed. |
| B. Local release commit | NO-GO pending validation | Establish pre-start network isolation; load and test the exact candidate under Calibre 9.17/Python 3.14.8; rerun ordinary and fixture suites; record hashes/results; review intended tracked/untracked content. No public submission/multi-platform validation is required for this owner's local target. |
| C. Isolated test-profile installation | NO-GO until isolation gate passes | Use a verified network-disabled Windows sandbox/VM with the target runtime, or a verified effective process-level block covering native/child networking; set/check all disposable paths before startup. First pass non-registering loader validation, then use only that disposable profile for any installation test. |
| D. Replace currently installed ISFDB4 | NO-GO | Complete B/C and owner review of results/remaining limitations, explicitly decide inherited online TLS policy, then separately authorize installation. Preserve a recoverable old plugin/config backup before a later authorized replacement. No live installation occurs now. |

Do not solve the gate by moving environment setup inside the Python script,
turning off audit guards, starting the GUI, or assuming a post-start hook is
equivalent to network containment from process creation. No approval was sought
for broad firewall changes; none was attempted. The failed rule-query access
is an environment limitation, not an automatic-approval rejection.

## Complete repository inventory and Git evidence

Modified tracked files: README.md, __init__.py, objects.py (all prior phases).
This report is the only Phase 9C repository addition. No tracked/untracked file
was deleted or discarded. Full tracked inventory (20 files):

```
.gitattributes
.gitignore
.idea/.gitignore
.idea/inspectionProfiles/Project_Default.xml
.idea/inspectionProfiles/profiles_settings.xml
.idea/isfdb4-calibre.iml
.idea/misc.xml
.idea/modules.xml
.idea/vcs.xml
LICENSE
README.md
__init__.py
debug.bat
dev_install_and_restart.bat
myglobals.py
objects.py
plugin-import-name-isfdb4.txt
plugin_install.bat
translations/de.mo
translations/de.po
```

Untracked inventory after this report (24 files):

```
docs/CAMOUFOX_FEASIBILITY.md
docs/PHASE8_AUDIT.md
docs/PHASE9A.md
docs/PHASE9B.md
docs/PHASE9C.md
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

Cumulative tracked git diff --stat (untracked files are excluded):

```
 README.md   |  29 +++++
 __init__.py | 407 ++++++++++++++++++++++++++++++++++++++++--------------------
 objects.py  | 365 ++++++++++++++++++++++++++++++++++++++---------------
 3 files changed, 569 insertions(+), 232 deletions(-)
```

git diff --check passes with no output. No production, test, live configuration,
library or application file was modified in this phase. No install, executable
build script, external request, dependency download, native browser launch,
commit, push, reset, clean, stash or discard operation occurred. Firewall
application-rule enumeration was the failed check; later runtime checks were
deliberately not attempted. Runtime isolation remains unproven, not silently
waived. Stop here pending the stated pre-start gate.
