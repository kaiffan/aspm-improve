import json,re,sys,time
from django.db import connection
from django.test import Client
account=json.load(sys.stdin)[0]
client=Client(HTTP_HOST='localhost',HTTP_AUTHORIZATION='Token '+account['token'],raise_request_exception=False)
for name,url in [('products','/api/v2/products/?limit=100'),('product_detail','/api/v2/products/2/')]:
    client.get(url)
    queries=[]
    def measure(execute,sql,params,many,context):
        start=time.perf_counter()
        try:return execute(sql,params,many,context)
        finally:queries.append((sql,params,(time.perf_counter()-start)*1000))
    with connection.execute_wrapper(measure):response=client.get(url)
    assert response.status_code==200
    for sql,params,ms in sorted(queries,key=lambda q:q[2],reverse=True)[:3]:
        if 'dojo_finding' not in sql or not sql.startswith('SELECT'):continue
        with connection.cursor() as cursor:
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, TIMING OFF) '+sql,params)
            plan='\n'.join(row[0] for row in cursor.fetchall())
        print('PLAN '+json.dumps({'case':name,'query_ms':ms,'sql':re.sub(r"'(?:[^']|'')*'","'?'",sql),'plan':plan}),flush=True)
