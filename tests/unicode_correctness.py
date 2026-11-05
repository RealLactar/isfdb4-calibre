"""Phase 7 offline query/identity/credit correctness; GPLv3, 2026-11-04."""
import unicodedata
from urllib.parse import parse_qsl, urlsplit
from unittest.mock import patch

from calibre_plugins.isfdb4 import objects


class UnicodeCorrectness:
    def test_phase7_mixed_script_lookalike_is_not_exact_identity(self):
        with self.edge_router([('43', 'Ad\u0430 Example'), ('42', 'Ada Example')],
                              {'42': self.edge_bibliography([('101', 'Intended Work', '1965')])},
                              {'101': self.edge_title('Intended Work')}):
            results = self.identify(authors=['Ada Example'])
        self.assertEqual([mi.identifiers['isfdb-title'] for mi in results], ['101'])
        self.log.warn.assert_not_called()

    def test_phase7_ordered_credit_ids_include_unlinked_authors(self):
        from lxml.html import fromstring
        root = fromstring('<div><b>Authors:</b> Unlinked Writer and <a href="https://www.isfdb.org/cgi-bin/ea.cgi?42">Same Name</a> &amp; <span><a href="https://www.isfdb.org/cgi-bin/ea.cgi?43">Same Name</a></span><br/></div>')
        self.assertEqual(objects.title_credit_names(root[0], with_ids=True),
                         [('Unlinked Writer', None), ('Same Name', 'https://www.isfdb.org/cgi-bin/ea.cgi?42'),
                          ('Same Name', 'https://www.isfdb.org/cgi-bin/ea.cgi?43')])

    def test_phase7_latin1_parameters_and_order_are_preserved(self):
        params = {'ORDERBY': 'title_title', 'START': '0', 'TYPE': 'Title',
                  'USE_1': 'author_canonical', 'OPERATOR_1': 'contains',
                  'TERM_1': "Jos\u00e9 O'Neil & Co + 50%"}
        original = dict(params)
        query = objects.encode_query(params, self.log)
        self.assertEqual(query, 'ORDERBY=title_title&START=0&TYPE=Title&USE_1=author_canonical&OPERATOR_1=contains&TERM_1=Jos%E9+O%27Neil+%26+Co+%2B+50%25')
        self.assertEqual(parse_qsl(query, encoding='latin1'), list(params.items()))
        self.assertEqual(params, original)

    def test_phase7_supported_latin1_names_roundtrip(self):
        for name in ('Jos\u00e9', 'Zo\u00eb', 'M\u00fcller', 'Fran\u00e7ois', 'Stra\u00dfe', '\u00b5 Example'):
            with self.subTest(name=name):
                query = objects.encode_query({'arg': name, 'type': 'Name'}, self.log)
                self.assertEqual(parse_qsl(query, encoding='latin1'), [('arg', name), ('type', 'Name')])

    def test_phase7_unsupported_scripts_fail_with_parameter_and_codepoint(self):
        names = ['\u0418\u0432\u0430\u043d', '\u039d\u03af\u03ba\u03bf\u03c2', '\u4e2d\u6587', '\u5bae\u5d0e',
                 'O\u2019Neil', 'A\u2014B', 'Ada \u0410', 'x\u0301 Example']
        for name in names:
            with self.subTest(name=name):
                params = {'arg': name, 'type': 'Name', 'START': '0'}
                before = dict(params)
                with self.assertRaises(objects.UnsupportedQuery) as caught:
                    objects.SearchResults.simple_url_from_params(params, self.log, self.prefs)
                normalized = unicodedata.normalize('NFC', name)
                unsupported = next(c for c in normalized if ord(c) > 255)
                self.assertIn('arg', str(caught.exception))
                self.assertIn('U+{:04X}'.format(ord(unsupported)), str(caught.exception))
                self.assertEqual(params, before)

    def test_phase7_nfc_is_canonical_not_compatibility_transliteration(self):
        self.assertEqual(objects.encode_query({'arg': 'Jose\u0301', 'type': 'Name'}, self.log),
                         'arg=Jos%E9&type=Name')
        self.assertIn('%B5', objects.encode_query({'arg': '\u00b5', 'type': 'Name'}, self.log))
        for name in ('\u03bc', '\uff2aose', 'x\u0301'):
            with self.subTest(name=name), self.assertRaises(objects.UnsupportedQuery):
                objects.encode_query({'arg': name, 'type': 'Name'}, self.log)

    def test_phase7_nonlatin_input_with_multiple_parameters_never_sends_partial_query(self):
        for params in ({'arg': '\u5bae\u5d0e', 'type': 'Name', 'START': '0'},
                       {'type': 'Name', 'START': '0', 'arg': 'Ada \u0410'}):
            with self.subTest(params=params), patch.object(objects, 'urlopen') as fetch:
                with self.assertRaises(objects.UnsupportedQuery):
                    objects.SearchResults.simple_url_from_params(params, self.log, self.prefs)
                fetch.assert_not_called()
        with patch.object(objects, 'urlopen') as fetch:
            self.assertEqual(self.identify(authors=['Ada \u0410']), [])
        fetch.assert_not_called()

    def test_phase7_advanced_query_rejects_unrepresentable_term_atomically(self):
        params = {'TYPE': 'Title', 'USE_1': 'title_title', 'TERM_1': 'Caf\u00e9',
                  'CONJUNCTION_1': 'AND', 'USE_2': 'author_canonical', 'TERM_2': '\u0418\u0432\u0430\u043d'}
        with self.assertRaises(objects.UnsupportedQuery) as caught:
            objects.SearchResults.url_from_params(params, self.log, self.prefs)
        self.assertIn('TERM_2', str(caught.exception))

    def test_phase7_casefold_expansion_does_not_override_exact_author_name(self):
        with self.edge_router([('43', 'Strasse Example'), ('42', 'Stra\u00dfe Example')],
                              {'42': self.edge_bibliography([('101', 'Intended Work', '1965')])},
                              {'101': self.edge_title('Intended Work', ('Stra\u00dfe Example',))}):
            results = self.identify(authors=['Stra\u00dfe Example'])
        self.assertEqual(results[0].authors, ['Stra\u00dfe Example'])
        self.log.warn.assert_not_called()

    def test_phase7_exact_punctuation_match_precedes_name_variant(self):
        with self.edge_router([('43', 'O Neil'), ('42', "O'Neil")],
                              {'42': self.edge_bibliography([('101', 'Intended Work', '1965')])},
                              {'101': self.edge_title('Intended Work', ("O'Neil",))}):
            results = self.identify(authors=["O'Neil"])
        self.assertEqual(results[0].authors, ["O'Neil"])
        self.log.warn.assert_not_called()

    def test_phase7_partial_pseudonyms_keep_separate_ids_and_ambiguity(self):
        with self.edge_router([('42', 'Ada Canonical'), ('43', 'Ada Pen Name')],
                              {'42': self.edge_bibliography([('101', 'Canonical Work', '1965')]),
                               '43': self.edge_bibliography([('102', 'Pen Name Work', '1975')])},
                              {'101': self.edge_title('Canonical Work', ('Ada Canonical',)),
                               '102': self.edge_title('Pen Name Work', ('Ada Pen Name',))}):
            results = self.identify(authors=['Ada'])
        self.assertEqual({mi.identifiers['isfdb-title'] for mi in results}, {'101', '102'})
        self.assertTrue(all('Ambiguous author search' in mi.comments for mi in results))
        self.log.warn.assert_called()

    def test_phase7_mixed_script_metadata_works_with_stable_identifiers(self):
        self.prefs['search_publications'] = False
        def respond(request, **kwargs):
            if '/ea.cgi?' in request.full_url:
                return self.response(self.edge_bibliography([('101', 'Mixed Work', '1965')]), request.full_url)
            return self.response(self.edge_title('Mixed Work', ('Ada \u0410',)), request.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(authors=['Ada \u0410'], identifiers={'isfdb-author': '42'})
        self.assertEqual(results[0].authors, ['Ada \u0410'])

    def test_phase7_distinct_homonym_coauthors_survive_publication_merge(self):
        def respond(request, **kwargs):
            html = self.fixture('publication.html') if '/pl.cgi?' in request.full_url else self.edge_title(authors=('Ada Example', 'Ada Example'))
            return self.response(html, request.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(identifiers={'isfdb': '202', 'isfdb-title': '101'})
        self.assertEqual(results[0].authors, ['Ada Example', 'Ada Example'])

    def test_phase7_canonical_spelling_and_coauthor_order_are_preserved(self):
        def respond(request, **kwargs):
            if '/pl.cgi?' in request.full_url:
                html = self.fixture('publication.html').replace(b'Ada Example', b'Jose&#769; Example')
            else:
                html = self.edge_title(authors=('Jos\u00e9 Example', 'Bea Collaborator'))
            return self.response(html, request.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            results = self.identify(identifiers={'isfdb': '202', 'isfdb-title': '101'})
        self.assertEqual(results[0].authors, ['Jose\u0301 Example', 'Bea Collaborator'])
