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
    biomechanics/             # pure-math métricas sobre keypoints
      __init__.py             # re-exporta a API pública de cada módulo
      escala.py               # calcular_fator_escala (US-007)
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
- Heavy external dependencies (OpenCV, Ultralytics YOLO) live behind the `VideoValidator` and `PoseExtractor` protocols in `server.src.video_pipeline`. `VideoValidator` is injected via `Depends(get_video_validator)` (`ValidatorDep` alias in the router). `PoseExtractor` is used by the background `run_pipeline(sessao_id, video_path)` — it's **not** a FastAPI dependency (background tasks run outside the DI scope).
- Background pipeline (`run_pipeline`) owns the full keypoint → metrics → recomendações chain in-memory. It opens its own session via `SessionLocal` (or an injected `session_factory`), advances `sessao.status` through `detectando_pose → calculando_metricas → concluido` on success or to `erro_qualidade_keypoints` / `erro_multiplas_pessoas` on failure, persists `sessao.fps`, and deletes the uploaded video file at the end. Future metric stories extend `run_pipeline` in place — do not persist keypoints between invocations.
- Keypoint constants live in `video_pipeline`: `NUM_KEYPOINTS=17`, `KEYPOINT_SCORE_THRESHOLD=0.5` (below → `None`), `LOW_QUALITY_KP_THRESHOLD=9` (strict majority of 17). Use `smooth_frames(frames, window=5)` output (moving average, preserves `None`) as the input for any downstream biomechanics calc, not raw extractor output.
- Multipart uploads require `python-multipart` (in `requirements.txt`). Endpoints use `pace_min_km: Annotated[float, Form()]` + `file: Annotated[UploadFile, File()]`. Persist uploads to `UPLOAD_DIR` env var (default `./uploads/`, gitignored) before validation, and always clean up on validation failure.
- Pure-math biomechanics utilities (ângulos, fator de escala, overstriding, …) vivem em `server/src/biomechanics/<metric>.py` e são re-exportados pelo `__init__.py` do pacote. Consomem a saída suavizada de `video_pipeline.smooth_frames(...)` (tipo `list[FrameKeypoints]`), devolvem `dataclass(frozen=True)` e levantam `ValueError(MSG_*)` com mensagens de módulo para erros de domínio.
- Persistência de métricas no pipeline: funções privadas `_persistir_<metric>(session, sessao_id, frames)` em `video_pipeline.py` encapsulam a chamada à biomecânica + criação de `Metrica`. Lazy-importam `biomechanics.<metric>` e `models.metrica` dentro da função para manter o módulo enxuto. **Não** alteram `sessao.status` — a transição final para `concluido` é responsabilidade exclusiva do gerador de recomendações (US-016).
- Métricas que precisam do `fator_escala` (overstriding em US-012, oscilação vertical em US-014) recebem o fator (`float`) já calculado como parâmetro puro. É o `_persistir_<metric>(session, sessao_id, frames, altura_cm)` em `video_pipeline.py` que carrega `altura_cm` em `run_pipeline` (via `sessao.usuario.altura_cm`), chama `calcular_fator_escala(frames, altura_cm).fator_escala`, e repassa para a biomecânica. A camada biomecânica jamais lê o ORM nem `usuario.altura_cm`. Falhas do fator (altura ausente, nenhum frame válido para altura em pixels) são engolidas no helper persist (no-op silencioso) — não interrompem o pipeline.
- Convenção de ângulo articular do **backend** é o ângulo interno calculado via `arccos` do produto escalar normalizado (perna estendida ⇒ 180°). Isso difere da convenção legada em `processing/src/mainGraph.py` (`180 - internal`). Ao implementar nova métrica de ângulo, proteja o `arccos` com clamp `cos_theta ∈ [-1, 1]` para blindar contra erro numérico em configurações colineares.

## Gotchas

- SQLite does not enforce FKs unless `PRAGMA foreign_keys=ON` is set per connection. Schema is still created correctly; enable the pragma when you need enforcement locally.
- Do not import model modules directly from Alembic migration scripts — autogenerate reads `target_metadata` from `env.py`, which already imports `server.src.models`.
- Never commit `server_dev.db` / `*.sqlite*` — they are in `.gitignore`.
