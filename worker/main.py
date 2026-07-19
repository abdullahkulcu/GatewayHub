"""Sync worker entrypoint: runs the poll scheduler forever.

The actual scheduler/sync logic lives in backend/app/poller.py (and is
unit-tested there against a real Postgres); this process is just the
long-running entrypoint that wires it to a DB session.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db import SessionLocal  # noqa: E402
from app.poller import run_forever  # noqa: E402

if __name__ == "__main__":
    with SessionLocal() as db:
        run_forever(db)
