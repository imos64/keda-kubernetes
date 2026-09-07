from pathlib import Path
import os,subprocess,sys,urllib.request,concurrent.futures
r=Path(__file__).resolve().parents[1]
env=dict(os.environ,BIND='127.0.0.1',PORT='0')
p=subprocess.Popen([sys.executable,str(r/'demo/app.py')],env=env,stdout=subprocess.PIPE,text=True)
try:
    port=int(p.stdout.readline());base=f'http://127.0.0.1:{port}'
    def get(path):
        with urllib.request.urlopen(base+path,timeout=10) as resp:return resp.read().decode()
    assert get('/healthz')=='ok\n'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:
        assert all(x=='work complete\n' for x in e.map(get,['/work']*8))
    assert 'demo_requests_total 8\n' in get('/metrics')
    print('PASS: real HTTP health, concurrent CPU work and Prometheus counter. Autoscaling itself was not run.')
finally:
    p.terminate();p.wait(timeout=10)
