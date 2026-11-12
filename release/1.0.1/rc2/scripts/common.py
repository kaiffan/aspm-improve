"""Private configuration stays outside Git; only allowlisted evidence is public."""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT.parent / 'aspm-rc2-private'
SOURCE = '25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb'
PROJECT = 'aspm-rc2'
WEB = PROJECT + '-aspm-1'
PG = 'django-defectdojo-postgres-1'
VARIANTS = {
    'round5': ('dd-r5-final:3.5.100', 'aspm-rc2-r5-static:3.5.100', 'c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37'),
    'rc1': ('aspm-build:5cdbc77fc9d4', 'aspm-nginx-build:5cdbc77fc9d4', '5cdbc77fc9d4b8d0899069f5d44cd5241b2acae6'),
    'rc2': ('aspm-build:25fb63ae7b48', 'aspm-nginx-build:25fb63ae7b48', SOURCE),
}


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, **kwargs)


def output(argv):
    return subprocess.check_output(argv, text=True).strip()


def save(path, value, private=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    if private:
        path.chmod(0o600)


def compose(*args, test=False, **kwargs):
    return run(['docker', 'compose', '-p', 'dd-final-tests' if test else PROJECT,
                '-f', str(PRIVATE / ('tests.compose.json' if test else 'compose.json')), *args], **kwargs)


def shell(code, data=None, container=WEB, **kwargs):
    return subprocess.check_output(['docker', 'exec', '-i', container, 'python', 'manage.py',
                                    'shell', '-c', code], input=data, stderr=subprocess.DEVNULL, **kwargs)


def pg(sql, db='source'):
    return output(['docker', 'exec', '-e', 'RC2_SQL='+sql, '-e', 'RC2_DB='+('' if db == 'source' else db),
                   PG, 'sh', '-c', 'PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=180000 -c TimeZone=UTC -c DateStyle=ISO,MDY" psql -X -U "$POSTGRES_USER" -d "${RC2_DB:-$POSTGRES_DB}" -Atc "$RC2_SQL"'])


def app_config(variant, database, instrument=False, cache_prefix='rc2-demo'):
    config = json.loads((PRIVATE / 'base.compose.json').read_text())
    app, static, sha = VARIANTS[variant]
    env = config['services']['aspm']['environment']
    from urllib.parse import urlsplit, urlunsplit
    parsed = urlsplit(env['DD_DATABASE_URL'])
    env['DD_DATABASE_URL'] = urlunsplit(parsed._replace(path='/'+database))
    env['DD_FINAL_CACHE_PREFIX'] = cache_prefix
    env['DD_DEBUG'] = 'False'
    # These are the exact frozen image's own metadata, never a different HEAD.
    env.pop('DD_ASPM_GIT_SHA', None)
    env.pop('DD_ASPM_BUILD_TIMESTAMP', None)
    config['services']['aspm']['image'] = app
    config['services']['nginx']['image'] = static
    settings_dir = PRIVATE / ('instrumented' if instrument else 'demo')
    config['services']['aspm']['volumes'][1] = str(settings_dir)+':/app/docker/extra_settings:ro'
    if database == 'dd_round4_seed':
        config['services']['aspm']['volumes'][0] += ':ro'
    save(PRIVATE / 'compose.json', config, private=True)
    return config


def ready():
    import http.client
    import time
    for _ in range(100):
        try:
            conn = http.client.HTTPConnection('127.0.0.1', 48091, timeout=3)
            conn.request('GET', '/login?force_login_form')
            response = conn.getresponse()
            response.read()
            conn.close()
            if response.status == 200:
                return
        except (OSError, http.client.HTTPException):
            pass
        time.sleep(1)
    raise RuntimeError('RC2 gateway did not become ready')


def switch(variant, database='dd_round4_seed', instrument=True, prefix='rc2-load'):
    config = app_config(variant, database, instrument, prefix)
    log = (OUT / 'raw' / 'controller.log').open('a')
    compose('up', '-d', 'rc2-cache', 'aspm', 'nginx', stdout=log, stderr=log)
    # Nginx must resolve the new application IP after container replacement.
    compose('restart', 'nginx', stdout=log, stderr=log)
    ready()
    actual = output(['docker', 'inspect', '--format', '{{.Image}}', WEB])
    expected = output(['docker', 'image', 'inspect', '--format', '{{.Id}}', config['services']['aspm']['image']])
    assert actual == expected, 'Unexpected running source image'
    log.close()
    return actual
