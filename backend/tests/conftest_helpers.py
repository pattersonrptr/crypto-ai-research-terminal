"""Shared test utilities for SQLite-based async fixtures.

The ``narratives`` table uses PostgreSQL ARRAY columns that are incompatible
with SQLite.  Use :func:`create_sqlite_tables` instead of
``Base.metadata.create_all`` to skip tables that require PostgreSQL features.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from sqlalchemy import Connection

# Tables that use PostgreSQL-only column types (e.g. ARRAY).
_PG_ONLY_TABLES = {"narratives"}


def create_sqlite_tables(conn: Connection) -> None:
    """Create all ORM tables except those requiring PostgreSQL-only types.

    Drop-in replacement for ``Base.metadata.create_all(conn)`` in SQLite
    fixtures.
    """
    tables = [t for t in Base.metadata.sorted_tables if t.name not in _PG_ONLY_TABLES]
    Base.metadata.create_all(conn, tables=tables)
