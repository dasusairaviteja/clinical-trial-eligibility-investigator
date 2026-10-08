"""Bounded local concurrency probe; not a production capacity benchmark.

Starts the actual Gunicorn runtime with an ephemeral database and random token.
No model calls are enabled. Only summary counts and latency are printed.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    with tempfile.TemporaryDirectory() as directory:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        token = secrets.token_urlsafe(32)
        env = {**os.environ, 'ENABLE_AZURE_MODEL': 'false',
               'REVIEWER_TOKENS_JSON': json.dumps({token: 'concurrency-probe'}),
               'REVIEW_DATABASE': str(Path(directory) / 'reviews.db')}
        process = subprocess.Popen([
            sys.executable, '-m', 'gunicorn', '-c', 'gunicorn.conf.py',
            '--bind', f'127.0.0.1:{port}', 'clinical_trial.wsgi:create_app()'],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def call(path, body=None, key=None):
            headers = {'Authorization': 'Bearer ' + token}
            if key:
                headers['Idempotency-Key'] = key
            if body is not None:
                headers['Content-Type'] = 'application/json'
            request = Request(f'http://127.0.0.1:{port}' + path, headers=headers,
                              data=None if body is None else json.dumps(body).encode())
            start = time.perf_counter()
            try:
                with urlopen(request, timeout=10) as response:
                    status, value = response.status, json.load(response)
            except HTTPError as error:
                status, value = error.code, json.load(error)
            return status, value, (time.perf_counter() - start) * 1000

        try:
            for _ in range(100):
                try:
                    if call('/health')[0] == 200:
                        break
                except URLError:
                    if process.poll() is not None:
                        raise RuntimeError('runtime exited')
                    time.sleep(.05)
            else:
                raise RuntimeError('runtime did not start')
            status, request, _ = call('/v1/demo')
            assert status == 200
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(lambda _: call('/v1/investigate', request), range(24)))
            counts = Counter(status for status, _, _ in results)
            assert counts[200] > 0 and set(counts) <= {200, 503}, counts
            identifiers = [value['id'] for status, value, _ in results if status == 200]
            assert len(identifiers) == len(set(identifiers))
            for status, value, _ in results:
                if status == 200:
                    assert value['report']['status'] == 'human_review_required'
                    assert value['report']['execution']['model_calls'] == 0
                    assert value['revision'] == 0 and len(value['audit']) == 1
            key = 'runtime-replay-check-0001'
            first = call('/v1/investigate', request, key)
            replay = call('/v1/investigate', request, key)
            assert first[0] == replay[0] == 200 and first[1] == replay[1]
            changed = call('/v1/investigate', {**request, 'case_id': 'different-case'}, key)
            assert changed[0] == 409
            latencies = sorted(elapsed for _, _, elapsed in results)
            print(json.dumps({'scope': 'local synthetic concurrency probe',
                'requests': 24, 'concurrency': 4, 'status_counts': dict(counts),
                'latency_p50_ms': round(latencies[11], 3),
                'latency_p95_ms': round(latencies[22], 3),
                'replay_verified': True, 'changed_payload_rejected': True,
                'model_calls': 0}, indent=2))
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    main()
