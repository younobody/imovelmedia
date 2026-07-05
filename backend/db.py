"""Conexão com o PostgreSQL (Supabase) via pool simples."""
import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL or "[YOUR-PASSWORD]" in DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL ausente ou sem senha. Copie .env.example para .env e "
        "preencha a senha do banco (Supabase > Connect > Session pooler > URI)."
    )

# Pool: 1 a 10 conexões reaproveitadas entre requisições.
_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)


@contextmanager
def get_cursor():
    """Empresta uma conexão do pool e devolve no fim (commit/rollback automático)."""
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def query(sql: str, params: tuple = ()):
    """Executa SELECT e devolve lista de dicts."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()
