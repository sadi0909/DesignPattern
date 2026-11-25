"""Run the idempotent demo seed from the backend directory: ``python seed.py``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from infrastructure.seed import main  # noqa: E402

if __name__ == "__main__":
    main()
