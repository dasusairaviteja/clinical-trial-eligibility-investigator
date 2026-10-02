"""Reject tracked local secrets files without opening their contents."""
from pathlib import PurePosixPath
import subprocess


def main() -> int:
    files = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    forbidden = [name for name in files if name and
        (PurePosixPath(name).name == ".env" or
         (PurePosixPath(name).name.startswith(".env.") and
          PurePosixPath(name).name != ".env.example"))]
    if forbidden:
        print("Rejected: tracked local environment files. Remove them from Git.")
        return 1
    print("No tracked .env files; this check is not a general secret scanner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
