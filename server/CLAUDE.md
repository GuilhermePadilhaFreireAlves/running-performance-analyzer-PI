# Backend (`server/`) — instructions for Claude

## Layout

```
server/
  alembic.ini                 # Alembic config (runs from repo root)
  alembic/
    env.py                    # reads DATABASE_URL, loads Base.metadata
    versions/                 # migration scripts
  src/
    database.py               # Base, engine, SessionLocal, get_session
    main.py                   # FastAPI app (server.src.main:app)
    models/                   # SQLAlchemy 2.0 ORM models
      __init__.py             # single re-export point — register new models here
      usuario.py
      sessao_analise.py
      metrica.py
      recomendacao.py
```

## Commands (run from repo root)

```
# boot API
uvicorn server.src.main:app --reload

# apply migrations
DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db" \
  alembic -c server/alembic.ini upgrade head

# generate a new migration
alembic -c server/alembic.ini revision -m "<message>"      # manual
alembic -c server/alembic.ini revision --autogenerate -m "<message>"   # against a live DB

# typecheck
mypy
```

`DATABASE_URL` defaults to `sqlite:///./server_dev.db` for quick local runs; Alembic auto-enables `render_as_batch` when the URL is SQLite.

## Conventions

- Use **absolute imports** (`from server.src.database import Base`). `server/__init__.py` and `server/src/__init__.py` must exist; mypy and Alembic both rely on the `server.src.*` module path.
- Every new ORM model must be added to `server/src/models/__init__.py` so Alembic sees it in `Base.metadata`.
- Use SQLAlchemy 2.0 typed style: `Mapped[...]` + `mapped_column(...)`.
- Enum-valued columns: VARCHAR + `CheckConstraint("col IN (...)")` for Postgres/SQLite portability. Export the tuple of allowed values as a module-level constant (e.g. `SESSAO_STATUS_VALUES`) so API/validation layers can reuse it.
- Keep migrations dialect-portable: prefer `sa.false()`, `sa.func.now()`, `sa.text(...)` over raw dialect literals.
- FastAPI endpoints must declare return types — mypy is configured with `disallow_untyped_defs = True` for `server/src/**`.
- Protect private routes with `from server.src.auth import CurrentUser` and a `user: CurrentUser` parameter. The dependency decodes the JWT, loads the `Usuario`, and emits a uniform 401 (`"Credenciais inválidas"`/`"Não autenticado"`) on every failure path. Tokens are minted by `server.src.security.create_access_token(user_id)` and signed with `SECRET_KEY` (env var, dev default in `security.py`).

## Gotchas

- SQLite does not enforce FKs unless `PRAGMA foreign_keys=ON` is set per connection. Schema is still created correctly; enable the pragma when you need enforcement in local tests.
- Do not import model modules directly from Alembic migration scripts — autogenerate reads `target_metadata` from `env.py`, which already imports `server.src.models`.
- Never commit `server_dev.db` / `*.sqlite*` — they are in `.gitignore`.
