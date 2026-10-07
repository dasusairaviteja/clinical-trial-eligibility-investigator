"""Generate deterministic SHA-256 inventory of tracked, redistributable source."""
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    paths=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
    entries={}
    for name in sorted(p for p in paths if p):
        path=Path(name)
        if path.is_symlink():raise ValueError('release symlinks require explicit review')
        if path.name.startswith('.env') and path.name!='.env.example':raise ValueError('secret file in release')
        entries[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    print(json.dumps({'schema_version':1,'algorithm':'sha256','files':entries},sort_keys=True,indent=2))


if __name__=='__main__':main()
