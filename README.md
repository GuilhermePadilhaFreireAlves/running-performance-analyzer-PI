# running-performance-analyzer

Analisador de corrida baseado em vídeo. Um modelo YOLO de pose extrai keypoints COCO do vídeo do corredor; o backend deriva ângulos articulares (cotovelo, joelho, quadril), inclinação do tronco, cadência, oscilação vertical, simetria e gera recomendações.

O projeto tem três frentes:

- **`processing/`** — scripts standalone em Python que rodam a pipeline diretamente em um vídeo (sem API), úteis para experimentação rápida.
- **`server/`** — API FastAPI com autenticação JWT, upload de vídeo, processamento assíncrono e endpoints de diagnóstico/histórico (PostgreSQL via SQLAlchemy + Alembic).
- **`client/`** — frontend React 19 + Vite + TypeScript que consome a API.

## Pré-requisitos

- **Python 3.11+** (3.11/3.12)
- **Node.js 20+** e **npm 10+** (para o frontend)
- **PostgreSQL 14+** (opcional — em desenvolvimento o backend cai em SQLite por padrão)
- **Pesos do YOLO**: arquivo `yolo26x-pose.pt` na raiz do repositório (~126 MB). Não está versionado — baixe os pesos da Ultralytics e coloque na raiz, ou aponte a env var `YOLO_POSE_MODEL` para outro caminho.
- **Vídeo de entrada** (apenas para os scripts standalone): coloque um arquivo em `./run/profissional.mp4` ou edite o argumento `source=` no script.

## Setup do backend

A partir da raiz do repositório:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Em ambientes headless (Dev Container / WSL2 / servidor sem GUI), force a versão
# headless do OpenCV. O `ultralytics` puxa `opencv-python` (com GUI) como
# dependência transitiva, e ela falha em runtime com `ImportError: libGL.so.1`
# porque o container não tem libs gráficas. O comando abaixo desinstala a versão
# com GUI e mantém apenas a `-headless` (já listada no requirements.txt).
pip uninstall -y opencv-python && pip install --force-reinstall --no-deps opencv-python-headless
```

### Variáveis de ambiente

Todas opcionais em desenvolvimento — o backend tem defaults sensatos. Para produção, defina:

| Variável            | Default                          | Descrição                                                           |
| ------------------- | -------------------------------- | ------------------------------------------------------------------- |
| `DATABASE_URL`      | `sqlite:///./server_dev.db`      | URL do banco. Para Postgres: `postgresql://user:pass@host/dbname`.  |
| `SECRET_KEY`        | dev string >= 32 chars           | Chave HMAC do JWT. **Obrigatório** trocar em produção.              |
| `UPLOAD_DIR`        | `./uploads/`                     | Diretório onde os vídeos enviados são persistidos (gitignored).     |
| `YOLO_POSE_MODEL`   | `yolo26x-pose.pt`                | Caminho do peso YOLO usado pela validação de perspectiva.           |

### Migrations

```bash
alembic -c server/alembic.ini upgrade head
```

Para gerar uma nova migration depois de adicionar/alterar modelos:

```bash
alembic -c server/alembic.ini revision --autogenerate -m "descrição da mudança"
```

### Subir a API

```bash
uvicorn server.src.main:app --reload --host 0.0.0.0
```

A API sobe em `http://localhost:8000`. Docs interativas em `http://localhost:8000/docs`.

> **Por que `--host 0.0.0.0`?** Em ambientes Dev Container / WSL2 / Docker, o port-forward do VS Code só expõe portas que escutam em todas as interfaces. Sem essa flag, o uvicorn só responde em `127.0.0.1` dentro do container e o navegador no host não consegue alcançar a API — o frontend exibe "Não foi possível conectar ao servidor". Em desenvolvimento local fora de container, a flag é inofensiva.

### Typecheck

```bash
mypy
```

Cobre `server/src` e `server/alembic` com `disallow_untyped_defs = True`. Toda função nova precisa declarar tipos.

## Setup do frontend

A partir de `client/`:

```bash
cd client
npm install
```

Crie um `.env.local` (opcional) baseado no `.env.example` se quiser apontar para uma API em outro host:

```
VITE_API_BASE_URL=http://localhost:8000
```

### Comandos

```bash
npm run dev     # Vite dev server em http://localhost:5173
npm run build   # tsc -b + vite build (build + typecheck de produção)
npm run lint    # ESLint
```

Para a aplicação funcionar end-to-end, suba o backend (`uvicorn ...` na raiz) e o frontend (`npm run dev` em `client/`) em terminais separados.

## Scripts standalone (sem API)

Para rodar a pipeline de análise diretamente em um vídeo, sem subir backend nem frontend:

```bash
# A partir da raiz do repositório, com a venv ativada:
python processing/src/mainYolo.py    # apenas saída no console
python processing/src/mainGraph.py   # console + salva grafico_*.png no CWD
```

Ambos os scripts assumem:

- `yolo26x-pose.pt` na raiz do repositório.
- `./run/profissional.mp4` como vídeo de entrada (edite o `source=` para outro caminho).

## Estrutura do projeto

```
.
├── processing/src/        # scripts standalone (mainYolo.py, mainGraph.py)
├── server/
│   ├── alembic/           # migrations
│   ├── alembic.ini
│   └── src/
│       ├── main.py        # FastAPI app
│       ├── database.py    # engine + SessionLocal
│       ├── auth.py        # dependency get_current_user / CurrentUser
│       ├── security.py    # bcrypt + JWT helpers
│       ├── models/        # SQLAlchemy 2.0 (usuario, sessao_analise, metrica, recomendacao)
│       ├── schemas/       # Pydantic v2
│       ├── routers/       # users, auth, videos, analysis, historico
│       └── video_pipeline.py  # validador YOLO + entrypoint do processamento assíncrono
├── client/                # frontend React + Vite
│   ├── src/
│   │   ├── api/           # axios client + chamadas (auth, videos, analysis, ...)
│   │   ├── context/       # AuthContext + useAuth
│   │   ├── components/    # PrivateRoute, etc.
│   │   ├── pages/         # telas (login, signup, upload, status, analysis, ...)
│   │   └── utils/         # validações e helpers puros
│   └── package.json
├── requirements.txt
├── mypy.ini
├── yolo26x-pose.pt        # NÃO versionado — colocar manualmente
└── run/                   # NÃO versionado — colocar profissional.mp4 aqui
```

## Workflow de desenvolvimento típico

1. Ative a venv e suba a API: `uvicorn server.src.main:app --reload --host 0.0.0.0`
2. Em outro terminal: `cd client && npm run dev`
3. Acesse `http://localhost:5173`, cadastre um usuário, faça login e suba um vídeo.
4. O backend valida (pace, FPS >= 60, perspectiva lateral via YOLO) e dispara o processamento como `BackgroundTask`.
5. A tela de status faz polling em `GET /api/videos/{id}/status` até o status ficar `concluido` ou `erro_*`.

## Notas

- **Plataforma primária de desenvolvimento**: Windows (mas roda igual em Linux/macOS — todos os comandos acima são portáveis).
- **Convenção de idioma no código**: nomes de variáveis, comentários e mensagens em português (`angulo`, `joelho`, `quadril`, `passos`, `cadencia`). Mantenha esse padrão ao estender os scripts em `processing/`.
- **Convenção de ângulo do joelho**: os scripts reportam `180 - ângulo_interno` (perna reta ≈ 0°, perna dobrada = positivo crescente). Isso é proposital — não "consertar".
- **Cadência**: aproximada, baseada em wall-clock desde o início do script (inclui tempo de carregar o YOLO).
