"""GPLv3. ISFDB4 Phase 6B test-only prototype, 2026-11-04.

Uses installed Calibre APIs, not copied implementations. Calibre's API/worker
code is credited to Kovid Goyal and contributors; see UPSTREAM_PROVENANCE.md.
No real browser, worker process, download, external socket or plugin install.
Run only with run_camoufox_feasibility.ps1.
"""
import annotationlib
import asyncio
import hashlib
import inspect
import os
from pathlib import Path
import socket
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock, patch
import zipfile

REPO = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ['ISFDB4_FEASIBILITY_ROOT']).resolve()
assert ROOT.name.startswith('isfdb4-feasibility-')
for key in ('CALIBRE_CONFIG_DIRECTORY', 'CALIBRE_CACHE_DIRECTORY', 'CALIBRE_TEMP_DIR', 'TEMP', 'TMP'):
    assert Path(os.environ[key]).resolve().is_relative_to(ROOT), key
assert 'CALIBRE_METADATA_BROWSER_WORKER' not in os.environ
sys.dont_write_bytecode = True


def audit(event, args):
    if event in ('socket.getaddrinfo', 'subprocess.Popen', 'os.system', 'sqlite3.connect'):
        raise RuntimeError('Feasibility guard blocks ' + event)
    if event in ('socket.connect', 'socket.bind', 'socket.sendto'):
        address = args[-1]
        # Windows asyncio may use loopback sockets for its own wakeup channel.
        # No hostname resolution or non-loopback connection is allowed.
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1'):
            raise RuntimeError('Feasibility guard blocks external network')
    if event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not isinstance(path, int) and not Path(path).resolve().is_relative_to(ROOT):
            raise RuntimeError('Feasibility guard blocks non-disposable write: ' + str(path))
    if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.rename'):
        for path in args[:2] if event == 'os.rename' else args[:1]:
            if not Path(path).resolve().is_relative_to(ROOT):
                raise RuntimeError('Feasibility guard blocks non-disposable mutation')


sys.addaudithook(audit)
from calibre.constants import numeric_version, config_dir, cache_dir, bin_install_dir
from calibre.ebooks.metadata.sources.base import Source
from calibre.web.automate import metadata, camoufox, worker, download_deps
API_OBJECTS = (metadata.run_in_browser, metadata.SessionWorker, metadata.State,
               camoufox.Browser, camoufox.Page.open, camoufox.Page.html,
               worker.start_worker, worker.make_request)
HANDLERS_BEFORE = metadata.HANDLERS
assert numeric_version == (9, 17, 0)
assert sys.version_info[:3] == (3, 14, 8)
assert Path(config_dir).resolve().is_relative_to(ROOT)
assert Path(cache_dir()).resolve().is_relative_to(ROOT)

# Belt-and-braces guards: no real browser/worker or resource acquisition even
# if a test accidentally calls a live entry point. Individual tests supply
# their own fake start_worker/make_request implementations inside these guards.
guards = [
    patch.object(camoufox.Browser, 'launch', AsyncMock(side_effect=RuntimeError('Real browser launch forbidden'))),
    patch.object(metadata, 'start_worker', Mock(side_effect=RuntimeError('Real worker launch forbidden'))),
    patch.object(worker, 'start_worker', Mock(side_effect=RuntimeError('Real worker launch forbidden'))),
    patch.object(download_deps, 'use_camoufox', Mock(side_effect=RuntimeError('Dependency acquisition forbidden'))),
    patch.object(download_deps, 'browserforge_data', Mock(side_effect=RuntimeError('Dependency acquisition forbidden'))),
    patch.object(camoufox, 'use_camoufox', Mock(side_effect=RuntimeError('Dependency acquisition forbidden'))),
    patch.object(camoufox, 'browserforge_data', Mock(side_effect=RuntimeError('Dependency acquisition forbidden'))),
]
for guard in guards:
    guard.start()

INPUTS = ['__init__.py', 'objects.py', 'myglobals.py', 'plugin-import-name-isfdb4.txt']
INPUTS += [p.relative_to(REPO).as_posix() for p in (REPO / 'translations').glob('*') if p.is_file()]
HASHES = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in INPUTS}
ZIP = ROOT / 'checkout-isfdb4.zip'
with zipfile.ZipFile(ZIP, 'w') as archive:
    for name in INPUTS:
        archive.writestr(name, (REPO / name).read_bytes())
