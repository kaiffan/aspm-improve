import json,os,platform
import django
from django.conf import settings
from django.db import connection
import rest_framework
import dojo

row={'application_version':getattr(dojo,'__version__',None),'django':django.get_version(),'drf':rest_framework.VERSION,'python':platform.python_version(),
     'debug':settings.DEBUG,'timezone':settings.TIME_ZONE,'conn_max_age':connection.settings_dict.get('CONN_MAX_AGE'),
     'cache_backend':settings.CACHES['default']['BACKEND'],'cache_namespace_isolated':True,
     'uwsgi':{'processes':os.environ.get('DD_UWSGI_NUM_OF_PROCESSES'),'threads':os.environ.get('DD_UWSGI_NUM_OF_THREADS')},
     'features':{name:getattr(settings,name,None) for name in ('V3_FEATURE_LOCATIONS','ENABLE_V3_ORGANIZATION_ASSET_RELABEL')}}
with connection.cursor() as cursor:
    config={}
    for name in ('server_version','shared_buffers','work_mem','max_connections','max_parallel_workers_per_gather','track_io_timing','effective_cache_size'):
        cursor.execute('SHOW '+name);config[name]=cursor.fetchone()[0]
row['postgres']=config
print('CONFIG '+json.dumps(row))
