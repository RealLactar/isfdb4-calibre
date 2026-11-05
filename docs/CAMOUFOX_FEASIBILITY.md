# Phase 6B: Calibre Camoufox feasibility

Date: 2026-11-04. Target: Windows 10 Pro, Calibre 9.17.0, embedded
Python 3.14.8 (MSC v.1950, 64-bit AMD64).

**Recommendation: NO-GO for production integration on the available evidence.**
An isolated fixture prototype can use installed Calibre dispatch APIs without
installation or application changes. No real browser or child worker process
was launched, and no browser-network benefit has been demonstrated. This is
not a production adapter and does not enable Camoufox in ISFDB4.

## Reproducing the offline evaluation

From the repository root:

```powershell
.\tests\run_camoufox_feasibility.ps1
.\tests\run.ps1
```

The first command executes tests/camoufox_feasibility.py under the installed
calibre-debug executable, with disposable configuration/cache/temp paths. It
clears an inherited CALIBRE_METADATA_BROWSER_WORKER endpoint and development
source override, restores the parent environment, and removes its generated
temporary directory afterward. It builds a disposable checkout ZIP and uses
Calibre's loader without installing/registering it.

The prototype blocks Python external connections, DNS resolution, subprocess
launch, SQLite connections, and ordinary writes outside the disposable root.
Loopback sockets are allowed only for asyncio's local control facilities;
fixture fetching itself uses no HTTP server or socket. Real browser launch,
worker startup and dependency-acquisition entry points are additionally mocked
to fail. No dependency installer or binary updater is called. These guards are
not an OS sandbox for a running native browser: no native browser is launched.

The test-only FixtureHandler is supplied to an isolated metadata.State object.
It is not added to metadata.HANDLERS or to installed plugin state. Browser/Page
objects, HTTP status/redirect responses and process creation are test doubles.
The existing ordinary regression runner and its stricter network guard remain
unchanged.

## Evidence categories

| Requirement | Executable evidence | What remains unverified |
| --- | --- | --- |
| Flag behavior | Actual env_for_metadata_jobs uses uses_camoufox_worker to request prelaunch; Source.browser still returns mechanize even with the correct flag. | Successful shared-browser launch for ISFDB. |
| Default dispatch | Actual metadata.State rejects source ISFDB4; installed default handlers are amazon and google_images. | A supported third-party registration path in the shared process. |
| Fixture fetching | A custom, test-only handler dispatches local HTML through actual State, SourceHandler, Deadline and TabPool code. | Real Camoufox HTTP, JavaScript or response-body acquisition. |
| Redirects | FixturePage follows a controlled redirect and passes the final URL through. | Actual browser redirect/cookie/response behavior. |
| Unicode/parsers | Unicode fixture DOM including accented and Japanese text reaches the existing Title.from_url parser through a mocked fetch boundary intact. | Correct encoding and HTTP status extraction from a real browser response. |
| HTTP/empty errors | A controlled handler produces structured 403/404/429/500 and empty-body results. | Real Page HTTP-error mapping. controlled_status is a fixture annotation, not a Calibre Page property. |
| Worker errors | Actual run_in_browser wraps an injected worker exception/traceback as BrowserFailed; injected startup FileNotFoundError escapes before that conversion. | Real executable/resource/startup failures. |
| Concurrency | Actual per-source locks serialize six requests; separate sources share a bounded two-tab fixture pool concurrently. Threaded SessionWorker.ensure_started starts its fake worker once. | Native browser/IPC throughput, memory use and multiple Python worker-thread interaction. |
| Cancellation | Cancelling running/queued async fixture tasks releases pages, slots and locks. Actual reaper task starts/stops. | End-to-end abort of synchronous client calls and a native browser process. |
| Termination | Fake close callback is called once despite repeated SessionWorker.shutdown; fixture tasks/tabs/locks are cleaned. | Windows child-process reaping, browser-profile cleanup and orphan prevention after crashes. |

The browser/worker processes are deliberately absent, so zero new browser/worker
processes can be orphaned by this prototype. This does not establish real
process-cleanup reliability.

## Installed API contracts actually inspected

