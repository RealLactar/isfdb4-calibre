"""Run only via run.ps1: Calibre starts with disposable config/cache/temp paths."""
import ast
import hashlib
import inspect
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import Mock, patch
from queue import Queue
from threading import Event
from urllib.error import HTTPError, URLError
import zipfile

REPO = Path(__file__).resolve().parents[1]
SCRATCH = Path(os.environ['ISFDB4_TEST_ROOT']).resolve()
assert SCRATCH.name.startswith('isfdb4-tests-') and SCRATCH != REPO
for key in ('CALIBRE_CONFIG_DIRECTORY', 'CALIBRE_CACHE_DIRECTORY', 'CALIBRE_TEMP_DIR', 'TEMP', 'TMP'):
    assert Path(os.environ[key]).resolve().is_relative_to(SCRATCH), key
sys.dont_write_bytecode = True

def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'socket.sendto', 'socket.bind', 'subprocess.Popen', 'os.system', 'sqlite3.connect'):
        raise RuntimeError('Offline harness forbids ' + event)
    if event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not isinstance(path, int) and not Path(path).resolve().is_relative_to(SCRATCH):
            raise RuntimeError('Write outside disposable test root: ' + str(path))
    if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.rename'):
        for path in args[:2] if event == 'os.rename' else args[:1]:
            if not Path(path).resolve().is_relative_to(SCRATCH):
                raise RuntimeError('Mutation outside disposable test root: ' + str(path))

sys.addaudithook(audit)
from calibre.constants import numeric_version, config_dir, cache_dir
assert numeric_version == (9, 17, 0), numeric_version
assert Path(config_dir).resolve() == Path(os.environ['CALIBRE_CONFIG_DIRECTORY']).resolve()
assert Path(cache_dir()).resolve().is_relative_to(SCRATCH)
print('Calibre:', '.'.join(map(str, numeric_version)), flush=True)
print('Embedded Python:', sys.version, flush=True)
print('Executable:', sys.executable, flush=True)
print('Repository:', REPO, '\nDisposable root:', SCRATCH, flush=True)

FILES = ['__init__.py', 'objects.py', 'myglobals.py', 'plugin-import-name-isfdb4.txt']
FILES += [p.relative_to(REPO).as_posix() for p in sorted((REPO / 'translations').glob('*')) if p.is_file()]
HASHES = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in FILES}
ZIP = SCRATCH / 'checkout-isfdb4.zip'
with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in FILES:
        z.writestr(name, (REPO / name).read_bytes())
from calibre.customize.zipplugin import loader
Plugin = loader.load(str(ZIP))
import calibre_plugins.isfdb4 as plugin_module
import calibre_plugins.isfdb4.objects as objects
from calibre.ebooks.metadata.book.base import Metadata
from lxml.html import fromstring
sys.path.insert(0, str(REPO / 'tests'))
from author_edges import AuthorEdges
from phase4_cases import Phase4Cases
from http_diagnostics import HttpDiagnostics
from unicode_correctness import UnicodeCorrectness
from metadata_correctness import MetadataCorrectness
from reliability import Reliability

