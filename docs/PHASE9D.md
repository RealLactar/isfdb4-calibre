# Phase 9D containment investigation — 2026-11-05

## Outcome

**The runtime validation blocker is unresolved. Phase 9D did not achieve the
runtime-validation objective.** No Calibre component, loader, regression suite,
GUI, library or real Camoufox process was started. No isolation requirement was
waived. This report records both the investigation and a safeguard incident;
it must not be read as a successful containment certificate.

The least disruptive identified route is a disposable copy of the existing
VirtualBox Windows 10 VM with every virtual network adapter disconnected before
its first boot, no writable host shares, and verified guest execution. That
environment has not been created or tested. Existing VMs were not modified or
booted. No claim is made that target Calibre or usable guest access already
exists inside them.

## Verified repository/candidate state

Repository: C:\Users\apt\Git\Calibre-ISFDB4\isfdb4-calibre.
Branch main; HEAD 759c404b7ac93b499ff0c1b2ecc4ab657c6b6b20.
All Phase 9C input hashes remain unchanged. Existing code/tests/documentation,
including the historical audits, were preserved. The sole repository change
in this phase is this report. Production version remains 1.4.14.

Candidate still exists:
C:\Users\apt\AppData\Local\Temp\isfdb4-phase9c-bca93c68-9b56-448f-ba38-aeb865b5adc9\ISFDB4-local-candidate.zip

Its SHA-256 was independently recalculated and matches the required value:
`892e3ced4200030a0a3ec827de8f099b449d8fa1864cef785983697b647d538f`.
No rebuild, substitute ZIP, install or plugin registration was performed.

PHASE8_AUDIT.md, PHASE9A.md, PHASE9B.md, PHASE9C.md and
UPSTREAM_PROVENANCE.md were reviewed. The unresolved Phase 9C gate is not ZIP
construction: it is proving effective external-network containment, including
native/child processes, BEFORE Calibre startup, combined with protection of
live configuration/plugin/library paths. Existing audit hooks begin after
calibre-debug startup and do not prove that stronger property.

## Availability investigation (read-only except the incident below)

| Option | Actual evidence on this machine | Assessment |
|---|---|---|
| A. Separate/restricted user | Enabled local users include apt2, CodexSandboxOffline and CodexSandboxOnline; CodexSandboxUsers group and an existing sandbox setup marker are present. runas.exe is present. | Accounts exist, but a different username alone does not prove network or filesystem containment. No credentials were requested/extracted. The existing automated launcher has the ACL-refresh side effect described below. No supported no-change launch path was established. |
| B. Windows Sandbox | WindowsSandbox.exe absent at its system path and from PATH. Win32_OptionalFeature reports Containers-DisposableClientVM InstallState=2 (disabled). | Not currently available as an enabled mechanism. No feature was enabled. |
| C. Offline VM | VirtualBox 7.1.0.164728 exists at C:\Program Files\Oracle\VirtualBox\VBoxManage.exe, although it is not on PATH. Two .vbox files exist. | Installed and potentially usable without new host components, but neither VM is currently network-disabled. No safe guest execution has been verified. |
| D. Constrained process | Existing Codex CLI exposes a restricted-token sandbox command; its setup marker identifies offline/online sandbox accounts. | CLI availability is confirmed; all-path native/child network denial and live-path protection are not. The invocation incident rules out treating this launcher as a no-security-change method. A plain environment-variable change or unelevated username is insufficient. |
| E. Calibre test mechanism | Existing fixture runners use disposable env paths, ZIP loader and Python audit hooks; Calibre runtime only starts after their PowerShell setup. | Good application-level fixture guards, but no pre-start OS containment for native/child network paths was established. No Calibre-specific method was found that proves all requested properties without an external containment boundary. |

Additional environment facts:

- CPU virtualization firmware and VM-monitor extensions report enabled.
- Win32_ComputerSystem reports HypervisorPresent=false. This is not proof that
  VirtualBox cannot run; it can use its installed virtualization drivers.
- VBoxSup, VBoxUSBMon, VBoxNetAdp and VBoxNetLwf drivers report Running.
- HvHost and VBoxSDS services report Stopped/Manual. No service was started.
- Hyper-V, Virtual Machine Platform and Windows Subsystem for Linux optional
  features report InstallState=2 (disabled). wsl.exe exists, but was not treated
  as evidence of an enabled Linux VM. No registered distro was found in the
  checked user registry location. No WSL startup/update command was executed.
- VMware tools/standard installation directories, Docker CLI and Sandboxie
  executable/service paths checked were absent. No component was installed.
- No running VirtualBoxVM/VBoxHeadless/VMware/Hyper-V guest process was returned
  by the process-name check. No existing guest session was assumed accessible.

VM XML inspection, without a VirtualBox launch:

| VM | Declared OS type | Adapter 0 | Shared folders |
|---|---|---|---|
| STFC 1 | Windows10_64 | enabled=true; NAT | none declared |
| WinDev2401Eval | Windows11_64 | enabled=true; NAT; localhost-reachable=true | none declared |

The OS labels are VM metadata, not a verified running Windows version or
Calibre installation. Disk locations are STFC 1.vdi and
WinDev2401Eval-disk001.vdi respectively. Neither base disk was opened for
writes, cloned or booted. Existing .vbox timestamps remain historical; their
hashes/timestamps were saved as read-only evidence. A VM's NAT-enabled state
does not satisfy the requested disabled-network boundary, even if it has no
writable host folders.

No new restricted account, AppContainer profile, ACL grant, firewall rule,
Windows feature or VM configuration was deliberately created. The qualification
about ACLs is essential: the next section describes an automatic helper action.

## Safeguard incident — attempted help caused an ACL refresh

One investigative command was mistaken:
`codex sandbox windows --help`. This installed CLI uses the syntax
`codex sandbox [OPTIONS] [COMMAND]...`; it does NOT have a `windows` subcommand.
It interpreted `windows --help` as the child command, not as a help request.

The command failed before that child program could execute:
CreateProcessAsUserW error 2, command not found. However, the existing sandbox
launcher first ran a setup refresh. Its log records, around
2026-11-05 08:39:31–08:39:32 UTC (02:39 Chicago):

```
setup refresh: spawning ...codex-windows-sandbox-setup.exe
failed to grant non-inheriting read-attributes ACE on user profile ...;
  sharing violation; continuing setup
read-acl-only mode: applying read ACLs
read ACL run completed
setup refresh: processed 0 write roots (read roots delegated); errors=[]
helper copy: reused command-runner ...
hide users: failed to hide current user profile dir ... Access is denied
```

This crossed the requested no-security-settings-change boundary. It is NOT
correct to claim Windows security settings were untouched. The log shows an
ACL refresh was performed; without a pre-invocation ACL snapshot, the exact
set of changed access entries cannot be established. The failed profile-root
ACE attempt does not prove that no other read ACL changed.

I stopped using that launcher after discovering the behavior and disclosed the
incident during the work. No blind ACL rollback was attempted: without a known
baseline it could discard legitimate existing permissions or cause more harm.
No uninstall/setup/repair command was issued. Subsequent CLI calls were the
top-level help and `help sandbox` paths, not sandboxed command executions.
No claim is made that this launcher is acceptable under the current safeguards.

Known non-repository file writes associated with the incident:

- C:\Users\apt\.codex\.sandbox\sandbox.2026-11-05.log (log appended).
- C:\Users\apt\.codex\.sandbox\deny_read_acl_state.json (write timestamp
  08:39:31.7108794 UTC; current contents are an empty principals object).

The log says the existing command-runner binary was reused; no new helper
download/install was performed. setup_marker.json still describes the existing
2026-10-30 setup. No firewall/account-creation command was invoked by this work;
the helper reported read-ACL-only mode. Its exact ACL effects cannot be certified
or reversed from the available evidence. No Calibre command was passed to it.

## Containment/probe status

No method passed the selection gate, so no actual contained disposable probe
was executed and no test network traffic was sent. The failed `windows --help`
attempt was not a successful harmless-program containment test. Account names,
setup markers, disabled-feature metadata and environment plans are not network
or child-process test results.

| Required proof | Result |
|---|---|
| External native connections rejected before Calibre startup | NOT ESTABLISHED |
| Child processes inherit effective containment | NOT ESTABLISHED |
| Live configuration/plugin/library writes impossible | NOT ESTABLISHED for a running candidate context |
| Temporary/config/cache paths isolated | Prepared previously, not verified inside a new contained process |
| Runtime/binary path integrity | Candidate hash matches; installed runtime not executed |
| Live installed plugins cannot be discovered | Not verified in a running candidate context |
| Harmless probe passes network/child/file tests | NOT RUN — no accepted containment method |
| Exact candidate through Calibre ZIP loader | NOT RUN |
| Integration/regression/Camoufox fixture suites | NOT RUN |

Therefore Calibre remained unstarted, in accordance with the gate. There are
no new runtime pass/failure/error/skip/expected-failure counts in Phase 9D.
Historical Phase 9B ordinary result remains 145 executed: 144 passed, zero
unexpected failures/errors/skips and one advanced-search expected failure.
Historical separate Camoufox fixture result remains 24 passed. These are not
relabeled as fresh results or evidence that this exact ZIP has now been loaded.

## Least disruptive viable next step

Use VirtualBox already installed, rather than enabling Windows Sandbox/Hyper-V,
changing host firewall policy, or reusing a launcher that refreshes ACLs:

1. Prepare a disposable copy of the Windows10_64 STFC 1 guest, protecting the
   existing owner VM/disks from writes. A metadata OS label is not enough;
   establish usable guest access and actual Windows version. Do not guess or
   extract guest credentials. No guest-access method has been verified yet.
2. Disconnect/disable every virtual network adapter in that disposable VM
   before its first boot. Keep writable host shares, clipboard/drag-and-drop
   integration and other host write channels absent. These are per-clone VM
   settings, not host firewall or Windows-security changes. This preparation
   was not performed in Phase 9D; no existing VM configuration was changed.
3. Transfer only the hash-verified ZIP, fixtures/validation scripts and verified
   existing Calibre 9.17 bundle using a read-only controlled input medium. Prove
   that the owner's host configuration/libraries are not exposed for writes.
   Target runtime presence/usability in the guest must be established; do not
   assume it or install/download missing dependencies under the current request.
4. Before Calibre, run a harmless guest-native probe plus its child: verify
   no external route/adapter, controlled connection attempts fail without relying
   on timeout alone, child restrictions persist, only disposable files can be
   written, and host live paths are inaccessible. Use no live ISFDB endpoint.
   Successful evidence must precede any Calibre execution.
5. Set all disposable config/cache/temp/discovery overrides in the parent
   environment. Load the exact candidate ZIP, verify origin and defaults, run
   the ordinary suite against that artifact, then the fixture-only Camoufox
   suite. Never invoke a live install/restart batch script.

The installed VirtualBox/driver evidence makes this a concrete non-admin route
to investigate, not a tested VM solution. Guest access, verified disconnected
networking, read-only input transfer and runtime availability remain prerequisites.
No administrator privilege is requested for this report or its findings.

## Security and local-release assessment

Inherited unverified TLS is a confirmed design decision: endpoint certificate
authentication is disabled. The associated interception risk is real; no
interception exploit was tested. Redirect/body/resource limits and cooperative
cancellation retain their documented risks/limits. None of these policies was
changed. Camoufox remains unintegrated and NO-GO; advanced-search layout remains
unverified. Source 0..5 rating conversion is intentionally correct as established
in Phase 9A. Do not reopen those resolved findings without evidence.

The current release blocker is the absent containment proof and missing
exact-artifact runtime validation, not a public-distribution checklist. Future
online personal adoption also needs the owner's informed decision about the
inherited TLS policy. No public submission or multi-platform certification is
required for the owner's target Windows/Calibre version.

| Action | Decision | Remaining prerequisite |
|---|---|---|
| A. Development checkpoint commit | GO as an honest development checkpoint | Review/stage intended changes and this incident/blocked-state report; no commit performed. |
| B. Local release commit | NO-GO | Successful contained harmless probe, exact candidate load and fresh full regression/integration results under target runtime. |
| C. Isolated plugin installation | NO-GO | Establish and verify a genuinely contained disposable context first; then non-registering loader validation before any isolated-profile install. |
| D. Replace live ISFDB4 | NO-GO | Satisfy B/C, owner review of remaining limits/TLS policy and separate installation authorization with a recovery plan. |

## Files and evidence

Only repository addition: docs/PHASE9D.md. Existing tracked modifications stay
README.md, __init__.py and objects.py, all from earlier phases. No existing
production/test/documentation input was modified, and the candidate was not
rebuilt. Outside-repository investigative evidence created here:

C:\Users\apt\AppData\Local\Temp\isfdb4-phase9d-b3915ec7-711e-4455-888f-7049cb87a684

- sandbox-incident-excerpt.txt — relevant existing helper-log excerpt.
- vm-config-readonly-evidence.json — hashes/timestamps for the two .vbox files.

The two existing .codex sandbox files written by the helper and the unknown
ACL effects are documented above; they must not be omitted from side effects.
No password extraction, dependency download, Calibre execution, live ISFDB
request, plugin/library write, commit/push, reset/clean/stash or VM boot occurred.
No intentional firewall rule/profile change, feature enablement, account
creation or additional sandbox setup command occurred. The automatic ACL-refresh
incident prevents any blanket assertion of zero Windows-security changes.

Git diff --check passes without output. Cumulative tracked diff (untracked
reports/tests excluded):

```
 README.md   |  29 +++++
 __init__.py | 407 ++++++++++++++++++++++++++++++++++++++++--------------------
 objects.py  | 365 ++++++++++++++++++++++++++++++++++++++---------------
 3 files changed, 569 insertions(+), 232 deletions(-)
```

Untracked inventory after Phase 9D (25 files; includes earlier phases):

```
docs/CAMOUFOX_FEASIBILITY.md
docs/PHASE8_AUDIT.md
docs/PHASE9A.md
docs/PHASE9B.md
docs/PHASE9C.md
docs/PHASE9D.md
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

Stop after this investigation; no safe-runtime pass is claimed.