The imported metadata module resolves to the installed frozen Calibre library
under C:/Program Files/Calibre2/app/bin/python-lib.bypy.frozen. API inspection
was performed inside the target runtime, not solely against downloaded source.

- run_in_browser(source, action, args, timeout=120.0) returns a dictionary and
  has no abort/cancel argument.
- SessionWorker(input_data=None) exposes ensure_started, forget,
  launch_in_background and shutdown. ensure_started uses a lock; shutdown
  invokes the close callback and resets the endpoint.
- State(browser, handlers=HANDLERS, max_detail_tabs=10) accepts local test
  handlers. Its existence is not a public installed-plugin registry contract.
- Browser is asynchronous; it has no clone_browser or open_novisit method.
- Page.open(url, wait='load', timeout=60.0, referer='') is async and returns
  None. Page.html() is async and returns Unicode str.
- Browser accepts an explicit Install and defaults to launch_timeout=180.0,
  ignore_https_errors=False. These are API defaults, not measured startup
  durations or authorization to alter ISFDB4 TLS policy.
- start_worker returns an endpoint and close callback. make_request returns
  Response(response, exception, traceback). Those calls were mocked for I/O.
- Windows get_random_socket_path produces a named-pipe address; the installed
  connect_to_named_pipe signature has a 120-second timeout. Actual named-pipe
  creation/transport was not exercised.

Python 3.14 reflection of forward annotations can raise NameError when an
annotation references a TYPE_CHECKING-only name. The probe uses
annotationlib.Format.STRING; it does not change Calibre annotations or code.

The inspected shared-worker entry points can use Calibre's live-updated server
module. Those entry points were not started here: State/client methods were
tested in the installed parent runtime with process I/O mocked. A real-worker
evaluation must control live-update/module acquisition as well as browser/data
downloads; its server code cannot automatically be assumed to match this
installed snapshot. No live-update operation was invoked by the prototype.

Pinned source references, reviewed earlier and used without external access
in this phase:

- [Source flag/browser](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/ebooks/metadata/sources/base.py#L238).
- [State dispatch and handler registry](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/metadata.py#L744).
- [SessionWorker lifecycle](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/metadata.py#L891).
- [Worker process/IPC](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/worker.py#L299).
- [Browser/Page](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/camoufox.py#L2785).
- [Resource installer](https://github.com/kovidgoyal/calibre/blob/v9.17.0/src/calibre/web/automate/download_deps.py#L209).

## Lifecycle, concurrency and cancellation risks

The inspected implementation runs a session-owned worker and browser, with
per-source search tabs and a bounded pool of detail tabs. Jobs may inherit an
existing worker endpoint. The prototype clears that environment variable so
it cannot accidentally connect to the user's session.

The real State.handle acquires the source lock before checking the request
deadline. A test with an already-expired queued request confirms that it stays
pending until the active request releases the lock. Running handlers are
bounded by asyncio.timeout, but queued expiry is not prompt cancellation.
The short fixture deadlines are test controls, not changes to the production
90-second minimum socket timeout.

The synchronous run_in_browser/make_request path has no abort event parameter.
Closing/cancelling a caller thread is not demonstrated to cancel server work.
A native implementation needs a deliberate abort/lifecycle design rather than
assuming ISFDB4's existing thread abort checks propagate into the browser.

Actual run_in_browser retries connection failure for its locally owned worker
at most twice. This is new retry semantics relative to ISFDB4. The test verifies
the dispatcher's retry count with fake callbacks; it does not introduce those
retries into production. SessionWorker.forget drops the unreachable worker's
close callback; whether a still-live unreachable native worker is safely reaped
has not been tested. The owner-close callback in the inspected worker code
closes stdin and waits for the process; real shutdown latency is unmeasured.

Exceptions crossing the worker boundary are represented by strings and a
serialized traceback, then potentially BrowserFailed. Original HTTP exception
object identity/traceback cannot simply be carried across IPC as in Phase 6A.
Some startup failures can escape before BrowserFailed wrapping. Logging and
error translation therefore need an explicit reviewed adapter contract.

## Executables, dependencies and resource costs

Read-only inspection found this pre-existing executable candidate:

    C:/Users/apt/AppData/Local/calibre-dbin/camoufox/156.0.1-beta.36/camoufox.exe

It was not launched, modified, copied or used to trigger installation. Its
presence does not establish complete resources or runtime compatibility.

Default dependencies use %LOCALAPPDATA%/calibre-dbin independently of redirected
config/cache directories. Browserforge/fingerprint data and fonts/resources
may be acquired or updated on demand. Supplying Install for a browser alone
does not prove every other resource is available offline. Calibre's default
metadata initialization can also warm the browser on external sites. Those
paths must remain disabled/contained in any future offline real-engine test.

The native browser is expected to cost more process memory/CPU/startup work
than urllib/mechanize. No browser CPU, RAM, cold/warm startup, download size or
real cleanup measurements were collected. The approximately 0.12-second test
duration measures fixture tests only. Defaults of 180 seconds for launch and
120 seconds for worker requests are budgets, not performance measurements;
startup/queue costs could consume a request deadline before useful work.

Windows-specific named-pipe and browser process/profile cleanup code is present,
and the Python API tests pass on Windows 10. The particular executable's OS,
graphics/font, security-product and process-tree behavior remain unverified.

## Comparison and integration approaches

ISFDB4's primary ISFDB page transport is urllib with fixed headers and the
90-second floor. Mechanize remains the inherited clonable browser used by
other paths, including cover/external-page operations. Neither executes page
JavaScript. Camoufox may help sites requiring browser execution, but no such
benefit for ISFDB4 has been demonstrated by this offline evaluation.

| Approach | Assessment |
| --- | --- |
| Set the Source flag only | NO-GO. It does not route ISFDB requests and the shared worker lacks an ISFDB handler. |
| Obtain a supported shared-worker ISFDB handler/extension | Potential future approach, requiring an upstream-supported deployment contract. The private local State handler constructor is insufficient as a plugin registration promise. |
| Plugin-owned isolated worker using Browser/Page | Technically plausible. Requires lifecycle, offline resources, bounded thread/async bridge, cancellation, proxy/cookie/header ownership, error mapping and compatibility policy. Not implemented here. |
| Replace mechanize with a Camoufox object | NO-GO. Missing clone/open compatibility and different asynchronous semantics. |
| Keep current production transport | Recommended now. Retains tested behavior and avoids adding unverified dependencies or recovery semantics. |

A future browser path must accept Unicode DOM directly and preserve final URL
and metadata semantics. It must also decide how cover/external-page fetches
share any cookies/session, and how TLS/header policies are preserved. The
prototype does not resolve or silently change these contracts.

## Attribution, safeguards and conclusion

The prototype calls installed Calibre implementations rather than copying
them. Calibre Camoufox/metadata API work is credited to Kovid Goyal and
contributors, including introducing commits 32a29185a669ec2a4f4e1a00ba58d24fa8859f10
and 21014ee93c6014e37461b7c77923665bd4156924. ISFDB3 b8ff4a0 by bertholdm/Michael
Detambel is the upstream review motivation; its defective integration code
was not copied. The fixture handler/driver is ISFDB4 test scaffolding, not an
original ISFDB4 browser engine. See [provenance](UPSTREAM_PROVENANCE.md) and
the unchanged GPLv3 LICENSE. Existing notices remain applicable.

Results: feasibility suite 24 passed, no failures/errors/skips/expected failures;
ordinary suite 87 passed, no failures/errors/skips, one unchanged advanced-search
expected failure. Both ran in Calibre 9.17.0 / embedded Python 3.14.8.

Production code and existing regression scripts were not modified in Phase 6B.
No external network, live ISFDB, real worker/browser launch, binary download,
installation, application-directory writes, live settings/plugin/library
changes, TLS/timeout/header/retry changes, commits or pushes occurred. Only
repository test/research artifacts and disposable temporary files were used.

Production integration is NO-GO until a supported routing approach, complete
offline resource isolation, end-to-end cancellation/error contracts and
real-engine Windows startup/network/cleanup behavior are established under
separate authorization. Current benefit remains theoretical. No production
integration phase is begun by this report.