class Regression(Reliability, MetadataCorrectness, UnicodeCorrectness, HttpDiagnostics, Phase4Cases, AuthorEdges, unittest.TestCase):
    def setUp(self):
        # Fresh defaults for each case, without sharing persisted test preferences.
        pref_file = Path(config_dir) / 'metadata_sources' / 'ISFDB4.json'
        if pref_file.exists():
            pref_file.unlink()
        self.plugin = Plugin(str(ZIP))
        self.plugin.initialize()
        self.log = Mock()
        self.prefs = self.plugin.prefs
        self.prefs['log_level'] = 'DEBUG'
        self.prefs['exact_search'] = False

    def fixture(self, name):
        return (REPO / 'tests' / 'fixtures' / name).read_bytes()

    def response(self, data, url='https://www.isfdb.org/cgi-bin/title.cgi?101'):
        return Mock(read=Mock(return_value=data), geturl=Mock(return_value=url))

    def identify(self, **kwargs):
        queue = Queue()
        self.plugin.identify(self.log, queue, Event(), **kwargs)
        return list(queue.queue)

    def test_checkout_zip_identity(self):
        self.assertEqual(Path(self.plugin.plugin_path), ZIP)
        self.assertIn(str(ZIP), plugin_module.__file__)
        self.assertIn(str(ZIP), objects.__file__)
        with zipfile.ZipFile(ZIP) as z:
            for name, digest in HASHES.items():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest)
                self.assertEqual(hashlib.sha256((REPO / name).read_bytes()).hexdigest(), digest)

    def test_loading_and_initialization(self):
        self.assertEqual(self.plugin.name, 'ISFDB4')
        self.assertIn('identify', self.plugin.capabilities)
        self.assertIsInstance(Metadata('Test', ['Author']), Metadata)
        self.assertTrue(callable(plugin_module.load_translations))

    def test_configuration_isolation(self):
        self.prefs['phase1_isolation_sentinel'] = 'disposable only'
        self.assertTrue(Path(self.prefs.file_path).resolve().is_relative_to(SCRATCH))
        self.assertIn('phase1_isolation_sentinel', Path(self.prefs.file_path).read_text())
        self.assertFalse((Path(config_dir) / 'plugins' / 'ISFDB4.zip').exists())

    def test_network_guard(self):
        with self.assertRaisesRegex(RuntimeError, 'Offline harness'):
            socket.getaddrinfo('www.isfdb.org', 443)

    def test_write_guard(self):
        with self.assertRaisesRegex(RuntimeError, 'Write outside'):
            open(REPO / 'tests' / 'must-never-exist', 'w')

    def test_headers_and_timeout_floor(self):
        for requested, effective in [(5, 90), (30, 90), (120, 120)]:
            with self.subTest(timeout=requested), patch.object(objects, 'urlopen', return_value=self.response(self.fixture('title.html'))) as fetch:
                location, root = objects.fetch_isfdb_url(objects.Title.url_from_id('101'), requested, self.log, self.prefs)
                request = fetch.call_args.args[0]
                self.assertEqual(request.get_method(), 'GET')
                self.assertEqual(dict((k.lower(), v) for k, v in request.header_items()),
                                 dict((k.lower(), v) for k, v in objects.ISFDB_HTTP_HEADERS.items()))
                self.assertEqual(fetch.call_args.kwargs['timeout'], effective)
                self.assertEqual(root.xpath('//b')[0].text, 'Title:')

    def test_http_and_network_errors(self):
        errors = [HTTPError('https://www.isfdb.org/', c, 'synthetic', {}, None) for c in (403, 404, 500)]
        errors += [URLError('offline connection failure'), TimeoutError('synthetic timeout')]
        for error in errors:
            with self.subTest(error=repr(error)), patch.object(objects, 'urlopen', side_effect=error) as fetch:
                with self.assertRaises(type(error)):
                    objects.fetch_isfdb_url(objects.Title.url_from_id('101'), 30, self.log, self.prefs)
                self.assertEqual(fetch.call_count, 1)

    def test_title_metadata_and_public_queue(self):
        with patch.object(objects, 'urlopen', return_value=self.response(self.fixture('title.html'))):
            results = self.identify(identifiers={'isfdb-title': '101'})
        self.assertEqual(len(results), 1)
        mi = results[0]
        self.assertIsInstance(mi, Metadata)
        self.assertEqual(mi.title, 'The Offline Star')
        self.assertEqual(mi.authors, ['Ada Example'])
        self.assertEqual(mi.identifiers['isfdb-title'], '101')
        self.assertEqual(mi.pubdate.year, 1965)
        self.assertEqual(mi.language, 'eng')
        self.assertIn('Novel', mi.tags)

    def test_publication_metadata_parser(self):
        with patch.object(objects, 'urlopen', return_value=self.response(self.fixture('publication.html'))):
            data = objects.Publication.from_url(self.plugin.browser, objects.Publication.url_from_id('202'), 30, self.log, self.prefs)
        self.assertEqual(data['title'], 'The Offline Star')
        self.assertEqual(data['authors'], ['Ada Example'])
        self.assertEqual(data['publisher'], 'Example Press')
        self.assertEqual(data['pubdate'].year, 1970)
        self.assertEqual(data['isfdb'], '202')

    def test_publication_id_routing_and_queue(self):
        data = {'isfdb': '202', 'isfdb-title': '101', 'title': 'The Offline Star', 'authors': ['Ada Example'], 'tags': ['novel'], 'publisher': 'Example Press'}
        with patch.object(objects.Publication, 'from_url', return_value=data) as publication, patch.object(objects.Title, 'from_url', return_value={'publications': ['202']}) as title:
            results = self.identify(identifiers={'isfdb': '202', 'isfdb-title': '101'})
        self.assertEqual(publication.call_args.args[1], objects.Publication.url_from_id('202'))
        self.assertEqual(title.call_args.args[1], objects.Title.url_from_id('101'))
        self.assertEqual(results[0].identifiers['isfdb'], '202')

    def test_publication_id_end_to_end_fixture_parsing(self):
        def respond(request, **kwargs):
            url = request.full_url
            if url == objects.Publication.url_from_id('202'):
                return self.response(self.fixture('publication.html'), url)
            if url == objects.Title.url_from_id('101'):
                return self.response(self.fixture('title.html'), url)
            self.fail('Unexpected request: ' + url)
        with patch.object(objects, 'urlopen', side_effect=respond) as fetch:
            results = self.identify(identifiers={'isfdb': '202', 'isfdb-title': '101'})
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(len(results), 1)
        mi = results[0]
        self.assertEqual(mi.identifiers['isfdb'], '202')
        self.assertEqual(mi.identifiers['isfdb-title'], '101')
        self.assertEqual(mi.publisher, 'Example Press')
        self.assertEqual(mi.pubdate.year, 1970)
        self.assertTrue(mi.comments)

    def test_title_author_search_orchestration(self):
        self.prefs['search_publications'] = False
        self.prefs['search_titles'] = True
        stub = {'title': 'The Offline Star', 'url': objects.Title.url_from_id('101'), 'date': '1965'}
        with patch.object(objects.TitleList, 'from_url', return_value=[stub]) as search, patch.object(objects.TitleList, 'from_author') as author_search, patch.object(objects, 'urlopen', return_value=self.response(self.fixture('title.html'))):
            results = self.identify(title='The Offline Star', authors=['Example, Ada'])
        author_search.assert_not_called()
        query = search.call_args.args[1]
        self.assertIn('TERM_1=The+Offline+Star', query)
        self.assertIn('TERM_2=Ada+Example', query)
        self.assertEqual(len(results), 1)

    def test_search_result_stub_parsing(self):
        root = fromstring(self.fixture('search.html'))
        row = root.xpath('//tr[td]')[0]
        data = objects.Title.stub_from_search(row, self.log, self.prefs)
        self.assertEqual(data['title'], 'The Offline Star')
        self.assertEqual(data['authors'], ['Ada Example'])

    @unittest.expectedFailure
    def test_known_advanced_search_language_column(self):
        # Existing code reads both title and language from td[5]. No real-world
        # layout is asserted here: this demonstrates the internal contradiction.
        with patch.object(objects, 'urlopen', return_value=self.response(self.fixture('search.html'))):
            rows = objects.TitleList.from_url(self.plugin.browser, objects.TitleList.url_from_title_and_author('The Offline Star', 'Ada Example', self.log, self.prefs), 30, self.log, self.prefs)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['title'], 'The Offline Star')

    def test_simple_fallback_parsing_preserves_preferences(self):
        before = dict(self.prefs)
        responses = [self.response(self.fixture('restricted_search.html')), self.response(self.fixture('simple_search.html'))]
        query = objects.TitleList.url_from_title_and_author('The Offline Star', 'Ada Example', self.log, self.prefs)
        with patch.object(objects, 'urlopen', side_effect=responses) as fetch:
            rows = objects.TitleList.from_url(self.plugin.browser, query, 30, self.log, self.prefs)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['authors'], ['Ada Example'])
        self.assertIn('/se.cgi?arg=', fetch.call_args.args[0].full_url)
        self.assertEqual(dict(self.prefs), before)

    def test_title_author_lookup_end_to_end_offline(self):
        self.prefs['search_publications'] = False
        self.prefs['search_titles'] = True
        def respond(request, **kwargs):
            url = request.full_url
            if '/adv_search_results.cgi?' in url:
                return self.response(self.fixture('restricted_search.html'), url)
            if '/se.cgi?' in url:
                return self.response(self.fixture('simple_search.html'), url)
            if url == objects.Title.url_from_id('101'):
                return self.response(self.fixture('title.html'), url)
            self.fail('Unexpected request: ' + url)
        with patch.object(objects, 'urlopen', side_effect=respond) as fetch:
            results = self.identify(title='The Offline Star', authors=['Ada Example'])
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].authors, ['Ada Example'])

    def test_http_403_does_not_trigger_html_fallback(self):
        query = objects.TitleList.url_from_title_and_author('The Offline Star', 'Ada Example', self.log, self.prefs)
        with patch.object(objects, 'urlopen', side_effect=HTTPError(query, 403, 'synthetic', {}, None)) as fetch:
            with self.assertRaises(HTTPError):
                objects.TitleList.from_url(self.plugin.browser, query, 30, self.log, self.prefs)
        self.assertEqual(fetch.call_count, 1)

    def test_pre_set_abort_avoids_search(self):
        abort = Event()
        abort.set()
        queue = Queue()
        with patch.object(objects, 'urlopen') as fetch:
            self.plugin.identify(self.log, queue, abort, title='The Offline Star', authors=['Ada Example'])
        fetch.assert_not_called()
        self.assertTrue(queue.empty())

    def test_initialization_migration_is_confined_to_test_config(self):
        self.prefs['ai_api_key'] = 'synthetic-not-a-real-key'
        other = Plugin(str(ZIP))
        self.assertNotIn('ai_api_key', other.prefs)
        self.assertTrue(Path(other.prefs.file_path).resolve().is_relative_to(SCRATCH))

    def test_publication_search_result_parsing(self):
        html = b'<div id="main"><table><tr><td><a href="https://www.isfdb.org/cgi-bin/pl.cgi?202">The Offline Star</a></td><td>1970</td><td><a>Ada Example</a></td></tr></table></div>'
        with patch.object(objects, 'urlopen', return_value=self.response(html)):
            rows = objects.PublicationsList.from_url(self.plugin.browser, objects.PublicationsList.url_from_isbn('0330020420', self.log, self.prefs), 30, self.log, self.prefs)
        self.assertEqual(rows, [{'title': 'The Offline Star', 'url': objects.Publication.url_from_id('202'), 'authors': ['Ada Example'], 'pub_year': '1970'}])

    def test_collision_qualification_preserves_distinct_records(self):
        records = []
        for identity in ('101', '102'):
            mi = Metadata('The Offline Star', ['Ada Example'])
            mi.set_identifier('isfdb-title', identity)
            records.append((mi, objects.Title.url_from_id(identity)))
        self.plugin._qualify_colliding_results(records, self.log)
        self.assertEqual([mi.title for mi, url in records], ['The Offline Star (Title #101)', 'The Offline Star (Title #102)'])

    def test_malformed_html_is_recovered_by_parser(self):
        with patch.object(objects, 'urlopen', return_value=self.response(b'<html><body><b>unclosed')):
            location, root = objects.fetch_isfdb_url(objects.Title.url_from_id('101'), 30, self.log, self.prefs)
        self.assertIn('unclosed', root.text_content())

    def test_latin1_request_encoding(self):
        url = objects.TitleList.url_from_title_and_author('\u00dcberfall', 'Ada Example', self.log, self.prefs)
        self.assertIn('%DCberfall', url)
        self.assertEqual(list(self.plugin.get_author_tokens(['Example, Ada J.'])), ['Ada', 'J.', 'Example'])

    def author_response(self, request, **kwargs):
        url = request.full_url
        if url == 'https://www.isfdb.org/cgi-bin/se.cgi?arg=Ada+Example&type=Name':
            return self.response(self.fixture('author_search.html'), url)
        if url == 'https://www.isfdb.org/cgi-bin/ea.cgi?42':
            return self.response(self.fixture('author_bibliography.html'), url)
        titles = {'101': 'The Offline Star', '102': 'The Later Star', '103': 'The First Star'}
        for identifier, title in titles.items():
            if url == objects.Title.url_from_id(identifier):
                html = self.fixture('title.html').replace(b'The Offline Star', title.encode())
                return self.response(html, url)
        self.fail('Unexpected author-search request: ' + url)

    def test_author_only_missing_and_empty_titles_return_metadata(self):
        for title in (None, ''):
            with self.subTest(title=title):
                self.prefs['search_titles'] = True
                self.prefs['search_publications'] = False
                self.prefs['max_results'] = 2
                with patch.object(objects, 'urlopen', side_effect=self.author_response) as fetch:
                    results = self.identify(title=title, authors=['Example, Ada'])
                self.assertEqual({mi.identifiers['isfdb-title'] for mi in results}, {'103', '101'})
                self.assertTrue(all(mi.authors == ['Ada Example'] for mi in results))
                self.assertEqual({mi.title for mi in results}, {'The First Star', 'The Offline Star'})
                self.assertEqual(fetch.call_count, 4)
                self.assertEqual(self.prefs['max_results'], 2)

    def test_author_bibliography_filtering_deduplication_and_dates(self):
        with patch.object(objects, 'urlopen', side_effect=self.author_response):
            rows = objects.TitleList.from_author(self.plugin.browser, 'Ada Example', 30, self.log, self.prefs)
        self.assertEqual([(row['title'], row['date']) for row in rows], [
            ('The Later Star', '1975'), ('The Offline Star', '1965'), ('The First Star', '1955')])

    def test_author_search_redirect_to_bibliography(self):
        with patch.object(objects, 'urlopen', return_value=self.response(self.fixture('author_bibliography.html'), 'https://www.isfdb.org/cgi-bin/ea.cgi?42')) as fetch:
            rows = objects.TitleList.from_author(self.plugin.browser, 'Ada Example', 30, self.log, self.prefs)
        self.assertEqual(len(rows), 3)
        self.assertEqual(fetch.call_count, 1)

    def test_author_search_no_matches(self):
        with patch.object(objects, 'urlopen', return_value=self.response(b'<div id="main">No matches</div>')) as fetch:
            self.assertEqual(self.identify(authors=['Nobody Example']), [])
        self.assertEqual(fetch.call_count, 1)

    def test_author_search_partial_name_and_author_page_limit(self):
        self.prefs['max_results'] = 1
        # No exact match: retain the site's candidate order, bound author-page
        # requests, and let the existing identify path select titles by date.
        search = self.fixture('author_search.html').replace(b'Other Ada Example', b'Ada Example Senior').replace(b'>Ada Example<', b'>Ada Example Junior<')
        def respond(request, **kwargs):
            if '/se.cgi?' in request.full_url:
                return self.response(search, request.full_url)
            if request.full_url == 'https://www.isfdb.org/cgi-bin/ea.cgi?43':
                return self.response(self.fixture('author_bibliography.html'), request.full_url)
            self.fail('Unexpected request: ' + request.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond) as fetch:
            rows = objects.TitleList.from_author(self.plugin.browser, 'Ada Example', 30, self.log, self.prefs)
        self.assertEqual(len(rows), 3)
        self.assertEqual(fetch.call_count, 2)

    def test_author_search_respects_disabled_search_preferences(self):
        self.prefs['search_titles'] = False
        self.prefs['search_publications'] = False
        with patch.object(objects, 'urlopen') as fetch:
            self.assertEqual(self.identify(authors=['Ada Example']), [])
        fetch.assert_not_called()

    def test_author_translation_language_preference(self):
        self.prefs['languages'] = 'fre'
        with patch.object(objects, 'urlopen', side_effect=self.author_response):
            rows = objects.TitleList.from_author(self.plugin.browser, 'Ada Example', 30, self.log, self.prefs)
        self.assertIn('104', [objects.Title.id_from_url(row['url']) for row in rows])

    def test_author_only_both_record_types_obey_limit(self):
        self.prefs['search_titles'] = True
        self.prefs['search_publications'] = True
        self.prefs['max_results'] = 2
        def respond(request, **kwargs):
            if request.full_url == objects.Publication.url_from_id('202'):
                return self.response(self.fixture('publication.html'), request.full_url)
            return self.author_response(request, **kwargs)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(len(results), 2)
        self.assertEqual({mi.identifiers.get('isfdb') or mi.identifiers.get('isfdb-title') for mi in results}, {'103', '202'})

    def test_author_publication_only_uses_existing_expansion(self):
        self.prefs['search_titles'] = False
        self.prefs['search_publications'] = True
        self.prefs['max_results'] = 1
        def respond(request, **kwargs):
            if request.full_url == objects.Publication.url_from_id('202'):
                return self.response(self.fixture('publication.html'), request.full_url)
            return self.author_response(request, **kwargs)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].identifiers['isfdb'], '202')
        self.assertEqual(results[0].publisher, 'Example Press')
        self.assertEqual(results[0].authors, ['Ada Example'])

    def test_empty_input_does_not_search(self):
        with patch.object(objects, 'urlopen') as fetch:
            self.assertEqual(self.identify(), [])
            self.assertEqual(self.identify(title=''), [])
        fetch.assert_not_called()

    def test_isbn_without_title_still_delivers_metadata(self):
        self.prefs['max_results'] = 1
        stub = {'url': objects.Publication.url_from_id('202')}
        publication = {'isfdb': '202', 'isfdb-title': '101', 'title': 'The Offline Star', 'authors': ['Ada Example'], 'tags': []}
        with patch.object(objects.PublicationsList, 'from_url', return_value=[stub]), patch.object(objects.Publication, 'from_url', return_value=publication), patch.object(objects.Title, 'from_url', return_value={'publications': ['202']}):
            results = self.identify(identifiers={'isbn': '0330020420'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].identifiers['isfdb'], '202')

    def test_lookup_does_not_persist_exact_search(self):
        before = Path(self.prefs.file_path).read_bytes()
        with patch.object(objects, 'urlopen', return_value=self.response(self.fixture('title.html'))):
            self.identify(title='=The Offline Star', identifiers={'isfdb-title': '101'})
        self.assertFalse(self.prefs['exact_search'])
        self.assertEqual(Path(self.prefs.file_path).read_bytes(), before)

    def test_missing_content_box(self):
        with patch.object(objects, 'urlopen', return_value=self.response(b'<html><body>No record</body></html>')):
            self.assertEqual(self.identify(identifiers={'isfdb-title': '101'}), [])

    def test_empty_html(self):
        with patch.object(objects, 'urlopen', return_value=self.response(b'')):
            location, root = objects.fetch_isfdb_url(objects.Title.url_from_id('101'), 30, self.log, self.prefs)
        self.assertEqual(root.text_content(), '')
        self.log.error.assert_called()

    def test_worker_network_failure_has_no_result(self):
        with patch.object(objects, 'urlopen', side_effect=TimeoutError('synthetic timeout')):
            self.assertEqual(self.identify(identifiers={'isfdb-title': '101'}), [])
        self.log.exception.assert_called()

    def test_existing_helper_keyword_signature(self):
        from calibre.ebooks.metadata.sources.test import test_identify_plugin
        signature = inspect.signature(test_identify_plugin)
        tree = ast.parse((REPO / '__init__.py').read_bytes())
        call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'test_identify_plugin')
        keywords = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
        print('\nInstalled test_identify_plugin parameters:', list(signature.parameters), '\nCheckout keywords:', keywords)
        signature.bind('ISFDB4', [], **keywords)

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Regression)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert all(hashlib.sha256((REPO / name).read_bytes()).hexdigest() == digest for name, digest in HASHES.items())
    print('Production input hashes unchanged; all writes confined to disposable root.')
    print('SUMMARY:', result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped) - len(result.expectedFailures),
          'passed;', len(result.failures), 'failed;', len(result.errors), 'errors;', len(result.skipped),
          'skipped;', len(result.expectedFailures), 'expected failures;', len(result.unexpectedSuccesses), 'unexpected successes')
    raise SystemExit(not result.wasSuccessful())