from calibre.customize.zipplugin import loader
Plugin = loader.load(str(ZIP))
from calibre_plugins.isfdb4 import objects
from lxml.html import fromstring


class ApiInspection(unittest.TestCase):
    def test_runtime_and_browser_contracts(self):
        print('\nInstalled API signatures:')
        for obj in API_OBJECTS:
            print(obj.__qualname__, inspect.signature(obj, annotation_format=annotationlib.Format.STRING))
        self.assertFalse(Source.uses_camoufox_worker)
        self.assertTrue(inspect.iscoroutinefunction(camoufox.Page.open))
        self.assertTrue(inspect.iscoroutinefunction(camoufox.Page.html))
        self.assertFalse(hasattr(camoufox.Browser, 'clone_browser'))
        self.assertFalse(hasattr(camoufox.Browser, 'open_novisit'))
        self.assertFalse(inspect.signature(camoufox.Browser).parameters['ignore_https_errors'].default)
        self.assertEqual({handler.name for handler in metadata.HANDLERS}, {'amazon', 'google_images'})

    def test_correct_flag_prelaunch_contract(self):
        fake_session = Mock(path='offline-fixture-worker')
        source = Mock(uses_camoufox_worker=False)
        source.is_configured.return_value = True
        with patch('calibre.customize.ui.metadata_plugins', return_value=[source]), patch.object(metadata, 'session_worker', fake_session):
            self.assertEqual(metadata.env_for_metadata_jobs(), {})
            fake_session.launch_in_background.assert_not_called()
            source.uses_camoufox_worker = True
            self.assertEqual(metadata.env_for_metadata_jobs(), {metadata.ENV_VAR: 'offline-fixture-worker'})
            fake_session.launch_in_background.assert_called_once()

    def test_flag_does_not_replace_source_browser(self):
        class FlagOnly(Source):
            name = 'Offline flag inspection'
            uses_camoufox_worker = True
        source = FlagOnly(None)
        browser = source.browser
        self.assertEqual(type(browser).__module__, 'calibre.utils.browser')
        self.assertTrue(callable(browser.clone_browser))
        self.assertTrue(callable(browser.open_novisit))

    def test_dependency_location_is_not_isolated_by_cache_override(self):
        path = Path(bin_install_dir()).resolve()
        print('\nDefault dependency directory (read-only inspection):', path)
        print('Directory exists:', path.is_dir())
        self.assertFalse(path.is_relative_to(ROOT))
        self.assertEqual(download_deps.install_root(), str(path))
        print('Existing executable candidates (not launched):', [str(p) for p in path.glob('camoufox/*/camoufox.exe')])

    def test_external_network_and_write_guards(self):
        with self.assertRaisesRegex(RuntimeError, 'blocks'):
            socket.getaddrinfo('www.isfdb.org', 443)
        with self.assertRaisesRegex(RuntimeError, 'blocks'):
            (REPO / 'must-not-exist-feasibility').open('w')

    def test_windows_worker_uses_named_pipe_address(self):
        self.assertEqual(sys.platform, 'win32')
        address = worker.get_random_socket_path('isfdb4-offline', random_suffix='fixed')
        self.assertTrue(address.startswith('\\\\.\\pipe\\'))
        params = inspect.signature(worker.connect_to_named_pipe, annotation_format=annotationlib.Format.STRING).parameters
        self.assertEqual(params['timeout'].default, 120.0)


@dataclass
class Fixture:
    html: str = ''
    status: int = 200
    redirect: str = ''
    gate: object = None


class FixturePage:
    """Controlled Page-shaped test double; does not execute JavaScript/HTTP.

    controlled_status is a fixture annotation, NOT a Calibre Page API.
    Mapping real browser HTTP responses remains a production design gap.
    """
    def __init__(self, browser):
        self.browser = browser
        self.url = 'about:blank'
        self.closed = False
        self.controlled_status = 0

    async def open(self, url, *, wait='load', timeout=60, referer=''):
        for _ in range(5):
            self.browser.visits.append(url)
            fixture = self.browser.routes[url]
            if fixture.redirect:
                url = fixture.redirect
                continue
            self.url = url
            self.controlled_status = fixture.status
            self.fixture = fixture
            self.browser.entered.set()
            if fixture.gate is not None:
                await fixture.gate.wait()
            await asyncio.sleep(0)
            return
        raise ValueError('Fixture redirect limit exceeded')

    async def html(self):
        return self.fixture.html

    async def close(self):
        self.closed = True


