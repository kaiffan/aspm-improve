"""Server-side page semantics on the isolated copy; credentials only on stdin."""
import json
import sys
from urllib.parse import parse_qs, urlencode, urlsplit
from django.conf import settings
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse

setup_test_environment()
accounts=json.load(sys.stdin)
rows=[]
for role,account in [('admin',accounts[0]),('restricted',accounts[1])]:
    client=Client(HTTP_HOST='localhost')
    client.cookies[settings.SESSION_COOKIE_NAME]=account['session']
    product=account['product']
    cases=[('findings',reverse('open_findings'),'findings','',{'test__engagement__product':product,'severity':'High'}),
           ('product_findings',reverse('product_open_findings',args=[product]),'findings','',{'severity':'High'}),
           ('products','/asset','prod_list','',{}),
           ('engagements','/engagement','engagements','',{}),
           ('test_findings','/test/'+str(account['test']),'findings','findings',{})]
    for name,path,key,prefix,filters in cases:
        def get(state,extra):
            params={**filters,**extra}
            response=client.get(path,params,secure=True)
            assert response.status_code==200,(name,state,response.status_code)
            page=response.context[key]
            ids=[obj.pk for obj in page]
            assert len(ids)==len(set(ids)),(name,state,'duplicates')
            if key=='findings':
                assert all(obj.test.engagement.product_id==product for obj in page),(name,'foreign Product')
            row={'actor':role,'case':name,'state':state,'status':response.status_code,'page':page.number,'pages':page.paginator.num_pages,'count':page.paginator.count,'per_page':page.paginator.per_page,'start':page.start_index(),'end':page.end_index(),'ids':ids}
            rows.append(row)
            return row,response
        first,response=get('first',{})
        assert first['page']==1
        second,_=get('next',{prefix+'page':2})
        if first['pages']>1:assert not set(first['ids'])&set(second['ids'])
        previous,_=get('previous',{prefix+'page':1})
        assert previous['ids']==first['ids']
        last,_=get('last',{prefix+'page':first['pages']})
        assert last['end']==first['count']
        for value,state in [('bad','malformed_page'),('999999999999999','huge_page'),('-1','negative_page')]:
            page,_=get(state,{prefix+'page':value})
            assert page['page']==(1 if value=='bad' else first['pages'])
        fifty,_=get('size_50',{prefix+'page_size':50})
        assert fifty['per_page']==50 and fifty['count']==first['count']
        invalid,_=get('malformed_size',{prefix+'page_size':'bad'})
        assert invalid['per_page']==25 and invalid['count']==first['count']
        for ordering in ['title','-title'] if key=='findings' else ['name','-name']:
            one,_=get('ordered_first_'+ordering,{'o':ordering})
            two,_=get('ordered_next_'+ordering,{'o':ordering,prefix+'page':2})
            assert one['count']==first['count']
            if one['pages']>1:assert not set(one['ids'])&set(two['ids'])
        empty_filter={'title':'ASPM-RC2-absent-namespace-550043'} if key=='findings' else {'name':'ASPM-RC2-absent-namespace-550043'}
        empty,_=get('empty_result',empty_filter)
        assert empty['count']==0 and empty['ids']==[]
print('MATRIX '+json.dumps({'checks':len(rows),'failures':[],'rows':rows}),flush=True)
