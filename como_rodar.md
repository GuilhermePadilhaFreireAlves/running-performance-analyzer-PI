# Como rodar o projeto

## Sequência rápida (primeira vez)

```bash
# 1. Ambiente Python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Banco de dados (SQLite dev — sem instalar nada)
alembic -c server/alembic.ini upgrade head

# 3. Backend
uvicorn server.src.main:app --reload

# 4. Frontend (outro terminal)
cd client
npm install
npm run dev
```

Acesse: **http://localhost:5173**

---

## Sequência rápida (próximas vezes)

```bash
# Terminal 1 — backend
venv\Scripts\activate
uvicorn server.src.main:app --reload

# Terminal 2 — frontend
cd client
npm run dev
```

---

## Pré-requisitos

| Ferramenta | Versão mínima | Verificar |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

Não é necessário instalar PostgreSQL para desenvolvimento local — o projeto usa SQLite por padrão.

---

## Configuração detalhada

### 1. Ambiente Python

```bash
# Na raiz do repositório
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/macOS)
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Variáveis de ambiente

O backend não precisa de `.env` para rodar localmente — usa SQLite e uma chave JWT padrão de dev.

Para sobrescrever:

```bash
# Cria um .env na raiz (opcional)
SECRET_KEY=sua-chave-secreta
DATABASE_URL=sqlite:///./server_dev.db   # padrão — pode omitir
```

Para usar **PostgreSQL** em vez de SQLite:

```bash
DATABASE_URL=postgresql+psycopg2://usuario:senha@localhost:5432/stride_db
```

### 3. Banco de dados

```bash
# Aplicar todas as migrations (cria o arquivo server_dev.db se usar SQLite)
alembic -c server/alembic.ini upgrade head

# Ver status atual das migrations
alembic -c server/alembic.ini current

# Reverter uma migration
alembic -c server/alembic.ini downgrade -1
```

> O arquivo `server_dev.db` é gerado na raiz do repositório e está no `.gitignore`. Não commitar.

### 4. Backend (FastAPI)

```bash
# Sempre a partir da raiz do repositório, com venv ativo
uvicorn server.src.main:app --reload
```

- Sobe em `http://localhost:8000`
- Docs automáticas: `http://localhost:8000/docs`
- `--reload` reinicia ao salvar arquivos Python

### 5. Frontend (React + Vite)

```bash
cd client

# Copiar variáveis de ambiente (só na primeira vez)
copy .env.example .env.local      # Windows
# cp .env.example .env.local      # Linux/macOS

npm install
npm run dev
```

- Sobe em `http://localhost:5173`
- Proxy do Vite já aponta para `http://localhost:8000` via `VITE_API_BASE_URL`

---

## Assets de runtime (não estão no git)

Para rodar os scripts de análise local (`mainYolo.py` / `mainGraph.py`), dois arquivos precisam existir na raiz:

| Arquivo | Descrição |
|---|---|
| `yolo26x-pose.pt` | Pesos do modelo YOLO pose (~126 MB). Baixar do Ultralytics e colocar na raiz. |
| `run/profissional.mp4` | Vídeo de entrada. Criar a pasta `run/` e colocar o vídeo. |

```bash
# Rodar análise (a partir da raiz, com venv ativo)
python processing/src/mainYolo.py    # saída no console
python processing/src/mainGraph.py   # console + gráficos PNG na raiz
```

O script detecta GPU automaticamente: usa CUDA se disponível (NVIDIA), CPU caso contrário.

---

## Typecheck e lint

```bash
# Backend
mypy

# Frontend (typecheck via build)
cd client && npm run build

# Frontend lint (opcional)
cd client && npm run lint
```

---

## Troubleshooting

**`no such column: sessao_analise.eventos_json`**
Migração pendente. Rode: `alembic -c server/alembic.ini upgrade head`

**`ModuleNotFoundError: No module named 'server'`**
Execute sempre a partir da raiz do repositório, nunca de dentro de `server/`.

**`CORS error` no browser**
O backend precisa estar rodando em `localhost:8000`. Verifique se o uvicorn está ativo.

**`torch.cuda` não encontrado (GPU)**
PyTorch instalado sem suporte CUDA. Para NVIDIA, reinstale:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```