class FixtureBrowser:
    def __init__(self, routes):
        self.routes = routes
        self.pages = []
        self.visits = []
        self.entered = asyncio.Event()
        self.peak = 0

    async def new_page(self, url='', *, wait='load', timeout=60):
        page = FixturePage(self)
        self.pages.append(page)
        self.peak = max(self.peak, sum(not p.closed for p in self.pages))
        return page


class FixtureHandler(metadata.SourceHandler):
    """Test-only adapter supplied to a LOCAL State, never the global registry."""
    name = 'isfdb4_fixture'

    async def handle(self, action, args, deadline):
        if action != 'fetch':
            raise ValueError('Unknown fixture action: ' + action)
        async with self.state.tab_pool.slots(1):
            page = await self.browser.new_page(timeout=deadline.remaining())
            try:
                await page.open(args['url'], timeout=deadline.remaining())
                html = await page.html()
                if page.controlled_status >= 400:
                    return dict(metadata.error_result('http', 'Controlled HTTP error'), status=page.controlled_status, url=page.url)
                if not html.strip():
                    return dict(metadata.error_result('empty', 'Controlled empty response'), url=page.url)
                return {'url': page.url, 'html': html}
            finally:
                await page.close()


class AsyncContracts(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.browser = FixtureBrowser({'fixture://title': Fixture((REPO / 'tests/fixtures/title.html').read_text())})
        self.state = metadata.State(self.browser, handlers=[FixtureHandler], max_detail_tabs=2)
        self.tasks = []

    def request(self, url='fixture://title', source=FixtureHandler.name, seconds=5):
        return {'source': source, 'action': 'fetch', 'args': {'url': url}, 'deadline': time.time() + seconds}

    def task(self, request):
        task = asyncio.create_task(self.state.handle(request))
        self.tasks.append(task)
        return task

    async def asyncTearDown(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        reaper = self.state.reaper
        self.state.stop_reaper()
        if reaper is not None:
            await asyncio.gather(reaper, return_exceptions=True)
        self.assertEqual(self.state.tab_pool.free, self.state.tab_pool.size)
        self.assertTrue(all(page.closed for page in self.browser.pages))
        self.assertTrue(all(not handler.queue.locked() for handler in self.state.handlers.values()))

    async def test_fixture_fetch_existing_title_parser(self):
        result = await self.state.handle(self.request())
        with patch.object(objects.ISFDBObject, 'root_from_url', return_value=(objects.Title.url_from_id('101'), fromstring(result['html']))):
            plugin = Plugin(str(ZIP))
            data = objects.Title.from_url(None, objects.Title.url_from_id('101'), 90, Mock(), plugin.prefs)
        self.assertEqual(data['title'], 'The Offline Star')
        self.assertEqual(data['authors'], ['Ada Example'])

    async def test_redirect_and_unicode_dom_are_preserved(self):
        self.browser.routes['fixture://redirect'] = Fixture(redirect='fixture://unicode')
        self.browser.routes['fixture://unicode'] = Fixture('<html><p>Caf\u00e9 \u5bae\u5d0e</p></html>')
        result = await self.state.handle(self.request('fixture://redirect'))
        self.assertEqual(result['url'], 'fixture://unicode')
        self.assertEqual(fromstring(result['html']).xpath('//p/text()'), ['Caf\u00e9 \u5bae\u5d0e'])
        self.assertEqual(self.browser.visits, ['fixture://redirect', 'fixture://unicode'])

    async def test_unicode_dom_passes_through_existing_title_parser(self):
        html = (REPO / 'tests/fixtures/title.html').read_text().replace('The Offline Star', 'Caf\u00e9 \u5bae\u5d0e').replace('Ada Example', 'Jos\u00e9 Example')
        self.browser.routes['fixture://unicode-title'] = Fixture(html)
        result = await self.state.handle(self.request('fixture://unicode-title'))
        with patch.object(objects.ISFDBObject, 'root_from_url', return_value=(objects.Title.url_from_id('101'), fromstring(result['html']))):
            plugin = Plugin(str(ZIP))
            data = objects.Title.from_url(None, objects.Title.url_from_id('101'), 90, Mock(), plugin.prefs)
        self.assertEqual(data['title'], 'Caf\u00e9 \u5bae\u5d0e')
        self.assertEqual(data['authors'], ['Jos\u00e9 Example'])

    async def test_controlled_http_errors_and_empty_body(self):
        for status in (403, 404, 429, 500):
            self.browser.routes['fixture://error'] = Fixture('Denied', status=status)
            result = await self.state.handle(self.request('fixture://error'))
            self.assertEqual((result['kind'], result['status']), ('http', status))
        self.browser.routes['fixture://empty'] = Fixture(' \n')
        self.assertEqual((await self.state.handle(self.request('fixture://empty')))['kind'], 'empty')

    async def test_real_default_dispatch_has_no_isfdb_handler(self):
        state = metadata.State(self.browser)
        with self.assertRaises(KeyError):
            await state.handle(self.request(source='ISFDB4'))
        self.assertEqual(self.browser.visits, [])

    async def test_same_source_concurrent_requests_are_serialized(self):
        tasks = [self.task(self.request()) for _ in range(6)]
        results = await asyncio.gather(*tasks)
        self.assertEqual(len(results), 6)
        self.assertEqual(self.browser.peak, 1)

    async def test_different_sources_can_share_bounded_tab_pool(self):
        class OtherFixture(FixtureHandler):
            name = 'other_fixture'
        self.state = metadata.State(self.browser, handlers=[FixtureHandler, OtherFixture], max_detail_tabs=2)
        gate = asyncio.Event()
        self.browser.routes['fixture://blocked'] = Fixture('<p>done</p>', gate=gate)
        tasks = [self.task(self.request('fixture://blocked', source=name)) for name in (FixtureHandler.name, OtherFixture.name)]
        for _ in range(20):
            if self.browser.peak == 2:
                break
            await asyncio.sleep(0)
        self.assertEqual(self.browser.peak, 2)
        gate.set()
        await asyncio.gather(*tasks)

    async def test_running_request_deadline_returns_structured_timeout(self):
        self.browser.routes['fixture://blocked'] = Fixture('never', gate=asyncio.Event())
        result = await self.state.handle(self.request('fixture://blocked', seconds=0.02))
        self.assertEqual(result['kind'], 'timeout')

    async def test_cancel_running_request_releases_fixture_page_and_slot(self):
        self.browser.routes['fixture://blocked'] = Fixture('never', gate=asyncio.Event())
        task = self.task(self.request('fixture://blocked'))
        await self.browser.entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_queued_expired_request_waits_until_lock_is_released(self):
        gate = asyncio.Event()
        self.browser.routes['fixture://blocked'] = Fixture('<p>done</p>', gate=gate)
        first = self.task(self.request('fixture://blocked'))
        await self.browser.entered.wait()
        second = self.task(self.request(seconds=-1))
        await asyncio.sleep(0)
        # Actual Calibre State acquires the per-source lock BEFORE checking
        # deadline expiry. It cannot promptly time out while queued here.
        self.assertFalse(second.done())
        gate.set()
        await first
        self.assertEqual((await second)['kind'], 'timeout')

    async def test_cancel_queued_request_does_not_leak_lock(self):
        gate = asyncio.Event()
        self.browser.routes['fixture://blocked'] = Fixture('<p>done</p>', gate=gate)
        first = self.task(self.request('fixture://blocked'))
        await self.browser.entered.wait()
        second = self.task(self.request())
        await asyncio.sleep(0)
        second.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await second
        gate.set()
        await first

    async def test_reaper_starts_and_stops_without_remaining_task(self):
        self.state.start_reaper()
        task = self.state.reaper
        self.state.stop_reaper()
        await asyncio.gather(task, return_exceptions=True)
        self.assertTrue(task.cancelled())


class ClientContracts(unittest.TestCase):
    def test_session_worker_startup_is_thread_safe_and_shutdown_is_idempotent(self):
        session = metadata.SessionWorker({'warmup': False})
        close = Mock(return_value=0)
        with patch.object(metadata, 'start_worker', return_value=('offline-worker', close)) as start:
            with ThreadPoolExecutor(max_workers=6) as pool:
                paths = list(pool.map(lambda unused: session.ensure_started(), range(12)))
            self.assertEqual(set(paths), {'offline-worker'})
            start.assert_called_once()
            session.shutdown()
            session.shutdown()
        close.assert_called_once()
        self.assertEqual(session.path, '')

    def test_run_in_browser_transmits_request_and_deadline(self):
        session = metadata.SessionWorker()
        close = Mock(return_value=0)
        try:
            with patch.object(metadata, 'session_worker', session), patch.object(metadata, 'start_worker', return_value=('offline-worker', close)), patch.object(metadata, 'make_request', return_value=worker.Response(response={'html': '<p>fixture</p>'})) as request:
                result = metadata.run_in_browser('isfdb4_fixture', 'fetch', {'url': 'fixture://title'}, timeout=90)
            self.assertEqual(result['html'], '<p>fixture</p>')
            payload = request.call_args.args[1]
            self.assertEqual((payload['source'], payload['action']), ('isfdb4_fixture', 'fetch'))
            self.assertGreater(payload['deadline'], time.time())
        finally:
            session.shutdown()
        close.assert_called_once()

    def test_worker_exception_is_wrapped_as_browser_failed(self):
        session = metadata.SessionWorker()
        try:
            with patch.object(metadata, 'session_worker', session), patch.object(metadata, 'start_worker', return_value=('offline-worker', Mock())), patch.object(metadata, 'make_request', return_value=worker.Response(exception='Missing browser resource', traceback='controlled worker traceback')):
                with self.assertRaisesRegex(metadata.BrowserFailed, 'Missing browser resource') as caught:
                    metadata.run_in_browser('isfdb4_fixture', 'fetch', {})
                self.assertIn('controlled worker traceback', str(caught.exception))
        finally:
            session.shutdown()

    def test_startup_failure_can_escape_without_browser_failed_conversion(self):
        session = metadata.SessionWorker()
        with patch.object(metadata, 'session_worker', session), patch.object(metadata, 'start_worker', side_effect=FileNotFoundError('controlled startup failure')):
            with self.assertRaises(FileNotFoundError):
                metadata.run_in_browser('isfdb4_fixture', 'fetch', {})
        self.assertEqual(session.path, '')

    def test_local_worker_connection_failure_has_bounded_restart(self):
        session = metadata.SessionWorker()
        close = Mock()
        try:
            with patch.object(metadata, 'session_worker', session), patch.object(metadata, 'start_worker', return_value=('offline-worker', close)) as start, patch.object(metadata, 'make_request', side_effect=OSError('controlled disconnect')) as request:
                with self.assertRaises(metadata.BrowserFailed):
                    metadata.run_in_browser('isfdb4_fixture', 'fetch', {})
            self.assertEqual((start.call_count, request.call_count), (2, 2))
        finally:
            session.shutdown()
        # Forgetting an unreachable worker drops its callback. No real process
        # was created; cleanup of a still-live unreachable process is unverified.

    def test_client_api_has_no_abort_parameter(self):
        params = inspect.signature(metadata.run_in_browser, annotation_format=annotationlib.Format.STRING).parameters
        self.assertNotIn('abort', params)
        self.assertNotIn('cancel', params)


if __name__ == '__main__':
    print('Target Calibre:', numeric_version, 'Python:', sys.version, flush=True)
    print('Installed module:', metadata.__file__, flush=True)
    print('Browser process/worker startup and downloads are blocked.', flush=True)
    try:
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                                   for cls in (ApiInspection, AsyncContracts, ClientContracts))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert all(hashlib.sha256((REPO / name).read_bytes()).hexdigest() == digest for name, digest in HASHES.items())
        assert metadata.HANDLERS is HANDLERS_BEFORE
        print('Production hashes unchanged. Zero real browser/worker processes were launched.')
        print('SUMMARY:', result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
              'passed;', len(result.failures), 'failed;', len(result.errors), 'errors;', len(result.skipped), 'skipped')
    finally:
        for guard in reversed(guards):
            guard.stop()
    raise SystemExit(not result.wasSuccessful())
