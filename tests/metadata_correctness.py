"""Local ISFDB4 Phase 9A regression cases; existing GPLv3 lineage applies."""
from unittest.mock import patch
from calibre_plugins.isfdb4 import objects


class MetadataCorrectness:
    def test_phase9_rating_source_contract(self):
        from calibre.ebooks.metadata.sources import identify
        html = self.fixture('title.html').replace(b'<b>Language:', b'<b>User Rating:</b> 9.00 (5 votes)<br><b>Language:')
        with patch.object(objects, 'urlopen', return_value=self.response(html)):
            data = self.identify(identifiers={'isfdb-title':'101'})
        self.assertEqual(data[0].rating, 4.5)
        data[0].relevance_in_source = 0
        data[0].identify_plugin = self.plugin
        merged = identify.ISBNMerge(self.log).merge(data, 1965)
        # Calibre accepts source stars in 0..5, then rounds their mean here.
        # This is not the library's 0..10 storage contract.
        self.assertEqual(merged.rating, 4)

    def test_phase9_existing_volume_issue_notes(self):
        html=self.fixture('publication.html').replace(b'</ul>',b'<li><b>Notes:</b> <div class="notes">Vol. 4, No. 3</div></li></ul>')
        self.prefs['series_index_options']='vol_and_no'
        with patch.object(objects,'urlopen',return_value=self.response(html)):
            data=objects.Publication.from_url(None,objects.Publication.url_from_id('202'),30,self.log,self.prefs)
        self.assertEqual(data['series_index'],4.03)

    def test_phase9_publication_decimal_indices(self):
        for text, expected in [('1',1),('1.5',1.5),('2.25',2.25),('IV',4),('61/62',61)]:
            with self.subTest(text=text):
                html = self.fixture('publication.html').replace(b'</ul>', ('<li><b>Pub. Series:</b> <a href="https://www.isfdb.org/cgi-bin/pubseries.cgi?7">Cycle</a></li><li><b>Pub. Series #:</b> '+text+'</li></ul>').encode())
                with patch.object(objects, 'urlopen', return_value=self.response(html)), patch.object(objects.Series,'from_url',return_value='Cycle'):
                    data=objects.Publication.from_url(None,objects.Publication.url_from_id('202'),30,self.log,self.prefs)
                self.assertEqual(data['series_index'],expected)

    def test_phase9_missing_optional_combinations(self):
        for removals in [(), ('Type',), ('Type','Date','Language'), ('Type','Date','Author','Synopsis')]:
            with self.subTest(removals=removals):
                import re
                html=self.fixture('title.html')
                for label in removals:
                    html=re.sub(rb'<b>'+label.encode()+rb':</b>.*?<br>',b'',html)
                with patch.object(objects,'urlopen',return_value=self.response(html)):
                    data=self.identify(identifiers={'isfdb-title':'101'})
                self.assertEqual(len(data),1)
                self.assertEqual(data[0].title,'The Offline Star')
                self.assertEqual(data[0].identifiers['isfdb-title'],'101')

    def test_phase9_template_fallback_and_fields(self):
        from calibre.ebooks.metadata.book.base import Metadata
        for template, series, index, expected in [('{title} - {authors}',None,None,'Book - Ada'),
                ('{series} {series_index:.2f}', 'Cycle',2.25,'Cycle 2.25'),
                ('{title} {series_index:.2f}',None,None,'Book '),
                ('{title} {series_index:bad}','Cycle',2,'Book'),
                ('{unknown}',None,None,'Book')]:
            with self.subTest(template=template):
                mi=Metadata('Book',['Ada']); mi.series=series; mi.series_index=index
                self.prefs['title_template']=template
                self.plugin.clean_downloaded_metadata(mi)
                self.assertEqual(mi.title,expected)

    def test_phase9_malformed_or_missing_series_index(self):
        for text in ('nonsense','1.2.3',''):
            with self.subTest(text=text):
                html=self.edge_title(series=True).replace(b'Series Number:</b> 2',('Series Number:</b> '+text).encode())
                with patch.object(objects,'urlopen',return_value=self.response(html)):
                    data=objects.Title.from_url(None,objects.Title.url_from_id('101'),30,self.log,self.prefs)
                self.assertNotIn('series_index',data)

    def test_phase9_publication_missing_or_malformed_index(self):
        for text in ('nonsense','1.2.3',''):
            with self.subTest(text=text):
                html=self.fixture('publication.html').replace(b'</ul>', ('<li><b>Pub. Series:</b> <a href="https://www.isfdb.org/cgi-bin/pubseries.cgi?7">Cycle</a></li><li><b>Pub. Series #:</b> '+text+'</li></ul>').encode())
                with patch.object(objects,'urlopen',return_value=self.response(html)), patch.object(objects.Series,'from_url',return_value='Cycle'):
                    data=objects.Publication.from_url(None,objects.Publication.url_from_id('202'),30,self.log,self.prefs)
                self.assertIsNone(data.get('series_index'))

    def test_phase9_empty_optional_fields_keep_record(self):
        html=self.fixture('title.html').replace(b'Type:</b> NOVEL',b'Type:</b>').replace(b'Date:</b> 1965-00-00',b'Date:</b>')
        with patch.object(objects,'urlopen',return_value=self.response(html)):
            data=self.identify(identifiers={'isfdb-title':'101'})
        self.assertEqual(len(data),1)
        self.assertEqual(data[0].authors,['Ada Example'])

    def test_phase9_publication_optional_fields_keep_record(self):
        import re
        def respond(req,**kw):
            html=self.fixture('publication.html') if '/pl.cgi?' in req.full_url else self.fixture('title.html')
            html=re.sub(rb'<li><b>(Type|Date|Publisher):</b>.*?</li>',b'',html)
            html=html.replace(b'<b>Type:</b> NOVEL<br>',b'')
            return self.response(html,req.full_url)
        with patch.object(objects,'urlopen',side_effect=respond):
            data=self.identify(identifiers={'isfdb':'202','isfdb-title':'101'})
        self.assertEqual(len(data),1)
        self.assertEqual(data[0].identifiers['isfdb'],'202')
        self.assertEqual(data[0].authors,['Ada Example'])
        self.assertTrue(data[0].comments)

    def test_phase9_standalone_series_missing_index(self):
        html=self.edge_title(series=True).replace(b'<b>Series Number:</b> 2<br>',b'')
        with patch.object(objects,'urlopen',return_value=self.response(html)):
            data=self.identify(identifiers={'isfdb-title':'101'})
        self.assertEqual(data[0].series,'Offline Cycle')
        self.assertIsNone(data[0].series_index)

    def test_phase9_template_missing_authors(self):
        from calibre.ebooks.metadata.book.base import Metadata
        mi=Metadata('Book',[])
        mi.authors=[]
        self.prefs['title_template']='{title} - {authors}{series}{series_code}{main_series}'
        self.plugin.clean_downloaded_metadata(mi,self.log)
        self.assertEqual(mi.title,'Book - ')

    def test_phase9_collection_contains_story_with_matching_title(self):
        def respond(req,**kw):
            if '/pl.cgi?' in req.full_url:
                html=self.fixture('publication.html').replace(b'NOVEL',b'COLLECTION')
            else:
                html=self.edge_title(authors=('Contained Writer',)).replace(b'NOVEL',b'SHORTFICTION').replace(b'ea.cgi?42',b'ea.cgi?43')
            return self.response(html,req.full_url)
        with patch.object(objects,'urlopen',side_effect=respond):
            data=self.identify(identifiers={'isfdb':'202','isfdb-title':'101'})
        self.assertEqual(data[0].authors,['Ada Example'])

    def test_phase9_template_failure_logs_and_retains_original(self):
        self.prefs['title_template']='{title} {series_index:bad}'
        with patch.object(objects,'urlopen',return_value=self.response(self.edge_title(series=True))):
            data=self.identify(identifiers={'isfdb-title':'101'})
        self.assertEqual(data[0].title,'The Offline Star')
        self.assertTrue(any('title template' in str(call) for call in self.log.error.call_args_list))

    def test_phase9_optional_type_and_template(self):
        for template in ('{title}', '{title} - {authors}', '{series_index:bad}'):
            with self.subTest(template=template):
                self.prefs['title_template'] = template
                html = self.fixture('title.html').replace(b'<b>Type:</b> NOVEL<br>', b'')
                with patch.object(objects, 'urlopen', return_value=self.response(html)):
                    data = self.identify(identifiers={'isfdb-title': '101'})
                self.assertEqual(len(data), 1)
                self.assertNotIn('None', data[0].title)

    def test_phase9_decimal_indices(self):
        for text, expected in [('1', 1), ('1.5', 1.5), ('2.25', 2.25), ('IV', 4), ('61/62', 61)]:
            with self.subTest(text=text):
                html = self.edge_title(series=True).replace(b'Series Number:</b> 2', ('Series Number:</b> '+text).encode())
                with patch.object(objects, 'urlopen', return_value=self.response(html)):
                    data = objects.Title.from_url(None, objects.Title.url_from_id('101'), 30, self.log, self.prefs)
                self.assertEqual(data['series_index'], expected)

    def test_phase9_container_credits(self):
        def respond(req, **kw):
            html = self.fixture('publication.html').replace(b'The Offline Star', b'Offline Anthology').replace(b'<b>Author:</b>', b'<b>Editor:</b>').replace(b'NOVEL', b'ANTHOLOGY') if '/pl.cgi?' in req.full_url else self.edge_title(authors=('Story Writer',)).replace(b'ea.cgi?42', b'ea.cgi?43')
            return self.response(html, req.full_url)
        with patch.object(objects, 'urlopen', side_effect=respond):
            data = self.identify(identifiers={'isfdb':'202', 'isfdb-title':'101'})
        self.assertEqual(data[0].authors, ['Ada Example (editor)'])

    def test_phase9_series_pair_precedence(self):
        cases = [({'series':'Cycle','series_index':2}, {}, 'Cycle', 2),
                 ({'series':'Cycle','series_index':2}, {'series':'Pub','series_index':3}, 'Pub', 3),
                 ({'series':'Cycle','series_index':2}, {'series':'Cycle'}, 'Cycle', None),
                 ({'series_index':2}, {}, None, None)]
        cases += [({}, {'series':'Pub','series_index':3}, 'Pub',3),
                  ({'series':'Cycle','series_index':2},{'series':'Cycle','series_index':5},'Cycle',5),
                  ({'series':'Parent.Child','series_index':2},{},'Parent.Child',2),
                  ({'series':'Cycle'},{},'Cycle',None),
                  ({'series':'Cycle','series_index':2},{'series_index':9},'Cycle',2)]
        for title_series, pub_series, name, index in cases:
            with self.subTest(title=title_series, publication=pub_series):
                pub = dict(isfdb='202', title='The Offline Star', authors=['Ada Example'], tags=[], series='')
                pub.update(pub_series)
                tit = dict(title='The Offline Star', authors=['Ada Example'], tags=[], publications=['202'])
                tit.update(title_series)
                with patch.object(objects.Publication,'from_url',return_value=pub), patch.object(objects.Title,'from_url',return_value=tit):
                    data = self.identify(identifiers={'isfdb':'202', 'isfdb-title':'101'})
                self.assertEqual(data[0].series or None, name)
                if index is not None:
                    self.assertEqual(data[0].series_index,index)
                else:
                    self.assertIsNone(data[0].series_index)

