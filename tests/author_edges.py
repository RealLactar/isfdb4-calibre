"""Offline characterization of author-search boundaries; no production overrides."""
from html import escape
from urllib.parse import parse_qs, urlsplit
import unittest
from unittest.mock import patch

from calibre_plugins.isfdb4 import objects


class AuthorEdges:
    """Mixed into the existing isolated Regression TestCase."""

    def edge_search(self, candidates):
        rows = ''.join('<tr><td><a href="https://www.isfdb.org/cgi-bin/ea.cgi?{}">{}</a></td></tr>'.format(
            identifier, escape(name)) for identifier, name in candidates)
        return ('<div id="main"><table>' + rows + '</table></div>').encode('ascii', 'xmlcharrefreplace')

    def edge_bibliography(self, entries):
        rows = ''.join('<li><a class="italic" href="https://www.isfdb.org/cgi-bin/title.cgi?{}">{}</a>{}</li>'.format(
            identifier, escape(title), ' (<b>{}</b>)'.format(year) if year else '')
            for identifier, title, year in entries)
        return ('<div id="content"><div class="ContentBox"><ul><li><b>Language:</b> English</li></ul></div>'
                '<div class="ContentBox"><table class="bibliolinks"><tr><td>Other views</td></tr></table>'
                '<ul>' + rows + '</ul></div></div>').encode('ascii', 'xmlcharrefreplace')

    def edge_title(self, title='The Offline Star', authors=('Ada Example',), date='1965-00-00', series=False, publications=('202',)):
        html = self.fixture('title.html').decode('ascii')
        html = html.replace('The Offline Star', escape(title))
        html = html.replace('<a href="https://www.isfdb.org/cgi-bin/ea.cgi?42">Ada Example</a>',
                            ' '.join('<a href="https://www.isfdb.org/cgi-bin/ea.cgi?{}">{}</a>'.format(i + 42, escape(name)) for i, name in enumerate(authors)))
        if date is None:
            html = html.replace('<b>Date:</b> 1965-00-00<br>', '')
        else:
            html = html.replace('1965-00-00', date)
        if series:
            html = html.replace('<b>Language:', '<b>Series:</b> <a href="https://www.isfdb.org/cgi-bin/pe.cgi?7">Offline Cycle</a><br><b>Series Number:</b> 2<br><b>Language:')
        html = html.replace('<a href="https://www.isfdb.org/cgi-bin/pl.cgi?202">Publication</a>',
                            ''.join('<a href="https://www.isfdb.org/cgi-bin/pl.cgi?{}">Publication</a>'.format(identifier) for identifier in publications))
        return html.encode('ascii', 'xmlcharrefreplace')

    def edge_router(self, candidates, bibliographies, titles):
        def respond(request, **kwargs):
            url = request.full_url
            if '/se.cgi?' in url:
                self.assertEqual(parse_qs(urlsplit(url).query).get('type'), ['Name'])
                return self.response(self.edge_search(candidates), url)
            if '/ea.cgi?' in url:
                return self.response(bibliographies[urlsplit(url).query], url)
            if '/title.cgi?' in url:
                return self.response(titles[urlsplit(url).query], url)
            self.fail('Unexpected offline edge-case request: ' + url)
        self.prefs['search_titles'] = True
        self.prefs['search_publications'] = False
        return patch.object(objects, 'urlopen', side_effect=respond)

    def test_edge_exact_name_excludes_similar_names(self):
        with self.edge_router([('43', 'Ada Example Junior'), ('42', 'Ada Example')],
                              {'42': self.edge_bibliography([('101', 'The Offline Star', '1965')])},
                              {'101': self.edge_title()}) as fetch:
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].authors, ['Ada Example'])
        self.assertFalse(any('/ea.cgi?43' in call.args[0].full_url for call in fetch.call_args_list))

    def test_edge_identical_names_retain_explicit_identity_provenance(self):
        candidates = [('42', 'Ada Example'), ('43', 'Ada Example')]
        biblios = {'42': self.edge_bibliography([('101', 'First Identity', '1965')]),
                   '43': self.edge_bibliography([('201', 'Second Identity', '1975')])}
        with self.edge_router(candidates, biblios, {'101': self.edge_title('First Identity'), '201': self.edge_title('Second Identity')}):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual({mi.identifiers['isfdb-title'] for mi in results}, {'101', '201'})
        self.assertTrue(all(mi.authors == ['Ada Example'] for mi in results))
        self.log.warn.assert_called()
        for mi in results:
            self.assertIn('Ambiguous author search', mi.comments)
            source = '42' if mi.identifiers['isfdb-title'] == '101' else '43'
            self.assertIn('Source bibliography: <a href="https://www.isfdb.org/cgi-bin/ea.cgi?' + source, mi.comments)

    def test_edge_partial_name_matches_expose_ambiguity(self):
        candidates = [('42', 'Ada Example Senior'), ('43', 'Ada Example Junior')]
        biblios = {'42': self.edge_bibliography([('101', 'Senior Work', '1965')]),
                   '43': self.edge_bibliography([('201', 'Junior Work', '1975')])}
        titles = {'101': self.edge_title('Senior Work', ('Ada Example Senior',)),
                  '201': self.edge_title('Junior Work', ('Ada Example Junior',))}
        with self.edge_router(candidates, biblios, titles):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual({tuple(mi.authors) for mi in results}, {('Ada Example Senior',), ('Ada Example Junior',)})
        self.log.warn.assert_called()
        self.assertTrue(all('Ambiguous author search' in mi.comments for mi in results))

    def test_edge_duplicate_author_links_fetch_once(self):
        with self.edge_router([('42', 'Ada Example'), ('42', 'Ada Example')],
                              {'42': self.edge_bibliography([('101', 'The Offline Star', '1965')])},
                              {'101': self.edge_title()}) as fetch:
            self.assertEqual(len(self.identify(authors=['Ada Example'])), 1)
        self.assertEqual(sum('/ea.cgi?' in call.args[0].full_url for call in fetch.call_args_list), 1)

    def test_edge_shared_title_across_author_candidates_fetched_once(self):
        shared = self.edge_bibliography([('101', 'The Offline Star', '1965')])
        with self.edge_router([('42', 'Ada Example Senior'), ('43', 'Ada Example Junior')],
                              {'42': shared, '43': shared}, {'101': self.edge_title()}) as fetch:
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(len(results), 1)
        self.assertEqual(sum('/title.cgi?' in call.args[0].full_url for call in fetch.call_args_list), 1)

    def test_edge_known_coauthored_title_keeps_all_authors(self):
        with self.edge_router([('42', 'Ada Example')],
                              {'42': self.edge_bibliography([('101', 'The Offline Star', '1965')])},
                              {'101': self.edge_title(authors=('Ada Example', 'Bea Collaborator'))}):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].authors, ['Ada Example', 'Bea Collaborator'])

    def test_edge_multiple_editions_remain_distinct_without_duplicate_ids(self):
        title = self.edge_title(publications=('202', '203', '202'))
        def respond(request, **kwargs):
            url = request.full_url
            if '/se.cgi?' in url:
                return self.response(self.edge_search([('42', 'Ada Example')]), url)
            if '/ea.cgi?' in url:
                return self.response(self.edge_bibliography([('101', 'The Offline Star', '1965')]), url)
            if '/title.cgi?' in url:
                return self.response(title, url)
            if '/pl.cgi?' in url:
                return self.response(self.fixture('publication.html'), url)
            self.fail(url)
        self.prefs['search_titles'] = False
        self.prefs['search_publications'] = True
        self.prefs['max_results'] = 5
        with patch.object(objects, 'urlopen', side_effect=respond) as fetch:
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(len(results), 2)
        self.assertEqual({mi.identifiers['isfdb'] for mi in results}, {'202', '203'})
        self.assertEqual({mi.title for mi in results}, {'The Offline Star (Pub #202)', 'The Offline Star (Pub #203)'})
        self.assertEqual(sum('/pl.cgi?' in call.args[0].full_url for call in fetch.call_args_list), 2)

    def test_edge_series_and_nonseries_metadata(self):
        with self.edge_router([('42', 'Ada Example')],
                              {'42': self.edge_bibliography([('101', 'Series Work', '1965'), ('102', 'Standalone', '1975')])},
                              {'101': self.edge_title('Series Work', series=True), '102': self.edge_title('Standalone')}):
            results = {mi.identifiers['isfdb-title']: mi for mi in self.identify(authors=['Ada Example'])}
        self.assertEqual(results['101'].series, 'Offline Cycle')
        self.assertEqual(results['101'].series_index, 2)
        self.assertIsNone(results['102'].series)

    def test_edge_large_bibliography_selects_earliest_with_limit(self):
        entries = [(str(1000 + i), 'Work {}'.format(i), str(1900 + i)) for i in reversed(range(200))]
        with self.edge_router([('42', 'Ada Example')], {'42': self.edge_bibliography(entries)},
                              {str(1000 + i): self.edge_title('Work {}'.format(i)) for i in range(3)}) as fetch:
            self.prefs['max_results'] = 3
            results = self.identify(authors=['Ada Example'])
        self.assertEqual({mi.identifiers['isfdb-title'] for mi in results}, {'1000', '1001', '1002'})
        self.assertEqual(fetch.call_count, 5)
        self.assertEqual(self.prefs['max_results'], 3)

    def test_edge_empty_bibliography_returns_empty_with_diagnostic(self):
        with self.edge_router([('42', 'Ada Example')], {'42': b''}, {}):
            self.assertEqual(self.identify(authors=['Ada Example']), [])
        self.log.error.assert_called()

    def test_edge_valid_bibliography_without_titles_returns_empty(self):
        with self.edge_router([('42', 'Ada Example')], {'42': self.edge_bibliography([])}, {}):
            self.assertEqual(self.identify(authors=['Ada Example']), [])

    def test_edge_malformed_bibliography_without_structure_returns_empty(self):
        with self.edge_router([('42', 'Ada Example')], {'42': b'<html><div><b>broken'}, {}):
            self.assertEqual(self.identify(authors=['Ada Example']), [])

    def test_edge_recoverable_unclosed_bibliography_list(self):
        html = self.edge_bibliography([('101', 'The Offline Star', '1965')]).replace(b'</li>', b'')
        with self.edge_router([('42', 'Ada Example')], {'42': html}, {'101': self.edge_title()}):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(results[0].identifiers['isfdb-title'], '101')

    def test_edge_missing_dates_sort_before_known_dates(self):
        for date in (None, 'date unknown'):
            with self.subTest(date=date), self.edge_router([('42', 'Ada Example')],
                                  {'42': self.edge_bibliography([('101', 'Dated', '1965'), ('102', 'Undated', date)])},
                                  {'102': self.edge_title('Undated', date=date)}):
                self.prefs['max_results'] = 1
                results = self.identify(authors=['Ada Example'])
            self.assertEqual(results[0].identifiers['isfdb-title'], '102')
            self.assertTrue(results[0].is_null('pubdate'))

    def test_edge_case_and_surname_order_variations(self):
        with self.edge_router([('42', 'ADA EXAMPLE'), ('43', 'Ada Example Junior')],
                              {'42': self.edge_bibliography([('101', 'The Offline Star', '1965')])},
                              {'101': self.edge_title()}) as fetch:
            results = self.identify(authors=['Example, Ada'])
        query = parse_qs(urlsplit(fetch.call_args_list[0].args[0].full_url).query)
        self.assertEqual(query, {'arg': ['Ada Example'], 'type': ['Name']})
        self.assertEqual(results[0].authors, ['Ada Example'])

    def test_edge_latin1_unicode_name_returns_metadata(self):
        name = 'Jos\u00e9 Example'
        with self.edge_router([('42', name)], {'42': self.edge_bibliography([('101', 'The Offline Star', '1965')])},
                              {'101': self.edge_title(authors=(name,))}) as fetch:
            results = self.identify(authors=[name])
        self.assertIn('arg=Jos%E9+Example&type=Name', fetch.call_args_list[0].args[0].full_url)
        self.assertEqual(results[0].authors, [name])

    def test_edge_nonlatin_name_is_rejected_without_broader_query(self):
        with patch.object(objects, 'urlopen', return_value=self.response(self.edge_search([]))) as fetch:
            self.assertEqual(self.identify(authors=['\u5bae\u5d0e \u99ff']), [])
        fetch.assert_not_called()
        self.log.error.assert_called()

    def test_edge_coauthored_publication_keeps_all_authors(self):
        html = self.fixture('publication.html').replace(
            b'>Ada Example</a>', b'>Ada Example</a> <a href="https://www.isfdb.org/cgi-bin/ea.cgi?43">Bea Collaborator</a>')
        with patch.object(objects, 'urlopen', return_value=self.response(html)):
            data = objects.Publication.from_url(self.plugin.browser, objects.Publication.url_from_id('202'), 30, self.log, self.prefs)
        self.assertEqual(data['authors'], ['Ada Example', 'Bea Collaborator'])

    def test_edge_equal_date_selection_preserves_bibliography_order(self):
        entries = [('105', 'First Listed', '1965'), ('102', 'Second Listed', '1965'), ('101', 'Third Listed', '1965')]
        with self.edge_router([('42', 'Ada Example')], {'42': self.edge_bibliography(entries)},
                              {'105': self.edge_title('First Listed'), '102': self.edge_title('Second Listed')}):
            self.prefs['max_results'] = 2
            results = self.identify(authors=['Ada Example'])
        self.assertEqual({mi.identifiers['isfdb-title'] for mi in results}, {'105', '102'})

    def test_edge_composed_and_decomposed_unicode_names_select_same_identity(self):
        candidates = [('43', 'Jos\u00e9 Example Junior'), ('42', 'Jose\u0301 Example')]
        with self.edge_router(candidates, {'42': self.edge_bibliography([('101', 'Intended', '1965')])},
                              {'101': self.edge_title('Intended', ('Jos\u00e9 Example',))}):
            self.prefs['max_results'] = 1
            results = self.identify(authors=['Jos\u00e9 Example'])
        self.assertEqual(results[0].authors, ['Jos\u00e9 Example'])

    def test_edge_punctuation_variation_selects_matching_identity(self):
        candidates = [('43', 'Ada J Example Junior'), ('42', 'Ada J. Example')]
        with self.edge_router(candidates, {'42': self.edge_bibliography([('101', 'Intended', '1965')])},
                              {'101': self.edge_title('Intended', ('Ada J. Example',))}):
            self.prefs['max_results'] = 1
            results = self.identify(authors=['Ada J Example'])
        self.assertEqual(results[0].authors, ['Ada J. Example'])

    def test_edge_empty_candidate_does_not_consume_useful_page_allowance(self):
        with self.edge_router([('43', 'Ada Example Senior'), ('42', 'Ada Example Junior')],
                              {'43': self.edge_bibliography([]), '42': self.edge_bibliography([('101', 'Useful', '1965')])},
                              {'101': self.edge_title('Useful', ('Ada Example Junior',))}) as fetch:
            self.prefs['max_results'] = 1
            results = self.identify(authors=['Ada Example'])
        self.assertEqual(results[0].identifiers['isfdb-title'], '101')
        self.assertEqual(fetch.call_count, 4)
