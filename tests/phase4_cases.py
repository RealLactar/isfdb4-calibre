"""Focused correctness tests for the Phase 4 production fixes."""
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from calibre_plugins.isfdb4 import objects


class Phase4Cases:
    def test_phase4_explicit_author_id_bypasses_name_ambiguity(self):
        self.prefs['search_publications'] = False
        def respond(request, **kwargs):
            url = request.full_url
            if url == 'https://www.isfdb.org/cgi-bin/ea.cgi?42':
                return self.response(self.edge_bibliography([('101', 'The Offline Star', '1965')]), url)
            if url == objects.Title.url_from_id('101'):
                return self.response(self.edge_title(), url)
            self.fail('Author ID lookup unexpectedly searched by name: ' + url)
        with patch.object(objects, 'urlopen', side_effect=respond) as fetch:
            results = self.identify(identifiers={'isfdb-author': '42'})
        self.assertEqual(results[0].identifiers['isfdb-title'], '101')
        self.assertEqual(fetch.call_count, 2)

    def test_phase4_invalid_author_id_does_not_send_query(self):
        with patch.object(objects, 'urlopen') as fetch:
            self.assertEqual(self.identify(identifiers={'isfdb-author': '42&extra=1'}), [])
        fetch.assert_not_called()
        self.log.error.assert_called()

    def test_phase4_nonlatin_author_can_use_known_id(self):
        self.prefs['search_publications'] = False
        def respond(request, **kwargs):
            url = request.full_url
            if '/ea.cgi?' in url:
                return self.response(self.edge_bibliography([('101', 'The Offline Star', '1965')]), url)
            if '/title.cgi?' in url:
                return self.response(self.edge_title(authors=('\u5bae\u5d0e \u99ff',)), url)
            self.fail('Unexpected name query: ' + url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(authors=['\u5bae\u5d0e \u99ff'], identifiers={'isfdb-author': '42'})
        self.assertEqual(results[0].authors, ['\u5bae\u5d0e \u99ff'])

    def test_phase4_alias_redirects_group_by_author_id(self):
        def respond(request, **kwargs):
            if '/se.cgi?' in request.full_url:
                return self.response(self.edge_search([('42', 'Ada Example'), ('73', 'A. Example')]), request.full_url)
            return self.response(self.edge_bibliography([('101', 'The Offline Star', '1965')]), 'https://www.isfdb.org/cgi-bin/ea.cgi?42')
        with patch.object(objects, 'urlopen', side_effect=respond):
            stubs = objects.TitleList.from_author(self.plugin.browser, 'Example', 30, self.log, self.prefs)
        self.assertEqual(len(stubs), 1)
        self.assertEqual(list(stubs[0]['author_sources']), ['https://www.isfdb.org/cgi-bin/ea.cgi?42'])
        self.assertNotIn('author_ambiguity', stubs[0])
        self.log.warn.assert_not_called()

    def test_phase4_shared_work_displays_all_ambiguous_sources(self):
        shared = self.edge_bibliography([('101', 'The Offline Star', '1965')])
        with self.edge_router([('42', 'Ada Example Senior'), ('43', 'Ada Example Junior')],
                              {'42': shared, '43': shared}, {'101': self.edge_title()}):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(len(results), 1)
        self.assertIn('ISFDB author #42', results[0].comments)
        self.assertIn('ISFDB author #43', results[0].comments)

    def test_phase4_unexamined_candidate_is_explicit(self):
        with self.edge_router([('42', 'Ada Example Senior'), ('43', 'Ada Example Junior')],
                              {'42': self.edge_bibliography([('101', 'The Offline Star', '1965')])},
                              {'101': self.edge_title()}):
            self.prefs['max_results'] = 1
            results = self.identify(authors=['Ada Example'])
        self.assertIn('candidate ISFDB author IDs: 42, 43', results[0].comments)
        self.log.warn.assert_called()

    def test_phase4_empty_candidate_scan_has_hard_bound(self):
        candidates = [(str(i), 'Example ' + str(i)) for i in range(30)]
        bibliographies = {str(i): self.edge_bibliography([]) for i in range(20)}
        with self.edge_router(candidates, bibliographies, {}) as fetch:
            self.prefs['max_results'] = 1
            self.assertEqual(self.identify(authors=['Example']), [])
        self.assertEqual(fetch.call_count, 21)  # One Name request plus 20 pages.
        self.assertTrue(any('scan limited' in str(call) for call in self.log.warn.call_args_list))

    def test_phase4_empty_and_whitespace_responses_are_safe(self):
        for payload in (b'', b' \n\r\t'):
            for identifiers in ({'isfdb-title': '101'}, {'isfdb': '202'}):
                with self.subTest(payload=payload, identifiers=identifiers), patch.object(objects, 'urlopen', return_value=self.response(payload)):
                    self.assertEqual(self.identify(identifiers=identifiers), [])
        self.assertTrue(any('Empty ISFDB response' in str(call) for call in self.log.error.call_args_list))

    def test_phase4_query_encoding_preserves_all_latin1_parameters(self):
        for build in (objects.SearchResults.url_from_params, objects.SearchResults.simple_url_from_params):
            url = build({'arg': 'Jos\u00e9 Example', 'type': 'Name', 'TERM_2': 'A&B'}, self.log, self.prefs)
            self.assertEqual(parse_qs(urlsplit(url).query, encoding='latin1'),
                             {'arg': ['Jos\u00e9 Example'], 'type': ['Name'], 'TERM_2': ['A&B']})

    def test_phase4_unsupported_unicode_fails_before_network(self):
        for build in (objects.SearchResults.url_from_params, objects.SearchResults.simple_url_from_params):
            with self.assertRaises(objects.UnsupportedQuery):
                build({'arg': '\u5bae\u5d0e', 'type': 'Name'}, self.log, self.prefs)
        with patch.object(objects, 'urlopen') as fetch:
            self.assertEqual(self.identify(title='\u5bae\u5d0e', authors=['Ada Example']), [])
        fetch.assert_not_called()

    def test_phase4_decomposed_latin1_query_is_normalized_losslessly(self):
        url = objects.SearchResults.simple_url_from_params({'arg': 'Jose\u0301', 'type': 'Name'}, self.log, self.prefs)
        self.assertIn('arg=Jos%E9&type=Name', url)

    def test_phase4_nested_and_tooltip_coauthor_representations(self):
        original = '<b>Author:</b> <a href="https://www.isfdb.org/cgi-bin/ea.cgi?42">Ada Example</a>'
        forms = [
            '<b>Authors:</b> <div class="tooltip tooltipright"><a href="https://www.isfdb.org/cgi-bin/ea.cgi?42"><em>Ada</em> Example</a><sup class="mouseover">?</sup><span class="tooltiptext tooltipnarrow tooltipright">Alias</span></div> and <a href="https://www.isfdb.org/cgi-bin/ea.cgi?43">Bea Collaborator</a>',
            '<strong>Authors:</strong> <span>Ada Example</span> and <span>Bea Collaborator</span>',
            '<b>Authors:</b> Ada Example and Bea Collaborator',
            '<b>Authors:</b> <div><span>Ada Example</span> and <a href="https://www.isfdb.org/cgi-bin/ea.cgi?43"><em>Bea</em> Collaborator</a></div>',
            '<b>Author:</b> <a href="https://www.isfdb.org/cgi-bin/ea.cgi?42">Ada Example</a><br><b>Author:</b> <a href="https://www.isfdb.org/cgi-bin/ea.cgi?43">Bea Collaborator</a>',
        ]
        for form in forms:
            html = self.fixture('title.html').decode().replace(original, form).encode()
            with self.subTest(form=form), patch.object(objects, 'urlopen', return_value=self.response(html)):
                data = objects.Title.from_url(self.plugin.browser, objects.Title.url_from_id('101'), 30, self.log, self.prefs)
            self.assertEqual(data['authors'], ['Ada Example', 'Bea Collaborator'])

    def test_phase4_publication_merge_keeps_missing_title_coauthor(self):
        def respond(request, **kwargs):
            html = self.fixture('publication.html') if '/pl.cgi?' in request.full_url else self.edge_title(authors=('Ada Example', 'Bea Collaborator'))
            return self.response(html, request.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(identifiers={'isfdb': '202', 'isfdb-title': '101'})
        self.assertEqual(results[0].authors, ['Ada Example', 'Bea Collaborator'])

    def test_phase4_publication_credit_order_is_preserved(self):
        def respond(request, **kwargs):
            if '/pl.cgi?' in request.full_url:
                html = self.fixture('publication.html').replace(
                    b'<a href="https://www.isfdb.org/cgi-bin/ea.cgi?42">Ada Example</a>',
                    b'<a href="https://www.isfdb.org/cgi-bin/ea.cgi?43">Bea Collaborator</a> <a href="https://www.isfdb.org/cgi-bin/ea.cgi?42">Ada Example</a>')
            else:
                html = self.edge_title(authors=('Ada Example', 'Bea Collaborator'))
            return self.response(html, request.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(identifiers={'isfdb': '202', 'isfdb-title': '101'})
        self.assertEqual(results[0].authors, ['Bea Collaborator', 'Ada Example'])

    def test_phase4_merge_preserves_publication_alias_without_duplicate_identity(self):
        def respond(request, **kwargs):
            if '/pl.cgi?' in request.full_url:
                html = self.fixture('publication.html').replace(b'Ada Example', b'A. Example')
            else:
                html = self.edge_title(authors=('Ada Example', 'Bea Collaborator'))
            return self.response(html, request.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(identifiers={'isfdb': '202', 'isfdb-title': '101'})
        self.assertEqual(results[0].authors, ['A. Example', 'Bea Collaborator'])

    def test_phase4_calibre_logger_supports_warning_method(self):
        from calibre.ebooks.metadata.sources.base import create_log
        self.assertTrue(callable(create_log().warn))
