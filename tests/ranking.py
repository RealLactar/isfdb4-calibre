"""Phase 9F ranking; simple-search rows captured publicly 2026-11-05.

The eternity fixture retains five real Asimov rows, not an advanced-search
layout. Metadata bodies used below are explicit controlled test doubles.
"""
from unittest.mock import patch
from calibre_plugins.isfdb4 import objects


class Ranking:
    def eternity_stubs(self):
        query=objects.TitleList.url_from_title_and_author('The End of Eternity','Isaac Asimov',self.log,self.prefs)
        with patch.object(objects,'urlopen',side_effect=[self.response(self.fixture('restricted_search.html')),self.response(self.fixture('eternity_simple_search.html'))]):
            return objects.TitleList.from_url(None,query,30,self.log,self.prefs)

    def ranked_lookup(self,stubs,title,authors=None,limit=1):
        self.prefs['max_results']=limit;self.prefs['search_publications']=False
        def metadata(browser,url,*args):
            stub=next(s for s in stubs if s['url']==url)
            return {'title':stub['title'],'authors':['Isaac Asimov'],'isfdb-title':url.rsplit('?',1)[1],'tags':[],'publications':[],'language':'eng'}
        with patch.object(objects.TitleList,'from_url',return_value=stubs),patch.object(objects.Title,'from_url',side_effect=metadata):
            return self.identify(title=title,authors=authors)

    def test_phase9f_real_candidate_discovery(self):
        stubs=self.eternity_stubs()
        self.assertEqual([s['url'].rsplit('?',1)[1] for s in stubs],['954264','72841','2009','691469','954263'])
        self.assertEqual(sorted(stubs,key=lambda s:s['date'])[0]['url'].rsplit('?',1)[1],'691469')

    def test_phase9f_exact_novel_before_excerpt_limit_one(self):
        data=self.ranked_lookup(self.eternity_stubs(),'The End of Eternity',['Isaac Asimov'])
        self.assertEqual([m.identifiers['isfdb-title'] for m in data],['2009'])
        self.assertEqual(data[0].source_relevance,0)

    def test_phase9f_title_only_exact_before_partial(self):
        data=self.ranked_lookup(self.eternity_stubs(),'The End of Eternity')
        self.assertEqual(data[0].identifiers['isfdb-title'],'2009')

    def test_phase9f_partial_records_retained_at_larger_limit(self):
        data=self.ranked_lookup(self.eternity_stubs(),'The End of Eternity',['Isaac Asimov'],3)
        self.assertEqual([m.identifiers['isfdb-title'] for m in data],['2009','691469','954263'])
        self.assertEqual([m.source_relevance for m in data],[0,2,2])

    def test_phase9f_explicit_excerpt_is_valid_exact_work(self):
        data=self.ranked_lookup(self.eternity_stubs(),'The End of Eternity (excerpt)',['Isaac Asimov'])
        self.assertEqual(data[0].identifiers['isfdb-title'],'691469')

    def test_phase9f_distinct_numbered_titles_not_conflated(self):
        stubs=[{'title':'Volume 1','date':'1900','url':objects.Title.url_from_id('101')},
               {'title':'Volume 2','date':'2000','url':objects.Title.url_from_id('102')}]
        data=self.ranked_lookup(stubs,'Volume 2',['Isaac Asimov'])
        self.assertEqual(data[0].identifiers['isfdb-title'],'102')

    def test_phase9f_publication_exact_title_before_older_partial(self):
        self.prefs['max_results']=1;self.prefs['search_titles']=False
        stubs=[{'title':'Book (excerpt)','pub_year':'1900','url':objects.Publication.url_from_id('202')},
               {'title':'Book','pub_year':'2000','url':objects.Publication.url_from_id('203')}]
        def publication(browser,url,*args):
            return {'title':'Book' if url.endswith('203') else 'Book (excerpt)','isfdb':url.rsplit('?',1)[1],
                    'authors':['Ada'],'tags':[],'type':'NOVEL'}
        with patch.object(objects.PublicationsList,'from_url',return_value=stubs),patch.object(objects.Publication,'from_url',side_effect=publication),patch.object(objects.TitleList,'from_url',return_value=[]):
            data=self.identify(title='Book',authors=['Ada'])
        self.assertEqual([m.identifiers['isfdb'] for m in data],['203'])

    def test_phase9f_no_exact_match_keeps_date_precedence(self):
        stubs=[{'title':'Book Part Two','date':'2000','url':objects.Title.url_from_id('102')},
               {'title':'Book Part One','date':'1900','url':objects.Title.url_from_id('101')}]
        data=self.ranked_lookup(stubs,'Book',['Isaac Asimov'])
        self.assertEqual(data[0].identifiers['isfdb-title'],'101')
        self.assertEqual(data[0].source_relevance,2)

    def test_phase9f_mixed_editions_and_duplicate_links_survive(self):
        self.prefs['max_results']=4;self.prefs['search_publications']=True
        stubs=self.eternity_stubs()[:0]+[
            {'title':'Book (excerpt)','date':'1900','url':objects.Title.url_from_id('101')},
            {'title':'Book','date':'2000','url':objects.Title.url_from_id('102')}]
        def title(browser,url,*args):
            exact=url.endswith('102')
            return {'title':'Book' if exact else 'Book (excerpt)','isfdb-title':'102' if exact else '101','authors':['Ada'],'tags':[],
                    'publications':['202','202','203'] if exact else []}
        def publication(browser,url,*args):
            return {'title':'Book','isfdb':url.rsplit('?',1)[1],'authors':['Ada'],'tags':[]}
        with patch.object(objects.TitleList,'from_url',return_value=stubs),patch.object(objects.Title,'from_url',side_effect=title),patch.object(objects.Publication,'from_url',side_effect=publication),patch.object(objects.PublicationsList,'from_url',return_value=[]):
            data=self.identify(title='Book',authors=['Ada'])
        self.assertEqual(len(data),4)
        self.assertEqual({m.identifiers.get('isfdb') for m in data if m.identifiers.get('isfdb')},{'202','203'})
        self.assertEqual({m.identifiers.get('isfdb-title') for m in data if not m.identifiers.get('isfdb')},{'101','102'})
