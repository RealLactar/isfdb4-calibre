"""Phase 9B local reliability regressions; inherited GPLv3 notices apply."""
from unittest.mock import Mock, patch
from threading import Event
from queue import Queue
from calibre_plugins.isfdb4 import objects
import calibre_plugins.isfdb4 as module


class Reliability:
    def test_phase9b_canonical_match_identity_and_editions(self):
        matches=module.RecordMatches()
        for pair in [('http://isfdb.org/cgi-bin/pl.cgi?0202',2),
                     ('https://www.isfdb.org/cgi-bin/pl.cgi?202&view=1',0),
                     ('https://www.isfdb.org/cgi-bin/pl.cgi?203',1),
                     ('https://www.isfdb.org/cgi-bin/title.cgi?101',1),
                     ('http://www.isfdb.org/cgi-bin/title.cgi?101#x',2)]:
            matches.add(pair)
        self.assertEqual(len(matches),3)
        self.assertEqual(list(matches),[(objects.Publication.url_from_id('202'),0),
                (objects.Publication.url_from_id('203'),1),(objects.Title.url_from_id('101'),1)])

    def test_phase9b_cover_isbn_cache_after_publication_lookup(self):
        def respond(req,**kw):
            html=self.fixture('publication.html') if '/pl.cgi?' in req.full_url else self.fixture('title.html')
            if '/pl.cgi?' in req.full_url:
                html=html.replace(b'</ul>', b'<li><b>ISBN:</b> 0-306-40615-2 [978-0-306-40615-7]</li></ul>')
                html=html.replace(b'<div id="content">',b'<div id="content"><table><tr><td><a><img src="https://covers.example/202.jpg"></a></td></tr></table>')
            return self.response(html,req.full_url)
        with patch.object(objects,'urlopen',side_effect=respond):
            data=self.identify(identifiers={'isfdb':'202','isfdb-title':'101'})
        self.assertEqual(len(data),1)
        self.assertEqual(self.plugin.get_cached_cover_url({'isbn':'9780306406157'}),'https://covers.example/202.jpg')
        self.assertEqual(self.plugin.get_cached_cover_url({'isbn-10':'0306406152'}),'https://covers.example/202.jpg')

    def test_phase9b_concurrent_exact_and_normal_settings(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        barrier=Barrier(2); seen=[]
        before=dict(self.prefs)
        self.prefs['search_publications']=False
        before=dict(self.prefs)
        def search(browser,query,timeout,log,prefs):
            barrier.wait(timeout=5)
            seen.append(prefs['exact_search'])
            return []
        with patch.object(objects.TitleList,'from_url',side_effect=search):
            with ThreadPoolExecutor(2) as executor:
                jobs=[executor.submit(self.identify,title=title,authors=['Ada Example']) for title in ('=Book','Book')]
                self.assertEqual([job.result(timeout=10) for job in jobs],[[],[]])
        self.assertEqual(sorted(seen),[False,True]); self.assertEqual(dict(self.prefs),before)

    def test_phase9b_cancel_while_preparing_workers(self):
        abort=Event()
        stub=[{'url':objects.Publication.url_from_id(n)} for n in ('202','203')]
        def prepare(*args,**kwargs):
            abort.set(); return Mock(is_alive=Mock(return_value=False))
        with patch.object(objects.PublicationsList,'from_url',return_value=stub),patch.object(module,'Worker',side_effect=prepare) as worker:
            self.plugin.identify(self.log,Queue(),abort,identifiers={'isbn':'0330020420'})
        self.assertEqual(worker.call_count,1)

    def test_phase9b_cover_empty_and_multiple(self):
        for body, expected in [(b'<html><body></body></html>',[]),
              (b'<div id="main"><a><img src="https://covers.example/a.jpg"></a><a><img src="https://covers.example/b.jpg"></a></div>',
               ['https://covers.example/a.jpg','https://covers.example/b.jpg'])]:
            with self.subTest(expected=expected),patch.object(objects,'urlopen',return_value=self.response(body)),patch.object(self.plugin,'download_multiple_covers') as download:
                self.plugin.download_cover(self.log,Queue(),Event(),identifiers={'isfdb-title':'101'})
                if expected:self.assertEqual(download.call_args.args[2],expected)
                else:download.assert_not_called()

    def test_phase9b_cover_after_author_identification(self):
        from calibre.ebooks.metadata.book.base import Metadata
        mi=Metadata('Book',['Ada']); mi.set_identifier('isfdb-title','101')
        def identify(log,queue,*args): queue.put(mi)
        with patch.object(self.plugin,'identify',side_effect=identify),patch.object(objects.TitleCovers,'from_url',return_value=['https://covers.example/a.jpg']),patch.object(self.plugin,'download_multiple_covers') as download:
            self.plugin.download_cover(self.log,Queue(),Event(),authors=['Ada'])
        self.assertEqual(download.call_args.args[2],['https://covers.example/a.jpg'])

    def test_phase9b_partial_worker_failure_preserves_success(self):
        self.prefs['max_results']=2
        stubs=[{'url':objects.Publication.url_from_id(n)} for n in ('202','203')]
        good={'isfdb':'202','title':'Book','authors':['Ada'],'tags':[],'type':'NOVEL'}
        def publication(browser,url,*args):
            if url.endswith('203'):raise TimeoutError('offline partial failure')
            return dict(good)
        with patch.object(objects.PublicationsList,'from_url',return_value=stubs),patch.object(objects.Publication,'from_url',side_effect=publication),patch.object(objects.TitleList,'from_url',return_value=[]):
            data=self.identify(identifiers={'isbn':'0330020420'})
        self.assertEqual([mi.identifiers['isfdb'] for mi in data],['202'])
        self.log.exception.assert_called()
    def test_phase9b_cross_strategy_duplicate_workers(self):
        self.prefs['search_publications']=True
        stub={'title':'The Offline Star','url':objects.Title.url_from_id('101'),'date':'1965'}
        def respond(req,**kw):
            return self.response(self.fixture('publication.html') if '/pl.cgi?' in req.full_url else self.fixture('title.html'),req.full_url)
        with patch.object(objects.PublicationsList,'from_url',side_effect=[[{'url':objects.Publication.url_from_id('202')}],[]]), patch.object(objects.TitleList,'from_url',return_value=[stub]),patch.object(objects,'urlopen',side_effect=respond) as fetch:
            data=self.identify(title='The Offline Star',authors=['Ada Example'],identifiers={'isbn':'0330020420'})
        self.assertEqual(sum(m.identifiers.get('isfdb')=='202' for m in data),1)
        self.assertEqual(sum('/pl.cgi?' in c.args[0].full_url for c in fetch.call_args_list),1)
        self.assertTrue(any(m.identifiers.get('isfdb-title')=='101' and not m.identifiers.get('isfdb') for m in data))

    def test_phase9b_pre_cancelled_identifiers(self):
        abort=Event(); abort.set(); queue=Queue()
        with patch.object(objects,'urlopen') as fetch:
            self.plugin.identify(self.log,queue,abort,identifiers={'isfdb-title':'101'})
        fetch.assert_not_called(); self.assertTrue(queue.empty())

    def test_phase9b_request_preferences_do_not_persist(self):
        before=dict(self.prefs)
        with patch.object(objects,'urlopen',return_value=self.response(self.fixture('title.html'))):
            self.identify(title='=The Offline Star',identifiers={'isfdb-title':'101'})
        self.assertEqual(dict(self.prefs),before)

    def test_phase9b_fallback_preferences_do_not_persist(self):
        before=dict(self.prefs)
        query=objects.TitleList.url_from_title_and_author('The Offline Star','Ada Example',self.log,self.prefs)
        with patch.object(objects,'urlopen',side_effect=[self.response(self.fixture('restricted_search.html')),self.response(self.fixture('simple_search.html'))]):
            self.assertEqual(len(objects.TitleList.from_url(None,query,30,self.log,self.prefs)),1)
        self.assertEqual(dict(self.prefs),before)

    def test_phase9b_cancel_during_read_drops_late_result(self):
        abort=Event(); queue=Queue()
        response=self.response(self.fixture('title.html'))
        def read():
            abort.set(); return self.fixture('title.html')
        response.read.side_effect=read
        with patch.object(objects,'urlopen',return_value=response):
            self.plugin.identify(self.log,queue,abort,identifiers={'isfdb-title':'101'})
        self.assertTrue(queue.empty())
        self.log.exception.assert_not_called()

    def test_phase9b_cover_cached_publication_and_limits(self):
        self.plugin.cache_identifier_to_cover_url('202','https://covers.example/202.jpg')
        with patch.object(self.plugin,'download_multiple_covers') as download, patch.object(objects,'urlopen') as fetch:
            self.plugin.download_cover(self.log,Queue(),Event(),identifiers={'isfdb':'202'})
        fetch.assert_not_called()
        self.assertEqual(download.call_args.args[2],['https://covers.example/202.jpg'])
        self.assertIsNone(self.plugin.get_cached_cover_url({'isfdb':'203','isbn':'0330020420'}))

    def test_phase9b_title_cover_dedup_and_limit(self):
        self.prefs['max_covers']=1
        html=b'<div id="main"><a><img src="https://covers.example/a.jpg"></a><a><img src="https://covers.example/a.jpg"></a><a><img src="https://covers.example/b.jpg"></a></div>'
        with patch.object(objects,'urlopen',return_value=self.response(html)),patch.object(self.plugin,'download_multiple_covers') as download:
            self.plugin.download_cover(self.log,Queue(),Event(),identifiers={'isfdb-title':'101'})
        self.assertEqual(download.call_args.args[2],['https://covers.example/a.jpg'])

    def test_phase9b_pre_cancelled_cover(self):
        abort=Event(); abort.set()
        with patch.object(objects,'urlopen') as fetch,patch.object(self.plugin,'download_multiple_covers') as download:
            self.plugin.download_cover(self.log,Queue(),abort,identifiers={'isfdb-title':'101'})
        fetch.assert_not_called(); download.assert_not_called()

    def test_phase9b_fallback_childless_root_has_no_future_warning(self):
        import warnings
        query=objects.TitleList.url_from_title_and_author('Book','Ada',self.log,self.prefs)
        with warnings.catch_warnings(),patch.object(objects,'urlopen',side_effect=[self.response(self.fixture('restricted_search.html')),self.response(b'<p>No results</p>')]):
            warnings.simplefilter('error',FutureWarning)
            self.assertEqual(objects.TitleList.from_url(None,query,30,self.log,self.prefs),[])

    def test_phase9b_error_and_cancel_preserve_preferences(self):
        before=dict(self.prefs)
        with patch.object(objects,'urlopen',side_effect=TimeoutError('offline')):
            self.assertEqual(self.identify(identifiers={'isfdb-title':'101'}),[])
        abort=Event(); abort.set()
        self.plugin.identify(self.log,Queue(),abort,title='=Book')
        self.assertEqual(dict(self.prefs),before)

    def test_phase9b_worker_copies_request_preferences(self):
        prefs={'log_level':'DEBUG','exact_search':False}
        worker=module.Worker(objects.Title.url_from_id('101'),Queue(),self.plugin.browser,self.log,0,self.plugin,prefs)
        worker.prefs['exact_search']=True
        self.assertFalse(prefs['exact_search'])

    def test_phase9b_duplicate_candidates_do_not_consume_limit(self):
        self.prefs['max_results']=2
        stubs=[{'url':url} for url in ['http://isfdb.org/cgi-bin/pl.cgi?202',
                'https://www.isfdb.org/cgi-bin/pl.cgi?202#extra',objects.Publication.url_from_id('203')]]
        def publication(browser,url,*args):
            return {'isfdb':url.rsplit('?',1)[1],'title':'Book','authors':['Ada'],'tags':[],'type':'NOVEL'}
        with patch.object(objects.PublicationsList,'from_url',return_value=stubs),patch.object(objects.Publication,'from_url',side_effect=publication),patch.object(objects.TitleList,'from_url',return_value=[]):
            data=self.identify(identifiers={'isbn':'0330020420'})
        self.assertEqual([mi.identifiers['isfdb'] for mi in data],['202','203'])

    def test_phase9b_cancel_cover_read_does_not_download(self):
        abort=Event(); response=self.response(b'<html></html>')
        def read():abort.set(); return b'<html></html>'
        response.read.side_effect=read
        with patch.object(objects,'urlopen',return_value=response),patch.object(self.plugin,'download_multiple_covers') as download:
            self.plugin.download_cover(self.log,Queue(),abort,identifiers={'isfdb-title':'101'})
        download.assert_not_called(); self.log.exception.assert_not_called()

    def test_phase9b_explicit_notes_issue_keeps_user_preference(self):
        html=self.fixture('publication.html').replace(b'</ul>',b'<li><b>Notes:</b><div class="notes">Vol. 4, No. 3. Issue 22</div></li></ul>')
        before=dict(self.prefs)
        with patch.object(objects,'urlopen',return_value=self.response(html)):
            data=objects.Publication.from_url(None,objects.Publication.url_from_id('202'),30,self.log,self.prefs)
        self.assertEqual(data['series_index'],22)
        self.assertEqual(dict(self.prefs),before)

    def test_phase9b_external_asin_locale_fallback(self):
        html=self.fixture('publication.html').replace(b'</ul>',b'<li><b>External IDs:</b><ul><li><abbr>ASIN</abbr>: <a href="https://www.amazon.com/dp/B000000001?tag=example">US</a><a href="https://www.amazon.co.uk/dp/B000000001">GB</a></li></ul></li></ul>')
        with patch.object(objects,'urlopen',return_value=self.response(html)),patch.object(objects,'LOCALE_COUNTRY','ZZ'):
            data=objects.Publication.from_url(None,objects.Publication.url_from_id('202'),30,self.log,self.prefs)
        self.assertEqual(data['identifiers']['asin'],'B000000001')

    def test_phase9b_title_tags_are_extracted(self):
        html=self.fixture('title.html').replace(b'<b>Language:',b'<b>Current Tags:</b> <a href="https://www.isfdb.org/cgi-bin/tag.cgi?1">space travel</a> (1)<br><b>Language:')
        with patch.object(objects,'urlopen',return_value=self.response(html)):
            data=self.identify(identifiers={'isfdb-title':'101'})
        self.assertIn('Space Travel',data[0].tags)

    def test_phase9b_active_request_cancellation_and_cleanup(self):
        from threading import Thread
        started=Event(); release=Event(); abort=Event(); queue=Queue(); workers=[]
        real_worker=module.Worker
        def worker(*args,**kwargs):
            value=real_worker(*args,**kwargs); workers.append(value); return value
        response=self.response(self.fixture('publication.html'))
        def read():
            started.set()
            if not release.wait(5):raise AssertionError('test release not signalled')
            return self.fixture('publication.html')
        response.read.side_effect=read
        invocation=Thread(target=self.plugin.identify,args=(self.log,queue,abort),kwargs={'identifiers':{'isfdb':'202'}})
        with patch.object(objects,'urlopen',return_value=response) as fetch,patch.object(module,'Worker',side_effect=worker):
            try:
                invocation.start(); self.assertTrue(started.wait(3)); abort.set()
                invocation.join(3); self.assertFalse(invocation.is_alive())
                self.assertTrue(workers[0].is_alive())
            finally:
                release.set(); invocation.join(3)
                for value in workers:value.join(3)
        self.assertTrue(all(not value.is_alive() for value in workers))
        self.assertEqual(fetch.call_count,1); self.assertTrue(queue.empty())
        self.log.exception.assert_not_called()

    def test_phase9b_inherited_cover_downloader_raw_bytes_contract(self):
        import io
        from PIL import Image
        buffer=io.BytesIO(); Image.new('RGB',(320,480),'blue').save(buffer,format='PNG')
        image=buffer.getvalue()
        # Source's downloader transports raw bytes; decoding is a later contract.
        # Do not mistake that API boundary for image validation in this plugin.
        for body in (image,b'not an image'):
            with self.subTest(image_bytes=(body==image)):
                queue=Queue()
                browser=self.plugin.browser
                response=Mock(read=Mock(return_value=body))
                from unittest.mock import PropertyMock
                import sys
                errors=[]
                self.log.exception.side_effect=lambda *args:errors.append(repr(sys.exc_info()[1]))
                with patch.object(module.ISFDB4,'browser',new_callable=PropertyMock,return_value=browser),patch.object(browser,'open_novisit',return_value=response),patch.object(browser,'open',return_value=response),patch.object(browser,'clone_browser',return_value=browser):
                    self.plugin.download_multiple_covers('Book',['Ada'],['https://covers.example/a.png'],False,30,queue,Event(),self.log)
                self.assertFalse(queue.empty(),str(errors))
                self.assertEqual(queue.get()[1],body)

    def test_phase9b_active_cover_download_cancellation(self):
        from unittest.mock import PropertyMock
        abort=Event(); queue=Queue(); browser=self.plugin.browser
        response=Mock()
        def read():abort.set(); return b'late cover bytes'
        response.read.side_effect=read
        self.plugin.cache_identifier_to_cover_url('202','https://covers.example/a.png')
        with patch.object(module.ISFDB4,'browser',new_callable=PropertyMock,return_value=browser),patch.object(browser,'open',return_value=response),patch.object(browser,'open_novisit',return_value=response),patch.object(browser,'clone_browser',return_value=browser):
            self.plugin.download_cover(self.log,queue,abort,identifiers={'isfdb':'202'})
        self.assertTrue(queue.empty())
