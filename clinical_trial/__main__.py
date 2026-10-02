"""Credential-free environment check: python -m clinical_trial."""
import os
from .config import read_environment


def main() -> int:
    try:
        environment = read_environment(os.environ)
    except ValueError as error:
        print(str(error))
        return 2
    print(f"Environment validated: {environment.value}. No cloud deployment performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
