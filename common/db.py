import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Iterator, List, Mapping, Optional, Sequence, Union
from uuid import UUID

import psycopg
from psycopg.rows import namedtuple_row
from psycopg.sql import SQL, Composable, Identifier, Placeholder
from psycopg.types.string import TextLoader
from psycopg_pool import ConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://festhub:festhub@localhost:5433/festhub")
POOL_SIZE = int(os.getenv("GRPC_WORKERS", "10"))


def configure(connection: psycopg.Connection) -> None:
    connection.adapters.register_loader("uuid", TextLoader)


pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=POOL_SIZE, open=True, configure=configure,
                      kwargs={"autocommit": True, "row_factory": namedtuple_row})
current: ContextVar[Optional[psycopg.Connection]] = ContextVar("current_connection", default=None)


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    if (conn := current.get()) is not None:
        yield conn
        return
    with pool.connection() as conn:
        token = current.set(conn)
        try:
            yield conn
        finally:
            current.reset(token)


@contextmanager
def transaction() -> Iterator[None]:
    # commits when the block finishes and rolls back if it raises, so a failed command changes nothing
    with connection() as conn, conn.transaction():
        yield


def fetchone(
    query: Union[str, Composable], 
    params: Union[Sequence[Any], Mapping[str, Any], None] = None, 
    row_factory: Optional[Callable[..., Any]] = None
) -> Optional[Any]:
    with connection() as conn:
        return conn.cursor(row_factory=row_factory).execute(query, params).fetchone() # type: ignore


def fetchall(
    query: Union[str, Composable], 
    params: Union[Sequence[Any], Mapping[str, Any], None] = None, 
    row_factory: Optional[Callable[..., Any]] = None
) -> List[Any]:
    with connection() as conn:
        return conn.cursor(row_factory=row_factory).execute(query, params).fetchall() # type: ignore


def rowcount(
    query: Union[str, Composable], 
    params: Union[Sequence[Any], Mapping[str, Any], None] = None
) -> int:
    with connection() as conn:
        return conn.execute(query, params).rowcount # type: ignore


def to_uuid(record_id: Any) -> Optional[UUID]:
    # an id that isn't a valid UUID can't match any row, so send NULL instead of letting Postgres raise
    try:
        return UUID(record_id)
    except (TypeError, ValueError):
        return None


def get(table: str, record_id: Any) -> Optional[Any]:
    query = SQL("SELECT * FROM {} WHERE id = %s").format(Identifier(table))
    return fetchone(query, [to_uuid(record_id)])


def find(table: str, record_id: Any, order_by: str) -> List[Any]:
    if record_id is not None:
        row = get(table, record_id)
        return [row] if row else []
    query = SQL("SELECT * FROM {} ORDER BY {}, id").format(Identifier(table), Identifier(order_by))
    return fetchall(query)


def insert(table: str, custom_id: Any, record: Any) -> Optional[Any]:
    # returns None when the custom id is already taken
    values = vars(record)
    query = SQL(
        "INSERT INTO {} (id, {}) VALUES (COALESCE(%(id)s, uuidv7()), {}) ON CONFLICT (id) DO NOTHING RETURNING id"
    ).format(Identifier(table), SQL(", ").join(map(Identifier, values)), SQL(", ").join(map(Placeholder, values)))
    row = fetchone(query, dict(values, id=custom_id))
    return None if row is None else row.id


def update(table: str, record_id: Any, changes: Any) -> Optional[Any]:
    # values left as None keep the column's current value
    values = vars(changes)
    assignments = SQL(", ").join(
        SQL("{0} = COALESCE({1}, {0})").format(Identifier(column), Placeholder(column)) for column in values
    )
    query = SQL("UPDATE {} SET {} WHERE id = %(id)s RETURNING *").format(Identifier(table), assignments)
    return fetchone(query, dict(values, id=to_uuid(record_id)))


def delete(table: str, record_id: Any) -> bool:
    query = SQL("DELETE FROM {} WHERE id = %s").format(Identifier(table))
    return rowcount(query, [to_uuid(record_id)]) > 0


def link(table: str, event_id: Any, other_id: Any) -> bool:
    # returns False when the two are already linked
    query = SQL("INSERT INTO {} VALUES (%s, %s) ON CONFLICT DO NOTHING").format(Identifier(table))
    return rowcount(query, [to_uuid(event_id), to_uuid(other_id)]) > 0


def unlink(table: str, column: str, event_id: Any, other_id: Any) -> bool:
    query = SQL("DELETE FROM {} WHERE event_id = %s AND {} = %s").format(Identifier(table), Identifier(column))
    return rowcount(query, [to_uuid(event_id), to_uuid(other_id)]) > 0