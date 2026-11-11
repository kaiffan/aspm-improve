#!/usr/bin/env python3
"""Sequential same-port comparison. Credentials stay in a private file outside Git."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
IMAGES = {v: f'dd-final-{v}:3.5.100' for v in ('original', 'current', 'final')}
WEB = 'dd-final-web-1'


def command(argv, **kwargs):
    return subprocess.run(argv, check=True, **kwargs)


def wait_ready(accounts):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        connection = http.client.HTTPConnection('127.0.0.1', 48084, timeout=3)
        try:
            connection.request('GET', '/api/v2/findings/1000000/', headers={'Authorization': 'Token '+accounts[0]['token']})
            response = connection.getresponse()
            response.read()
            if response.status == 200:
                return
        except (OSError, http.client.HTTPException):
            pass
        finally:
            connection.close()
        time.sleep(1)
    raise RuntimeError('Candidate did not become ready')


def switch(variant, args, accounts, log):
    env = os.environ.copy()
    env['DD_FINAL_IMAGE'] = IMAGES[variant]
    env['DD_FINAL_CACHE_PREFIX'] = f'dd-r4-{args.phase}-{variant}-{time.time_ns()}'
    command(['docker', 'compose', '-p', 'dd-final', '-f', str(args.compose), 'up', '-d', 'web'], env=env, stdout=log, stderr=log)
    command(['docker', 'compose', '-p', 'dd-final', '-f', str(args.compose), 'restart', 'nginx'], stdout=log, stderr=log)
    wait_ready(accounts)
    actual = subprocess.check_output(['docker', 'inspect', '--format', '{{.Image}}', WEB], text=True).strip()
    expected = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', IMAGES[variant]], text=True).strip()
    if actual != expected:
        raise RuntimeError('Running image does not match requested variant')
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compose', type=Path, required=True)
    parser.add_argument('--credentials', type=Path, required=True)
    parser.add_argument('--phase', choices=['profile', 'endpoints', 'mixed', 'users'], required=True)
    parser.add_argument('--variants', default='original,current,final')
    parser.add_argument('--levels', default='5,10,15,25')
    parser.add_argument('--cases')
    parser.add_argument('--label-prefix')
    parser.add_argument('--endpoint-concurrency', type=int, default=1)
    parser.add_argument('--requests', type=int)
    parser.add_argument('--repeats', type=int, default=2)
    parser.add_argument('--stop-file', type=Path, required=True)
    args = parser.parse_args()
    if args.stop_file.exists():
        parser.error('Stop-file already exists; inspect its cause before starting another experiment')
    accounts = json.loads(args.credentials.read_text())
    credentials = json.dumps(accounts).encode()
    variants = args.variants.split(',')
    if any(v not in IMAGES for v in variants):
        parser.error('Unknown build')
    raw = ROOT/'raw'
    raw.mkdir(exist_ok=True)
    scenarios = json.loads((ROOT/'scenarios.json').read_text())
    cases = args.cases.split(',') if args.cases else list(scenarios)
    with (raw/(args.phase+'-controller.log')).open('a', buffering=1) as log:
        for rep in range(1, (1 if args.phase == 'profile' else args.repeats)+1):
            order = variants if rep % 2 else list(reversed(variants))
            for variant in order:
                image_id = switch(variant, args, accounts, log)
                label = f'{args.label_prefix or args.phase}-r{rep}-{variant}' if args.phase != 'endpoints' else f'endpoints-e{args.endpoint_concurrency}-r{rep}-{variant}'
                print('START '+label, flush=True)
                if args.phase == 'profile':
                    for name, target in [('profile.py', '/tmp/r4-profile.py'), ('scenarios.json', '/tmp/r4-scenarios.json')]:
                        command(['docker', 'cp', str(ROOT/name), WEB+':'+target], stdout=log, stderr=log)
                    with (raw/(label+'.raw')).open('wb') as output, (raw/(label+'.stderr')).open('wb') as error:
                        command(['docker', 'exec', '-i', '-e', 'DD_FINAL_VARIANT='+variant, WEB, 'python', 'manage.py', 'shell', '-c', "exec(open('/tmp/r4-profile.py').read())"], input=credentials, stdout=output, stderr=error)
                    rows=[];plans=[]
                    for line in (raw/(label+'.raw')).read_text().splitlines():
                        if line.startswith('PROFILE '): rows.append(json.loads(line[8:]))
                        elif line.startswith('PLAN '): plans.append(json.loads(line[5:]))
                    (ROOT/('profile_'+variant+'.json')).write_text(json.dumps(rows, indent=2)+'\n')
                    (ROOT/('explain_'+variant+'.json')).write_text(json.dumps(plans, indent=2)+'\n')
                    print('PROFILE '+variant+' '+str(len(rows))+' responses', flush=True)
                    continue
                monitor_log = (raw/(label+'-metrics.jsonl')).open('wb')
                monitor = subprocess.Popen([sys.executable, str(ROOT/'monitor.py'), str(raw/(label+'-metrics.jsonl')), str(args.stop_file), '4200', WEB], stdout=log, stderr=log)
                command(['docker', 'exec', WEB, 'python', '-c', "from pathlib import Path; Path('/tmp/dd-r4-rss-stop').unlink(missing_ok=True)"], stdout=log, stderr=log)
                rss_log = (raw/(label+'-rss.jsonl')).open('wb')
                rss = subprocess.Popen(['docker', 'exec', '-i', '-e', 'DD_RSS_DURATION=4200', WEB, 'python', '-'], stdin=subprocess.PIPE, stdout=rss_log, stderr=log)
                rss.stdin.write((ROOT/'worker_rss.py').read_bytes())
                rss.stdin.close()
                try:
                    levels = [args.endpoint_concurrency] if args.phase == 'endpoints' else ([25] if args.phase == 'users' else [int(c) for c in args.levels.split(',')])
                    for c in levels:
                        for case in (cases if args.phase == 'endpoints' else ['mixed']):
                            if variant == 'original' and case in {'products_count', 'products_none', 'fast_offset'}:
                                continue
                            output = raw/(f'{label}-c{c}-{case}.json')
                            argv=[sys.executable, str(ROOT/'benchmark.py'), '--variant', variant, '--concurrency', str(c), '--requests', str(args.requests or (40 if args.phase=='endpoints' else 300)), '--warmup', str(5 if args.phase=='endpoints' else 25), '--seconds', '300', '--timeout', '90', '--seed', str(35100+rep), '--scenario', case, '--stop-file', str(args.stop_file), '--output', str(output)]
                            if args.phase == 'endpoints': argv += ['--admin-only']
                            if args.phase == 'users': argv += ['--fixed-users', '--think-time', '0.25']
                            command(argv, input=credentials, stdout=log, stderr=log)
                            result=json.loads(output.read_text());result['image_id']=image_id;result['phase']=args.phase;result['rep']=rep
                            output.write_text(json.dumps(result,indent=2)+'\n')
                            print(f"DONE {label} c={c} {case} n={result['requests']} p95={result['p95_ms']}ms rps={result['rps']}", flush=True)
                            if args.stop_file.exists(): raise RuntimeError('Resource guard stopped the experiment')
                finally:
                    command(['docker', 'exec', WEB, 'touch', '/tmp/dd-r4-rss-stop'], stdout=log, stderr=log)
                    try: rss.wait(timeout=4)
                    except subprocess.TimeoutExpired: rss.terminate()
                    monitor.terminate()
                    try: monitor.wait(timeout=8)
                    except subprocess.TimeoutExpired: monitor.kill()
                    rss_log.close();monitor_log.close()
    return 0


if __name__=='__main__':
    sys.exit(main())
