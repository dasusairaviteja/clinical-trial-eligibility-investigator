"""CI-only container readiness/auth persistence check; no cloud resources."""
import json
import secrets
import subprocess
import time
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError


def main():
    token=secrets.token_urlsafe(32)
    name='triallens-smoke-'+secrets.token_hex(4)
    subprocess.run(['docker','run','-d','--name',name,'--read-only','--cap-drop=ALL',
                    '--security-opt=no-new-privileges','--tmpfs','/tmp','--tmpfs','/data:uid=10001,gid=10001',
                    '-p','127.0.0.1:18765:8000','-e','REVIEWER_TOKENS_JSON='+json.dumps({token:'container-reviewer'}),
                    'triallens:ci'],check=True,stdout=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urlopen('http://127.0.0.1:18765/health',timeout=2) as response:
                    assert json.load(response)['status']=='ok'
                break
            except (URLError,ConnectionError):time.sleep(.1)
        else:raise RuntimeError('container did not become healthy')
        def call(path,body=None):
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
            request=Request('http://127.0.0.1:18765'+path,headers=headers,
                            data=None if body is None else json.dumps(body).encode())
            with urlopen(request,timeout=5) as response:return json.load(response)
        saved=call('/v1/investigate',call('/v1/demo'))
        assert call('/v1/reports/'+saved['id'])==saved
        user=subprocess.check_output(['docker','exec',name,'id','-u'],text=True).strip()
        assert user=='10001'
        print('Container smoke passed: non-root, read-only root, investigation and storage')
    finally:
        subprocess.run(['docker','rm','-f',name],check=True,stdout=subprocess.DEVNULL)


if __name__=='__main__':main()
