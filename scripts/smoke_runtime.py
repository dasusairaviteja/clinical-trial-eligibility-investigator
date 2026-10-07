"""Exercise the real Gunicorn process with ephemeral synthetic credentials/data."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def main():
    with tempfile.TemporaryDirectory() as directory:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port = sock.getsockname()[1]
        token = secrets.token_urlsafe(32)
        env = {**os.environ,'REVIEWER_TOKENS_JSON':json.dumps({token:'smoke-reviewer'}),
               'REVIEW_DATABASE':str(Path(directory)/'reviews.db'),'ENABLE_AZURE_MODEL':'false'}
        process = subprocess.Popen([sys.executable,'-m','gunicorn','-c','gunicorn.conf.py',
                                    '--bind',f'127.0.0.1:{port}','clinical_trial.wsgi:create_app()'],
                                   env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def call(path, body=None, auth=True):
            headers = {'Authorization':'Bearer '+token} if auth else {}
            if body is not None: headers['Content-Type']='application/json'
            request = Request(f'http://127.0.0.1:{port}'+path,
                              data=json.dumps(body).encode() if body is not None else None,headers=headers)
            with urlopen(request,timeout=5) as response:
                return json.load(response)
        try:
            for _ in range(100):
                try: call('/health',auth=False); break
                except URLError:
                    if process.poll() is not None: raise RuntimeError('runtime exited')
                    time.sleep(.05)
            else: raise RuntimeError('runtime did not start')
            try:
                call('/v1/demo',auth=False)
                raise AssertionError('unauthenticated request accepted')
            except HTTPError as error:
                assert error.code == 401
            report = call('/v1/investigate',call('/v1/demo'))
            assert call('/v1/reports/'+report['id']) == report
            assert call('/v1/me')['reviewer'] == 'smoke-reviewer'
            print('Gunicorn smoke: health, authentication, investigation and persistence passed')
        finally:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); process.wait()


if __name__ == '__main__': main()
