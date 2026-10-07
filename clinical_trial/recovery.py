"""Offline verified backup/restore. Stop the server before restoring."""
import argparse
import json
import os
from pathlib import Path
from .reviews import ReviewStore


def snapshot(source, target):
    source, target = Path(source), Path(target)
    if not source.is_file() or target.exists() or source.resolve() == target.resolve():
        raise ValueError("existing source and new destination required")
    # Exclusive creation prevents overwriting a user file.
    descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        store = ReviewStore(source, read_only=True)
        expected = store.verify()
        store.backup(target)
        actual = ReviewStore(target, read_only=True).verify()
        if expected != actual:
            raise ValueError("source changed during backup; retry")
        return actual
    except Exception:
        target.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("backup", "restore", "verify"))
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, nargs="?")
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error("source must exist")
    if args.action == "verify":
        result = ReviewStore(args.source, read_only=True).verify()
    else:
        if args.destination is None:
            parser.error("destination required; restore into a new file then switch configuration")
        result = snapshot(args.source, args.destination)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
