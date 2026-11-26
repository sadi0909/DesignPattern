"""Phase 14 — migration smoke tests.

The offline test proves the revision graph is one linear chain. The gated test
runs ``alembic upgrade head`` twice and ``downgrade base`` on a throwaway
database, so a migration that only works against an already-populated dev
database fails here instead of in a reviewer's checkout.
"""

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from infrastructure.settings import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
VERSIONS_DIR = BACKEND_DIR / "alembic" / "versions"

CORE_TABLES = {
    "locations",
    "zones",
    "devices",
    "sensor_readings",
    "actuator_states",
    "automation_rules",
    "alerts",
    "command_log",
    "actuator_execution_log",
}


def _migration_graph() -> dict[str, str | tuple[str, ...] | None]:
    """Parse ``revision`` / ``down_revision`` from the version files.

    The local ``backend/alembic`` package shadows the installed ``alembic``
    library when pytest runs from ``backend``, so this reads the graph from
    the source files instead of importing ``alembic.script``.
    """
    revisions: dict[str, str | tuple[str, ...] | None] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        values: dict[str, object] = {}
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            name: str | None = None
            value: ast.expr | None = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    name, value = target.id, node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name, value = node.target.id, node.value
            if name in {"revision", "down_revision"} and value is not None:
                values[name] = ast.literal_eval(value)
        revision = values.get("revision")
        assert isinstance(revision, str) and revision, f"{path.name} has no revision"
        assert revision not in revisions, f"duplicate revision {revision} in {path.name}"
        revisions[revision] = values.get("down_revision")  # type: ignore[assignment]
    return revisions


def _head_revision(revisions: dict[str, str | tuple[str, ...] | None]) -> str:
    heads = {
        revision
        for revision, down in revisions.items()
        if down is None or isinstance(down, str)
    } - {
        down
        for down in revisions.values()
        if isinstance(down, str)
    }
    assert len(heads) == 1, f"expected exactly one head, found {sorted(heads)}"
    return heads.pop()


def test_migration_history_is_one_linear_chain():
    revisions = _migration_graph()
    assert revisions, "no migration revisions found"

    merges = [
        revision
        for revision, down in revisions.items()
        if isinstance(down, tuple)
    ]
    assert not merges, f"merge revisions branch the chain: {merges}"

    roots = [revision for revision, down in revisions.items() if down is None]
    assert len(roots) == 1, f"expected exactly one root revision, found {roots}"

    missing = {
        down
        for down in revisions.values()
        if isinstance(down, str) and down not in revisions
    }
    assert not missing, f"down_revision points at unknown revisions: {sorted(missing)}"

    _head_revision(revisions)


def _alembic_executable() -> Path:
    name = "alembic.exe" if os.name == "nt" else "alembic"
    candidate = Path(sys.executable).with_name(name)
    if candidate.exists():
        return candidate
    found = shutil.which("alembic")
    if found is None:
        pytest.skip("alembic executable not found next to the interpreter or on PATH")
    return Path(found)


def _run_alembic(*args: str, database_url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(_alembic_executable()), *args],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="set RUN_DB_INTEGRATION=1 to run against the configured PostgreSQL database",
)
def test_upgrade_head_twice_then_downgrade_base_on_a_scratch_database():
    head = _head_revision(_migration_graph())

    base_url = make_url(settings.database_url)
    scratch_name = f"greenhouse_migration_smoke_{os.getpid()}"
    admin_engine = create_engine(
        base_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    scratch_engine = None
    try:
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP DATABASE IF EXISTS "{scratch_name}" WITH (FORCE)')
            )
            connection.execute(text(f'CREATE DATABASE "{scratch_name}"'))

        scratch_url = base_url.set(database=scratch_name).render_as_string(
            hide_password=False
        )

        # Twice: the second run proves re-running migrations on a current
        # database is a no-op, which reviewers do after pulling a phase.
        for _ in range(2):
            result = _run_alembic("upgrade", "head", database_url=scratch_url)
            assert result.returncode == 0, result.stdout + result.stderr

        scratch_engine = create_engine(scratch_url)
        with scratch_engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            version = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        assert version == head
        assert CORE_TABLES <= tables, f"missing tables after upgrade: {CORE_TABLES - tables}"

        result = _run_alembic("downgrade", "base", database_url=scratch_url)
        assert result.returncode == 0, result.stdout + result.stderr

        with scratch_engine.connect() as connection:
            remaining = set(inspect(connection).get_table_names())
        assert CORE_TABLES.isdisjoint(remaining), (
            f"tables survived downgrade base: {CORE_TABLES & remaining}"
        )
    finally:
        if scratch_engine is not None:
            scratch_engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP DATABASE IF EXISTS "{scratch_name}" WITH (FORCE)')
            )
        admin_engine.dispose()
