# PRD: Running Analyzer — Sistema de Análise Biomecânica de Corrida por Visão Computacional

> **Versão:** 1.1 | **Data:** 18/04/2026 | **Status:** Em desenvolvimento  
> **Autores:** Guilherme Padilha, Marcos Mazzero Jr., Matheus Chagas, Thiago Gonzalez, Victor Borges

---

## 1. Introdução / Visão Geral

O **Running Analyzer** é um sistema baseado em Inteligência Artificial para análise biomecânica da corrida por meio de vídeos. O usuário envia um vídeo de sua corrida pelo aplicativo, informa seu pace e o sistema extrai automaticamente métricas biomecânicas (ângulo do joelho, inclinação do tronco, tempo de contato com o solo, entre outras), gerando um diagnóstico técnico com feedback claro e acionável.

**Problema central:** A análise biomecânica de corrida de qualidade está restrita a clínicas e laboratórios de alto custo, inacessíveis para o corredor amador. O Running Analyzer democratiza esse acesso utilizando visão computacional em vídeos do cotidiano.

**Público-alvo primário:** Corredores amadores e iniciantes sem acesso a acompanhamento profissional constante.  
**Público-alvo secundário:** Corredores avançados, treinadores e profissionais de saúde.

---

## 2. Objetivos

- Permitir que qualquer corredor envie um vídeo e receba um diagnóstico biomecânico acessível e aplicável.
- Identificar automaticamente falhas posturais via IA (desalinhamento do tronco, impacto incorreto, sobrepassada, etc.).
- Fornecer feedback em dois níveis: simplificado (amador) e técnico/bruto (avançado/profissional).
- Acompanhar a evolução do corredor ao longo do tempo via histórico de análises.
- Contribuir para a prevenção de lesões por identificação precoce de padrões incorretos.
- Processar vídeos de forma assíncrona e descartar o conteúdo bruto após extração dos dados, preservando privacidade.

---

## 3. Arquitetura e Stack Técnica

O sistema segue uma arquitetura de **pipeline assíncrono** com quatro componentes principais:

| Componente | Tecnologia | Responsabilidade |
|---|---|---|
| **Cliente** | React | Interface do usuário: envio de vídeos, visualização de resultados, histórico |
| **Servidor de Aplicação** | FastAPI (Python) | Gerencia requisições, orquestra o pipeline via Background Tasks, persiste dados |
| **Módulo de Processamento CV** | **YOLOv8-pose** + OpenCV | Detecção de 17 keypoints COCO frame a frame |
| **Motor Biomecânico** | Python (NumPy + lógica trigonométrica) | Calcula métricas biomecânicas a partir dos keypoints |
| **Banco de Dados** | PostgreSQL | Persiste usuários, sessões, métricas e recomendações |

> **Decisão técnica:** O modelo de detecção de pose escolhido é o **YOLOv8-pose**, por oferecer o melhor equilíbrio entre precisão e desempenho em CPU para cenários reais de corrida.

> **Decisão técnica:** O processamento assíncrono será implementado com **FastAPI Background Tasks** (nativo do FastAPI). Não há necessidade de Redis ou Celery para o escopo deste MVP.

**Pipeline de processamento:**
1. Validações no frontend (duração, resolução, FPS, pace preenchido)
2. Upload do vídeo com pace informado
3. Validação de perspectiva lateral no backend
4. Detecção de pose frame a frame (YOLOv8-pose)
5. Filtro de suavização (redução de jitter)
6. Cálculo de métricas biomecânicas
7. Geração de recomendações e nota geral
8. Persistência dos resultados + descarte do vídeo

---

## 4. Modelo de Dados (MER)

```
USUARIO (id, name, email, senha_hash, altura_cm, peso_kg, nivel_experiencia, criado_em)
    |
    | 1:N
    v
SESSAO_ANALISE (id, usuario_id, pace_min_km, nota_geral, feedback_ia, criado_em)
    |
    |------------ 1:N ------------|
    v                             v
METRICA                     RECOMENDACAO
(id, sessao_id,             (id, sessao_id,
 tipo, valor, unidade)       categoria, descricao, severidade)
```

**Entidades:**
- **USUARIO** — dados cadastrais do corredor; `altura_cm` é obrigatório para calibração de pixels→cm.
- **SESSAO_ANALISE** — cada análise de vídeo; armazena o `pace_min_km` informado pelo usuário, nota geral e feedback textual da IA.
- **METRICA** — valores calculados pelo motor biomecânico (ex: `angulo_joelho_dir = 42°`).
- **RECOMENDACAO** — feedback por categoria com severidade (Informativo / Atenção / Crítico).

---

## 5. APIs

### `POST /api/users/register`
- **Entrada:** `{ name, email, senha, altura_cm, peso_kg, nivel_experiencia }`
- **Saída:** `200 OK` com dados do perfil criado

### `POST /api/auth/login`
- **Entrada:** `{ email, senha }`
- **Saída:** `200 OK` + sessão autenticada

### `POST /api/videos/upload`
- **Entrada:** `form-data` com arquivo de vídeo + campo `pace_min_km` (float)
- **Saída:** `200 OK` com `video_id` (pipeline assíncrono iniciado via Background Task)
- **Validações no backend (antes de iniciar o pipeline):**
  - Perspectiva lateral (proporção ombro/quadril)
  - FPS ≥ 60 — se abaixo, retorna `422` com mensagem de erro clara
- **Fluxo interno:** Validação lateral → YOLOv8-pose → Suavização → Motor Biomecânico → Persistência → Descarte do vídeo

### `GET /api/videos/{id}/status`
- **Entrada:** `video_id` no path
- **Saída:** Status atual (ex: "Validando perspectiva", "Detectando pose", "Calculando métricas", "Concluído")

### `GET /api/analysis/{id}/simple`
- **Entrada:** `video_id` no path
- **Saída:** Diagnóstico em linguagem acessível com nota geral e recomendações categorizadas

### `GET /api/analysis/{id}/raw`
- **Entrada:** `video_id` no path
- **Saída:** Séries temporais numéricas, coordenadas brutas e métricas articulares por frame

### `GET /api/historico-analise`
- **Entrada:** Query params de paginação (`?page=1&limit=10`)
- **Saída:** Lista de sessões do usuário com data, pace, status e nota geral

---

## 6. Parâmetros Biomecânicos — Definição Científica Completa

> Esta seção define quais keypoints analisar, os valores ideais e como calculá-los, embasados por pesquisa científica. Análises críticas de cada métrica estão destacadas.

---

### 6.1 Ângulo do Joelho

#### O que é o ângulo ideal?

O ângulo do joelho varia ao longo do ciclo de passada. O foco principal do sistema é o **contato inicial**, que é o indicador mais robusto de lesão:

| Fase da Passada | Ângulo Ideal (Flexão) | Sinal de Problema |
|---|---|---|
| **Contato Inicial** ← *foco principal* | ~20° de flexão | Joelho totalmente estendido (<10°) = alto risco de lesão por impacto |
| **Meio do Apoio** (mid-stance) | 40–45° de flexão | <30° = rígido; >55° = colapso excessivo |
| **Saída do Pé** (toe-off) | ~40° de flexão | Muito estendido = perda de propulsão |
| **Pico de Oscilação** (swing) | 60–77° (varia com velocidade) | <50° = passada curta |

> **🚀 Melhoria Futura:** Adaptar os thresholds do ângulo do joelho por faixa de pace (lento / moderado / rápido) aumentaria a precisão diagnóstica, pois a literatura confirma que os ângulos variam com a velocidade. Esta funcionalidade foi avaliada como de complexidade elevada para o Motor Biomecânico no MVP e será implementada em uma versão futura.

#### Como calcular (keypoints COCO)

- **Índice 11/12:** Quadril Esq/Dir (referência superior)
- **Índice 13/14:** Joelho Esq/Dir (vértice do ângulo)
- **Índice 15/16:** Tornozelo Esq/Dir (referência inferior)

```
Ângulo_joelho = arccos(
  (vetor_quadril_joelho · vetor_tornozelo_joelho) /
  (|vetor_quadril_joelho| × |vetor_tornozelo_joelho|)
)
```

O contato inicial é detectado quando o tornozelo atinge seu ponto de altitude mínima no eixo Y (valor máximo em coordenadas de imagem).

#### Referência científica
- Neal, B. S. et al. **"An Evidence-Based Videotaped Running Biomechanics Analysis."** PMC4714754, 2016.
- Aeles, J. et al. **"Knee Angle Estimation with Dynamic Calibration Using IMUs."** Sensors, 2024.

---

### 6.2 Ângulo do Cotovelo (Swing de Braço)

#### O que é o ângulo ideal?

A faixa aceitável é **70° a 110°**. O valor de 90° é amplamente citado, mas é uma simplificação — o que importa é que o braço não cruze a linha central do corpo e que o movimento seja predominantemente anteroposterior (frente/trás).

- Cotovelo mais **fechado (<90°)** → levemente mais econômico.
- Cotovelo muito **aberto (>110°)** → indica fadiga ou tensão no ombro.

> **⚠️ Crítica:** A regra dos "90° exatos" é um mito simplificado. A pesquisa de 2025 (PMC11929735) demonstra que o balanço ativo do braço reduz a rotação do torso e o custo metabólico — o ângulo exato importa menos do que a direção do movimento. Sinalize apenas ângulos fora da faixa 70°–110°.

#### Como calcular (keypoints COCO)

- **Índice 5/6:** Ombro Esq/Dir
- **Índice 7/8:** Cotovelo Esq/Dir (vértice)
- **Índice 9/10:** Pulso Esq/Dir

```
Ângulo_cotovelo = arccos(
  (vetor_ombro_cotovelo · vetor_pulso_cotovelo) /
  (|vetor_ombro_cotovelo| × |vetor_pulso_cotovelo|)
)
```

Calcular a **média ao longo de vários ciclos** para obter o ângulo típico do atleta.

#### Referência científica
- Misu, S. et al. **"Active Arm Swing During Running Improves Rotational Stability of the Upper Body and Metabolic Energy Efficiency."** PMC11929735, 2025.

---

### 6.3 Cadência (Frequência de Passada)

#### O que é a cadência ideal?

| Perfil do Corredor | Cadência Típica |
|---|---|
| Iniciante / Recreativo | 150–165 spm |
| Intermediário | 165–175 spm |
| Avançado / Elite | 175–185+ spm |

> **⚠️ Crítica fundamental:** A cadência varia diretamente com o pace (Velocidade = Cadência × Comprimento de Passada). **Esta métrica é apenas informativa e NÃO deve penalizar a nota geral.** Um corredor lento com 160 spm pode estar perfeitamente saudável. A simetria entre lados é clinicamente mais relevante que o valor absoluto.

#### Como calcular

```
Cadência (spm) = (Número de contatos detectados / Duração do segmento em segundos) × 60
```

Usar o contato do pé direito apenas e multiplicar por 2. O FPS do vídeo é extraído automaticamente dos metadados.

#### Referência científica
- Bramah, C. et al. **"The Influence of Running Cadence on Biomechanics and Injury Prevention."** PMC12440572, 2025.
- Fletcher, J.R. **"The Effect of Running Speed on Cadence and Running Kinetics."** PMC12222555, 2025.

---

### 6.4 Inclinação do Tronco (Trunk Lean)

#### O que é a inclinação ideal?

| Inclinação | Interpretação |
|---|---|
| 0° a 3° (muito ereto) | Possível aumento de forças de frenagem |
| **4° a 8° (ideal)** | Melhor equilíbrio entre propulsão e economia |
| 9° a 14° (levemente excessivo) | Aumenta carga no quadril, reduz levemente a economia |
| >15° (excessivo) | Reduz significativamente a economia; sobrecarga no quadril |

> **⚠️ Crítica:** A inclinação anterior reduz o carregamento do joelho mas reduz a economia de corrida — trade-off importante. A faixa 4°–8° é a referência padrão. Acima de 15° é o gatilho para penalização crítica.

#### Como calcular (keypoints COCO)

```
Ponto_topo_tronco  = média(ombro_esq[5], ombro_dir[6])
Ponto_base_tronco  = média(quadril_esq[11], quadril_dir[12])
Vetor_tronco       = Ponto_topo - Ponto_base
Ângulo_inclinação  = arctan(ΔX / ΔY)
```

Calcular a média sobre múltiplos frames em fase de apoio médio para maior estabilidade.

#### Referência científica
- Teng, H.L. et al. **"The effect of forward postural lean on running economy, kinematics, and muscle activation."** PMC11135760, 2024.
- Paquette, M.R. et al. **"Managing lower extremity loading in distance running by altering sagittal plane trunk leaning."** Journal of Sport and Health Science, 2024.

---

### 6.5 Overstriding (Pisada à Frente do Centro de Massa)

#### O que é overstriding?

Overstriding ocorre quando o pé pousa significativamente à frente do Centro de Massa (CoM). Esse padrão:
- Cria uma **força de frenagem** a cada passada (o corredor freia a si mesmo).
- Aumenta o pico de força de reação ao solo.
- Eleva o risco de lesões (síndrome de estresse tibial, lesão de isquiotibiais, dor patelofemoral).

O pé no contato inicial deve pousar diretamente abaixo ou levemente à frente do quadril ipsilateral. Deslocamento horizontal >15–20 cm em relação ao CoM é considerado overstriding problemático.

> **⚠️ Crítica:** Esta é **uma das melhores métricas do sistema** — bem embasada, diretamente relacionada a lesões e extraível por visão computacional. O tipo de pisada (heel/mid/forefoot) importa menos do que *onde* o pé cai em relação ao CoM.

#### Como calcular (keypoints COCO)

```
CoM_X = (quadril_esq_X[11] + quadril_dir_X[12]) / 2

# No frame de contato inicial (tornozelo na altitude mínima):
Overstriding_px = tornozelo_X - CoM_X

# Conversão pixels → cm via altura do usuário:
Fator_Escala    = Altura_real_cm / Altura_em_pixels
Overstriding_cm = Overstriding_px × Fator_Escala
```

> **Calibração:** O Fator de Escala usa a altura cadastrada pelo usuário no momento do registro. Não é necessária uma etapa de calibração ativa — a altura do cadastro é suficiente para o MVP.

**Thresholds:**
- `< 5 cm` → Ideal
- `5–15 cm` → Atenção
- `> 15 cm` → Crítico

#### Referência científica
- Willy, R.W. et al. **"Effects of stride frequency and foot position at landing on braking force, hip torque, impact peak force and metabolic cost."** PubMed 26538175, 2015.
- Neal, B.S. et al. **"An Evidence-Based Videotaped Running Biomechanics Analysis."** PMC4714754, 2016.

---

### 6.6 Tempo de Contato com o Solo (TCS)

#### O que é o TCS ideal?

O TCS varia com o pace e **deve ser sempre contextualizado** com o pace informado pelo usuário:

| Perfil | TCS Típico |
|---|---|
| Corredores recreativos (pace lento) | 250–300 ms |
| Corredores intermediários | 200–250 ms |
| Corredores avançados | 180–220 ms |
| Atletas de elite | ~155–180 ms |

> **⚠️ Crítica importante:** A relação TCS-economia é mais complexa do que parece. Um estudo de 2024 (PubMed 38349337) mostrou que **TCS mais longo pode estar associado a melhor economia em atletas treinados**. A visão de "quanto menor melhor" é incorreta. O que é clinicamente mais relevante é a **simetria TCS esq vs dir** (assimetria >10% é preditor robusto de lesão). O sistema deve priorizar a assimetria como critério de penalização, e classificar o valor absoluto apenas em relação ao pace informado.

> **Dependência de FPS:** O TCS é calculado em frames. Um vídeo com menos de 60 FPS produz resolução temporal de >33 ms por frame, que é insuficiente para medir TCS com precisão. **Vídeos com FPS < 60 são bloqueados antes do processamento.**

#### Como calcular (keypoints COCO)

```
# Contato inicial: tornozelo atinge Y máximo (altitude mínima na imagem)
# Saída do pé: tornozelo começa elevação contínua

TCS_ms = (frames_de_contato / FPS_do_vídeo) × 1000
```

FPS extraído automaticamente dos metadados do vídeo pelo backend.  
Calculado separadamente para pé esquerdo e direito.

#### Referência científica
- Lee, J. et al. **"Kinetic and Spatiotemporal Characteristics of Running."** PMC11215647, 2024.
- Udofa, A.B. et al. **"Running Speed Can Be Predicted from Foot Contact Time."** PLOS One, 2016.
- Morin, J.B. et al. **"Humans Optimize Ground Contact Time and Leg Stiffness."** Frontiers in Sports and Active Living, 2019.
- Garcia-Pinillos, F. et al. **"Ground Contact Time Imbalances Strongly Related to Impaired Running Economy."** PMC7241633, 2020.

---

### 6.7 Oscilação Vertical

#### O que é a oscilação vertical ideal?

| Oscilação | Interpretação |
|---|---|
| **< 5 cm** | Insuficiente — passada "arrastada", sem fase de voo eficiente |
| **5 – 10 cm (ideal)** | Equilíbrio ótimo entre fase de voo e gasto energético |
| **> 10 cm** | Excessiva — desperdício de energia vertical, fadiga precoce |

#### Como calcular (keypoints COCO)

O Centro de Massa é aproximado pelo ponto médio dos quadris (keypoints 11 e 12):

```
# Passo 1: Y do CoM por frame
Y_CoM[frame] = (Y_quadril_esq[11] + Y_quadril_dir[12]) / 2

# Passo 2: Por ciclo de passada, calcular ΔY
# (Y cresce para baixo em coords de imagem)
ΔY_pixels = |Y_máximo_numérico - Y_mínimo_numérico|

# Passo 3: Converter para cm
Fator_Escala   = Altura_real_cm / Altura_em_pixels
Oscilação_cm   = ΔY_pixels × Fator_Escala
```

Calcular a média sobre todos os ciclos detectados no vídeo.

#### Referência científica
- Moore, I.S. **"Is There an Economical Running Technique? A Review of Modifiable Biomechanical Factors."** PMC4887549, 2016.
- Nummela, A. **"Factors Related to Top Running Speed and Economy."** PubMed 17549657, 2007.

---

### 6.8 Índice de Simetria (Esq vs Dir)

#### Por que incluir?

A assimetria entre lados é um dos **preditores mais robustos de lesão por overuse** na biomecânica de corrida. Qualquer assimetria acima de 10% em métricas como TCS, ângulo do joelho ou oscilação vertical entre os lados é clinicamente significativa.

#### Como calcular

Para cada métrica calculada bilateralmente:

```
IS = |Valor_esq - Valor_dir| / ((Valor_esq + Valor_dir) / 2) × 100%
```

**Thresholds:**
- `< 5%` → Simétrico (ideal)
- `5–10%` → Levemente assimétrico (atenção)
- `> 10%` → Assimetria significativa (crítico — risco de lesão)

Calcular para: TCS, ângulo do joelho no contato inicial e oscilação vertical.

#### Referência científica
- Patterson, K.K. et al. **"Evaluation of gait symmetry after stroke."** PubMed 19932621, 2009.
- Garcia-Pinillos, F. et al. **"Ground Contact Time Imbalances Strongly Related to Impaired Running Economy."** PMC7241633, 2020.

---

## 7. User Stories

### US-001: Cadastro e autenticação do usuário
**Descrição:** Como corredor, quero criar uma conta e fazer login para acessar minhas análises e histórico.

**Acceptance Criteria:**
- [ ] Formulário de cadastro com campos: nome, e-mail, senha, altura (cm), peso (kg), nível de experiência
- [ ] Campo `altura_cm` é obrigatório (usado para calibração de pixels→cm)
- [ ] Senha armazenada com hash seguro (bcrypt)
- [ ] E-mail duplicado retorna erro descritivo, não 500
- [ ] Login bem-sucedido estabelece sessão e redireciona ao Dashboard
- [ ] Typecheck/lint passa

---

### US-002: Validações de vídeo no frontend antes do upload
**Descrição:** Como corredor, quero ser avisado imediatamente se meu vídeo não está dentro dos requisitos, antes de gastar tempo com o upload.

**Acceptance Criteria:**
- [ ] Frontend lê metadados do arquivo localmente (sem upload) antes de liberar o envio
- [ ] **Bloqueia vídeos com duração < 30 segundos** → mensagem: "Vídeo muito curto — grave pelo menos 30 segundos de corrida contínua"
- [ ] **Bloqueia vídeos com duração > 3 minutos** → mensagem: "Vídeo muito longo — envie no máximo 3 minutos"
- [ ] **Bloqueia vídeos com resolução abaixo de 480p** (largura < 640px ou altura < 480px) → mensagem: "Qualidade insuficiente — grave em no mínimo 480p"
- [ ] **Exibe alerta para vídeos com FPS < 60** → o backend fará a validação definitiva e retornará erro se confirmado; o frontend exibe a mensagem de bloqueio retornada pela API
- [ ] Botão de envio permanece desabilitado até todas as validações passarem e o pace ser preenchido (ver US-017)
- [ ] Typecheck/lint passa
- [ ] Verificar no browser que cada mensagem de bloqueio é exibida corretamente para cada caso

---

### US-003: Informar pace antes do envio do vídeo
**Descrição:** Como corredor, quero informar meu pace ou velocidade antes de enviar o vídeo para que o sistema contextualize corretamente o TCS e outras métricas dependentes de velocidade.

**Acceptance Criteria:**
- [ ] Tela de upload exibe dois modos de entrada: **Pace (min:ss / km)** e **Velocidade (km/h)**
- [ ] Os dois campos são vinculados e se convertem em tempo real ao editar qualquer um deles
- [ ] Fórmulas de conversão:
  - Pace → km/h: `km_h = 60 / pace_em_minutos_decimais`
  - km/h → Pace: `pace_min = floor(60 / km_h)` ; `pace_seg = round((60 / km_h % 1) × 60)`
  - Exemplo: 5:30/km ↔ 10.9 km/h
- [ ] Faixa aceita: Pace entre 3:00/km e 12:00/km (5–20 km/h fora dessa faixa é rejeitado com mensagem)
- [ ] Envio do vídeo bloqueado até o pace ser preenchido
- [ ] Valor do pace salvo e associado à `SESSAO_ANALISE`
- [ ] Typecheck/lint passa
- [ ] Verificar no browser que a conversão em tempo real funciona e que o botão permanece bloqueado sem pace

---

### US-004: Upload de vídeo e início do processamento
**Descrição:** Como corredor autenticado, quero enviar o vídeo após preencher o pace para que o sistema inicie a análise.

**Acceptance Criteria:**
- [ ] Frontend envia `form-data` com o vídeo e o campo `pace_min_km`
- [ ] Backend valida perspectiva lateral após receber o vídeo (proporção ombro/quadril); vídeo de frente ou costas retorna `422` com mensagem de instrução clara
- [ ] Backend valida FPS ≥ 60; vídeo com FPS insuficiente retorna `422` com mensagem: "FPS do vídeo insuficiente — grave com pelo menos 60 FPS para garantir precisão na análise"
- [ ] `video_id` retornado imediatamente após upload bem-sucedido
- [ ] Processamento iniciado de forma assíncrona via FastAPI Background Tasks (usuário não fica bloqueado)
- [ ] Vídeo descartado da memória após extração dos keypoints
- [ ] Typecheck/lint passa
- [ ] Verificar no browser que o fluxo de upload funciona e os erros da API são exibidos corretamente

---

### US-005: Acompanhamento do status do processamento
**Descrição:** Como corredor, quero ver o progresso do processamento do meu vídeo em tempo real para que eu saiba quando a análise estará pronta e não fique sem feedback durante a espera.

**Acceptance Criteria:**
- [ ] Barra de progresso ou status textual exibido após upload
- [ ] Status consultado via polling periódico (`GET /api/videos/{id}/status`)
- [ ] Mensagens descritivas por etapa: "Validando perspectiva", "Detectando pose com YOLOv8", "Calculando métricas", "Concluído"
- [ ] Ao status "Concluído", interface redireciona automaticamente para os resultados
- [ ] Typecheck/lint passa
- [ ] Verificar no browser que a barra de progresso atualiza corretamente

---

### US-006: Visualizar diagnóstico simplificado
**Descrição:** Como corredor amador, quero ver os resultados em linguagem acessível para entender o que preciso melhorar.

**Acceptance Criteria:**
- [ ] Nota geral da corrida exibida (ex: 7.2/10)
- [ ] Recomendações categorizadas por severidade: Informativo (verde), Atenção (amarelo), Crítico (vermelho)
- [ ] Cada recomendação tem descrição textual clara e acionável (ex: "Seu joelho está muito rígido no impacto — tente aterrissar com o joelho levemente flexionado")
- [ ] Métricas apresentadas visualmente (não apenas números brutos)
- [ ] Typecheck/lint passa
- [ ] Verificar no browser que os cards de feedback renderizam corretamente

---

### US-007: Visualizar dados biomecânicos brutos
**Descrição:** Como corredor avançado ou profissional de saúde, quero acessar os dados técnicos completos para análise aprofundada.

**Acceptance Criteria:**
- [ ] Gráficos de séries temporais para cada métrica (ex: ângulo do joelho frame a frame)
- [ ] Dados acessíveis via `GET /api/analysis/{id}/raw`
- [ ] Visualização de assimetria entre lados esq/dir
- [ ] Typecheck/lint passa
- [ ] Verificar no browser que os gráficos renderizam corretamente com os dados reais

---

### US-008: Histórico de evolução
**Descrição:** Como corredor, quero ver minha evolução ao longo do tempo comparando análises anteriores.

**Acceptance Criteria:**
- [ ] Timeline com todas as sessões anteriores (data, pace, nota geral, status)
- [ ] Clique em qualquer sessão abre detalhes (US-006 ou US-007)
- [ ] Paginação funcional (`?page=1&limit=10`)
- [ ] Typecheck/lint passa
- [ ] Verificar no browser que o histórico carrega e pagina corretamente

---

### US-009: Pipeline de detecção de pose (YOLOv8-pose)
**Descrição:** Como desenvolvedor, preciso que o módulo de CV extraia corretamente os 17 keypoints COCO com YOLOv8-pose, frame a frame, para que o motor biomecânico tenha dados de entrada precisos e confiáveis.

**Acceptance Criteria:**
- [ ] Modelo YOLOv8-pose carregado e configurado
- [ ] 17 keypoints extraídos por frame com índices COCO padrão
- [ ] Confiança mínima por keypoint definida (score > 0.5); keypoints abaixo do threshold são descartados
- [ ] Filtro de suavização aplicado às coordenadas brutas (Kalman ou média móvel) para reduzir jitter
- [ ] Se mais de 50% dos frames do vídeo tiverem a maioria dos keypoints com score < 0.5, a análise é **invalidada completamente** e o status da sessão é atualizado para `"erro_qualidade_keypoints"` com mensagem ao usuário: "Não foi possível analisar o vídeo — iluminação insuficiente ou corredor fora do quadro. Por favor, envie um novo vídeo."
- [ ] Se o YOLOv8-pose detectar **mais de uma pessoa** em mais de 30% dos frames, a análise é **invalidada completamente** e o status é atualizado para `"erro_multiplas_pessoas"` com mensagem: "Mais de uma pessoa detectada no vídeo. Grave em um local sem outras pessoas no quadro e envie novamente."
- [ ] Em ambos os casos de invalidação, nenhuma METRICA ou RECOMENDACAO é persistida para a sessão
- [ ] FPS extraído automaticamente dos metadados do arquivo de vídeo
- [ ] Typecheck/lint passa

---

### US-010: Motor Biomecânico — Ângulo do Joelho
**Descrição:** Como desenvolvedor, preciso calcular o ângulo do joelho esquerdo e direito frame a frame para identificar rigidez ou colapso articular no contato com o solo.

**Acceptance Criteria:**
- [ ] Ângulo calculado usando keypoints quadril (11/12), joelho (13/14) e tornozelo (15/16) via produto escalar
- [ ] Calculado separadamente para lado esquerdo e direito a cada frame válido
- [ ] Contato inicial identificado quando tornozelo atinge Y máximo (altitude mínima)
- [ ] Ângulo no contato inicial armazenado como valor primário de análise
- [ ] Resultado salvo na tabela METRICA com `tipo = "angulo_joelho_esq"` / `"angulo_joelho_dir"`, `unidade = "graus"`
- [ ] Typecheck/lint passa

---

### US-011: Motor Biomecânico — Ângulo do Cotovelo
**Descrição:** Como desenvolvedor, preciso calcular o ângulo do cotovelo esquerdo e direito para identificar balanço de braço inadequado.

**Acceptance Criteria:**
- [ ] Ângulo calculado usando keypoints ombro (5/6), cotovelo (7/8) e pulso (9/10) via produto escalar
- [ ] Calculado separadamente para lado esquerdo e direito
- [ ] Valor médio calculado ao longo de múltiplos ciclos de passada
- [ ] Resultado salvo na tabela METRICA com `tipo = "angulo_cotovelo_esq"` / `"angulo_cotovelo_dir"`, `unidade = "graus"`
- [ ] Typecheck/lint passa

---

### US-012: Motor Biomecânico — Cadência
**Descrição:** Como desenvolvedor, preciso calcular a cadência do corredor para que o usuário tenha essa informação disponível como dado de contexto, sem que ela distorça a nota geral por variar com o pace.

**Acceptance Criteria:**
- [ ] Evento de contato inicial detectado por pé (tornozelo atinge altitude mínima)
- [ ] `Cadência (spm) = (nº de contatos / duração em segundos) × 60`
- [ ] FPS extraído dos metadados do vídeo
- [ ] Resultado salvo na tabela METRICA com `tipo = "cadencia"`, `unidade = "spm"`
- [ ] Flag "apenas_informativa = true" associada à métrica, garantindo que a camada de pontuação a ignore
- [ ] Typecheck/lint passa

---

### US-013: Motor Biomecânico — Inclinação do Tronco
**Descrição:** Como desenvolvedor, preciso calcular o ângulo de inclinação anterior do tronco para identificar postura inadequada.

**Acceptance Criteria:**
- [ ] Topo do tronco = média dos ombros (keypoints 5 e 6)
- [ ] Base do tronco = média dos quadris (keypoints 11 e 12)
- [ ] `Ângulo_inclinação = arctan(ΔX / ΔY)` em relação à vertical
- [ ] Média calculada sobre frames em fase de apoio médio
- [ ] Resultado salvo na tabela METRICA com `tipo = "inclinacao_tronco"`, `unidade = "graus"`
- [ ] Typecheck/lint passa

---

### US-014: Motor Biomecânico — Overstriding
**Descrição:** Como desenvolvedor, preciso detectar e quantificar a pisada à frente do centro de massa para identificar padrão de frenagem.

**Acceptance Criteria:**
- [ ] CoM_X = média horizontal dos quadris (keypoints 11 e 12) no frame de contato inicial
- [ ] `Overstriding_px = tornozelo_X - CoM_X`
- [ ] `Fator_Escala = Altura_real_cm / Altura_em_pixels` (via altura cadastrada no registro)
- [ ] `Overstriding_cm = Overstriding_px × Fator_Escala`
- [ ] Resultado salvo na tabela METRICA com `tipo = "overstriding_esq"` / `"overstriding_dir"`, `unidade = "cm"`
- [ ] Typecheck/lint passa

---

### US-015: Motor Biomecânico — Tempo de Contato com o Solo (TCS)
**Descrição:** Como desenvolvedor, preciso calcular o TCS de cada pé separadamente e contextualizá-lo com o pace informado pelo usuário para que a métrica seja exibida com referência adequada e para que a simetria entre lados possa ser derivada como indicador de risco de lesão.

**Acceptance Criteria:**
- [ ] Pace da `SESSAO_ANALISE` disponível para esta etapa do pipeline
- [ ] Contato inicial: tornozelo atinge Y máximo; saída do pé: tornozelo inicia elevação
- [ ] `TCS_ms = (frames_de_contato / FPS) × 1000`
- [ ] Calculado separadamente para pé esquerdo e direito
- [ ] TCS absoluto salvo na tabela METRICA com `tipo = "tcs_esq"` / `"tcs_dir"`, `unidade = "ms"`
- [ ] Flag `apenas_informativo = true` associada ao TCS absoluto, garantindo que a camada de pontuação o ignore
- [ ] O pace da sessão é exibido junto ao TCS nos resultados para contexto do usuário
- [ ] Typecheck/lint passa

---

### US-016: Motor Biomecânico — Oscilação Vertical
**Descrição:** Como desenvolvedor, preciso calcular a oscilação vertical do centro de massa por ciclo de passada e convertê-la para centímetros para que o sistema consiga identificar desperdício de energia vertical e oferecer feedback sobre a eficiência da corrida.

**Acceptance Criteria:**
- [ ] `Y_CoM[frame] = (Y_quadril_esq[11] + Y_quadril_dir[12]) / 2`
- [ ] Por ciclo: `ΔY_pixels = |Y_máximo_numérico - Y_mínimo_numérico|`
- [ ] `Oscilação_cm = ΔY_pixels × Fator_Escala` (Fator via altura do usuário)
- [ ] Média sobre todos os ciclos detectados
- [ ] Resultado salvo na tabela METRICA com `tipo = "oscilacao_vertical"`, `unidade = "cm"`
- [ ] Typecheck/lint passa

---

### US-017: Motor Biomecânico — Índice de Simetria
**Descrição:** Como desenvolvedor, preciso calcular o índice de simetria entre lados esquerdo e direito para TCS, ângulo do joelho e oscilação, pois assimetria > 10% é preditor clínico de lesão.

**Acceptance Criteria:**
- [ ] `IS = |Valor_esq - Valor_dir| / ((Valor_esq + Valor_dir) / 2) × 100%`
- [ ] Calculado para: TCS, ângulo do joelho no contato inicial e oscilação vertical
- [ ] Resultado salvo na tabela METRICA com `tipo = "simetria_tcs"` / `"simetria_joelho"` / `"simetria_oscilacao"`, `unidade = "%"`
- [ ] Typecheck/lint passa

---

### US-018: Geração de recomendações e nota geral
**Descrição:** Como desenvolvedor, preciso comparar as métricas calculadas com os parâmetros ideais (Seção 9) e gerar recomendações priorizadas com uma nota geral para que o corredor receba um diagnóstico claro e acionável ao final da análise.

**Acceptance Criteria:**
- [ ] Tabela de thresholds implementada conforme Seção 9 deste PRD
- [ ] Cada métrica fora dos limites gera ao menos uma RECOMENDACAO com categoria e severidade
- [ ] Nota geral calculada com base nas penalizações
- [ ] Recomendações persistidas na tabela RECOMENDACAO
- [ ] Cadência **não penaliza** a nota geral (flag `apenas_informativa`)
- [ ] Typecheck/lint passa

---

## 8. Requisitos Funcionais

- **FR-01:** O sistema deve suportar autenticação com e-mail e senha, com hash seguro (bcrypt).
- **FR-02:** O campo `altura_cm` é obrigatório no cadastro; é utilizado para calibração do fator de escala pixels→cm.
- **FR-03:** O modelo de detecção de pose é o **YOLOv8-pose** (treinado no dataset COCO, 17 keypoints).
- **FR-04:** O processamento assíncrono deve ser implementado com **FastAPI Background Tasks**.
- **FR-05:** O sistema deve validar a perspectiva lateral do vídeo antes de iniciar o pipeline completo. Vídeos de frente ou costas devem ser rejeitados com mensagem clara.
- **FR-06:** Vídeos com **FPS < 60** devem ser bloqueados pelo backend com mensagem de erro descritiva.
- **FR-07:** O frontend deve bloquear vídeos com **duração < 30 segundos**, lendo metadados localmente antes do upload.
- **FR-08:** O frontend deve bloquear vídeos com **duração > 3 minutos**, lendo metadados localmente antes do upload.
- **FR-09:** O frontend deve bloquear vídeos com **resolução < 480p** (< 640×480px), lendo metadados localmente antes do upload.
- **FR-10:** O upload deve ser bloqueado até o usuário informar o **pace ou velocidade**. O sistema deve aceitar ambos os formatos e converter em tempo real.
- **FR-11:** O pace informado deve ser persistido em `SESSAO_ANALISE.pace_min_km` e utilizado para contextualizar a classificação do TCS.
- **FR-12:** O vídeo original deve ser descartado após a extração dos keypoints. Nenhum frame é persistido.
- **FR-13:** Um filtro de suavização deve ser aplicado às coordenadas brutas antes do cálculo de métricas.
- **FR-14:** Keypoints com score de confiança < 0.5 devem ser descartados dos cálculos.
- **FR-15:** O FPS do vídeo deve ser extraído automaticamente dos metadados pelo backend.
- **FR-16:** A cadência e o **TCS absoluto** devem ser calculados e exibidos mas **não devem impactar a nota geral**. A evidência científica atual (PubMed 38349337, 2024) não sustenta o uso do TCS absoluto como critério de pontuação. O que é pontuado é exclusivamente a **simetria TCS** entre lados esquerdo e direito.
- **FR-17:** O fator de escala pixels→cm é calculado com base na `altura_cm` do cadastro do usuário. Nenhuma etapa de calibração ativa é necessária para o MVP.
- **FR-18:** As recomendações devem ter três níveis de severidade: Informativo, Atenção, Crítico.
- **FR-19:** O sistema deve expor dois modos de visualização: simplificado (amador) e bruto (avançado).
- **FR-20:** O histórico de sessões deve ser paginável via query params (`?page` e `?limit`).
- **FR-21:** Apenas usuários autenticados devem acessar rotas de análise e histórico.
- **FR-22:** Se mais de 50% dos frames do vídeo apresentarem confiança de keypoints globalmente baixa (score < 0.5 na maioria dos keypoints), a análise deve ser **invalidada completamente**. O sistema atualiza o status para `"erro_qualidade_keypoints"` e solicita ao usuário que envie um novo vídeo com melhor iluminação e corredor dentro do quadro.
- **FR-23:** Se o YOLOv8-pose detectar mais de uma pessoa em mais de 30% dos frames, a análise deve ser **invalidada completamente**. O sistema atualiza o status para `"erro_multiplas_pessoas"` e solicita ao usuário que grave em local sem outras pessoas no quadro.

---

## 9. Tabela de Thresholds para Pontuação

| Métrica | Ideal | Atenção | Crítico |
|---|---|---|---|
| Ângulo joelho (contato inicial) | 15°–25° flexão | 10°–15° ou 25°–35° | <10° ou >35° |
| Ângulo cotovelo | 70°–110° | 60°–70° ou 110°–120° | <60° ou >120° |
| Inclinação do tronco | 4°–8° | 1°–4° ou 8°–15° | <1° ou >15° |
| Overstriding | <5 cm | 5–15 cm | >15 cm |
| Simetria TCS (esq vs dir) | <5% | 5%–10% | >10% |
| Oscilação vertical | 5–10 cm | 3–5 cm ou 10–13 cm | <3 cm ou >13 cm |
| Simetria (joelho, oscilação) | <5% | 5%–10% | >10% |
| TCS absoluto | Apenas informativo¹ | — | — |
| Cadência | Apenas informativa | — | — |

> ¹ **TCS absoluto é apenas informativo:** Um estudo de 2024 (PubMed 38349337) demonstrou que TCS mais longo pode estar associado a melhor economia de corrida em atletas treinados, contradizendo a visão simplista de "quanto menor, melhor". O TCS varia com o pace e não possui um threshold universal confiável. O que é clinicamente válido é a **simetria entre lados** (linha acima), que independe desse debate. O TCS absoluto é exibido contextualizado pelo pace informado, mas não penaliza a nota geral.

> **Nota:** Os thresholds do ângulo do joelho são fixos nesta versão. Adaptar por faixa de pace é uma melhoria futura documentada na Seção 11.

---

## 10. Não-Goals (Fora de Escopo — MVP)

- Processamento em tempo real (escopo limitado a vídeos pré-gravados).
- Análise de corrida em esteira.
- Detecção de tipo de pisada (heel/mid/forefoot) como métrica primária.
- Sugestões de calçados ou equipamentos.
- Integração com wearables (GPS watches, sensores de frequência cardíaca).
- Análise de múltiplas pessoas no mesmo vídeo.
- Aplicativo mobile nativo (o MVP é web-first).
- Survey de satisfação ou validação de feedback com o usuário.
- Thresholds do joelho variáveis por pace (melhoria futura — ver Seção 11).

---

## 11. Melhorias Futuras (Pós-MVP)

- **Thresholds do joelho por pace:** Adaptar os limites do ângulo do joelho para diferentes faixas de velocidade (lento / moderado / rápido). A literatura confirma que os ângulos variam com o pace, mas a implementação aumenta consideravelmente a complexidade do motor biomecânico e foi adiada para uma versão futura.
- **Processamento em nuvem:** Caso o projeto evolua além do MVP acadêmico, será necessário avaliar infraestrutura de nuvem e políticas de privacidade compatíveis com LGPD.
- **Suporte a vídeos com FPS < 60:** Implementar interpolação de frames ou usar modelos especializados para vídeos de menor framerate.

---

## 12. Convenções de Desenvolvimento

> **Importante para agentes e desenvolvedores:** Esta seção define regras obrigatórias de workflow que devem ser seguidas em toda implementação deste projeto.

### Commits

- Seguir o padrão **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `style:`, `perf:`, `ci:`
- O commit deve conter **apenas o subject line** — sem corpo, sem descrição, sem linhas adicionais
- **Nunca** adicionar co-autoria (`Co-Authored-By`) ou qualquer atribuição de ferramenta
- Usar sempre o usuário git configurado localmente no repositório, sem modificá-lo

**Exemplos corretos:**
```
feat: add knee angle calculation to biomechanical engine
fix: correct overstriding threshold from 20cm to 15cm
chore: add YOLOv8-pose dependency to requirements.txt
docs: update API endpoint description for video upload
refactor: extract scale factor calculation to utils module
test: add unit tests for symmetry index calculation
```

**Exemplos incorretos:**
```
# ❌ Sem prefixo
add knee angle calculation

# ❌ Com descrição/corpo
feat: add knee angle calculation

Implements the knee angle using hip, knee and ankle keypoints.

# ❌ Com co-autoria
feat: add knee angle calculation

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 13. Considerações de Design

- Interface deve ser **simples e intuitiva**, usável em condições de cansaço pós-treino.
- Resultados simplificados devem usar linguagem não técnica com feedback visual (ícones, cores por severidade).
- Resultados brutos são opt-in — o usuário escolhe explicitamente ver os dados técnicos.
- A barra de progresso deve ter mensagens por etapa para reduzir ansiedade durante o processamento.
- As mensagens de bloqueio de vídeo (FPS, duração, resolução) devem ser claras e instruir o usuário sobre como corrigir o problema.

---

## 14. Considerações Técnicas

- **Modelo:** YOLOv8-pose (treinado no dataset COCO). Escolha definitiva para o MVP.
- **Async:** FastAPI Background Tasks — sem Redis ou Celery. Adequado para o escopo do MVP.
- **FPS:** Mínimo 60 FPS obrigatório. Validado pelo backend após receber o arquivo; FPS extraído dos metadados do vídeo.
- **Fator de escala:** Calculado a partir da `altura_cm` do cadastro. Validar que a altura está preenchida antes de iniciar cálculos que dependem de conversão.
- **Confiança dos keypoints:** Score mínimo de 0.5 por keypoint. Frames com keypoints críticos ausentes são descartados do cálculo mas não invalidam a análise.
- **Carga esperada (1 mês):** ~200 usuários × 3 sessões = 600 sessões → ~4.800 métricas → ~3.000 recomendações → total < 6 MB no PostgreSQL. Uma instância local é suficiente.
- **Subsample de frames:** Considerar processar 1 a cada 2 frames para reduzir custo computacional sem perda significativa de precisão (melhoria de performance).

---

## 15. Preocupações Transversais

- **Privacidade:** Vídeos processados localmente e descartados após extração de keypoints. Nenhum frame é persistido. Adequado ao escopo de MVP acadêmico.
- **Segurança:** Senhas com bcrypt, rotas protegidas por autenticação, controle de acesso por sessão ativa.
- **Confiabilidade:** A qualidade da análise depende da qualidade do vídeo (iluminação, ângulo, distância). O sistema deve comunicar essas limitações ao usuário e orientá-lo sobre como gravar corretamente.

---

## 16. Métricas de Sucesso

- Usuário consegue submeter vídeo e receber diagnóstico completo em menos de 5 minutos.
- Taxa de vídeos rejeitados pelas validações de frontend < 20% (indica que as instruções de gravação são claras).
- Assimetria TCS detectada corretamente em pelo menos 85% dos casos em dataset de teste.
- Nota geral de corrida possui correlação positiva com avaliação de pelo menos 2 treinadores (validação qualitativa).
- Nenhum vídeo persistido após processamento (privacidade).

---

## 17. Referências Científicas

1. NEAL, B.S. et al. **An Evidence-Based Videotaped Running Biomechanics Analysis.** British Journal of Sports Medicine, PMC4714754, 2016.
2. MOORE, I.S. **Is There an Economical Running Technique? A Review of Modifiable Biomechanical Factors.** Sports Medicine / PMC4887549, 2016.
3. LEE, J. et al. **Kinetic and Spatiotemporal Characteristics of Running During Regular Training Sessions for Collegiate Male Distance Runners.** PMC11215647, 2024.
4. UDOFA, A.B. et al. **Running Speed Can Be Predicted from Foot Contact Time during Outdoor over Ground Running.** PLOS One, 2016.
5. MORIN, J.B. et al. **Humans Optimize Ground Contact Time and Leg Stiffness to Minimize the Metabolic Cost of Running.** Frontiers in Sports and Active Living, 2019.
6. TENG, H.L. et al. **The effect of forward postural lean on running economy, kinematics, and muscle activation.** PMC11135760, 2024.
7. PAQUETTE, M.R. et al. **Managing lower extremity loading in distance running by altering sagittal plane trunk leaning.** Journal of Sport and Health Science, 2024.
8. WILLY, R.W. et al. **Effects of stride frequency and foot position at landing on braking force, hip torque, impact peak force and metabolic cost.** PubMed 26538175, 2015.
9. GARCIA-PINILLOS, F. et al. **Ground Contact Time Imbalances Strongly Related to Impaired Running Economy.** PMC7241633, 2020.
10. BRAMAH, C. et al. **The Influence of Running Cadence on Biomechanics and Injury Prevention: A Systematic Review.** PMC12440572, 2025.
11. MISU, S. et al. **Active Arm Swing During Running Improves Rotational Stability of the Upper Body and Metabolic Energy Efficiency.** PMC11929735, 2025.
12. PATTERSON, K.K. et al. **Evaluation of gait symmetry after stroke: a comparison of current methods and recommendations for standardization.** PubMed 19932621, 2009.
13. NUMMELA, A. **Factors Related to Top Running Speed and Economy.** International Journal of Sports Medicine, PubMed 17549657, 2007.
14. STANKIEWICZ, M. **Biomechanical differences between overground and treadmill running in professional runners: a pilot study.** PubMed 41384467, 2025.

---

## 18. Reformulação de UI/UX — v2

> **Contexto:** O frontend MVP (US-019 a US-027 entregues por Ralph) é funcionalmente completo, porém visualmente cru: única CSS file de 909 linhas, paleta accent roxa (`#aa3bff`) sobre fundo branco/quase-preto, sem app shell, sem sistema de design, sem branding, sem microinterações, h1 de 56px herdado do scaffold do Vite, layout com largura fixa de 1126px e bordas verticais decorativas que não fazem sentido em uma aplicação. Esta seção define a v2 da interface: uma direção visual esportiva, clara, acessível e coerente com os princípios do `interfaceguidelines.md` (na raiz do repositório), entregue por meio de um sistema de design + redesenho página a página.

> **Restrições explícitas do usuário:**
> - **Cores claras e esportivas** (referências: Strava, Nike Run Club, Garmin Connect, Whoop)
> - **NÃO usar preto puro nem roxo** — substituir o accent atual e o fundo dark por uma paleta com personalidade atlética
> - Manter a stack atual (React 19 + Vite + TypeScript + axios + recharts + react-router-dom) — sem novas libs pesadas; ícones via lib leve permitida (`lucide-react` ou similar inline-SVG)
> - Toda mudança visual deve respeitar `interfaceguidelines.md` — referência canônica para acessibilidade, motion, formulários e layout

---

### 18.1 Princípios de Design

1. **Esportivo, não corporativo.** A interface deve transmitir movimento e energia — usar verbos no imperativo nos CTAs ("Analisar corrida", "Ver evolução"), métricas grandes e legíveis (`tabular-nums`), microinterações que reforçam progresso (não puramente decorativas).
2. **Claro por padrão.** Tema light é o primário; tema dark é opt-in via `prefers-color-scheme` + toggle manual no header. Nada de fundo `#000` — o "preto" do tema escuro vira slate profundo, levemente azulado (`#0F172A`).
3. **Hierarquia primeiro, ornamento depois.** Tipografia, espaçamento e cor semântica fazem o trabalho pesado. Sombras e gradientes são acessórios, não estrutura.
4. **Acessibilidade não-negociável.** Todos os critérios MUST do `interfaceguidelines.md` são bloqueantes para aceite de qualquer US dessa seção. Contraste APCA Lc ≥ 60 para texto corrente, ≥ 75 para CTAs.
5. **Mobile-first real.** O usuário-alvo grava vídeos no celular e tipicamente abre o app no celular logo após o treino. O layout fixo de 1126px é eliminado; passa-se a um sistema fluido com breakpoints `≥ 640px (sm)`, `≥ 1024px (lg)`, `≥ 1280px (xl)`.
6. **Sem dead-ends.** Todo estado vazio, todo erro, toda tela final tem um próximo passo visível.

---

### 18.2 Paleta Proposta (Sport Light)

> Direção: **Emerald + Tangerine sobre Slate frio.** Verde-esmeralda transmite GO/forward/saúde; laranja-tangerina é energia/ritmo (substitui o roxo). Slate frio para neutros (substitui preto puro).

#### Cores de marca

| Token | Hex | Uso |
|---|---|---|
| `--brand-50` | `#ECFDF5` | Background de banner suave de sucesso |
| `--brand-100` | `#D1FAE5` | Hover sutil em chips/badges |
| `--brand-500` | `#10B981` | **Cor primária** — CTA, links ativos, gauge ideal |
| `--brand-600` | `#059669` | Hover/focus do CTA |
| `--brand-700` | `#047857` | Pressed/active do CTA |
| `--accent-400` | `#FB923C` | Highlight de energia, progresso ativo, botão secundário |
| `--accent-500` | `#F97316` | Hover do accent |
| `--accent-50` | `#FFF7ED` | Background suave do accent |

#### Neutros (Slate frio)

| Token | Hex | Uso |
|---|---|---|
| `--bg` | `#F8FAFC` | Fundo da app (light) |
| `--surface` | `#FFFFFF` | Cards, modais, inputs |
| `--surface-raised` | `#FFFFFF` + shadow-md | Cards elevados, dropdowns |
| `--border` | `#E2E8F0` | Bordas padrão |
| `--border-strong` | `#CBD5E1` | Bordas hover/focus |
| `--text` | `#0F172A` | Texto headline (NÃO usar `#000`) |
| `--text-muted` | `#475569` | Texto corrente (parágrafos, labels) |
| `--text-subtle` | `#94A3B8` | Texto secundário (hints, captions) |
| `--text-on-brand` | `#FFFFFF` | Texto sobre fundo `--brand-500` |

#### Cores semânticas

| Token | Hex | Uso |
|---|---|---|
| `--success` | `#10B981` | = `--brand-500` (verde) |
| `--warning` | `#F59E0B` | Banners de atenção, FPS marginal |
| `--danger` | `#EF4444` | Erros de validação, recomendações críticas |
| `--info` | `#0EA5E9` | Banners informativos, dicas |

#### Severidades de recomendação (alinhadas a `analysis_card`)

| Severidade | Background | Borda/ícone | Texto |
|---|---|---|---|
| Crítico | `#FEF2F2` | `#DC2626` | `#7F1D1D` |
| Atenção | `#FFFBEB` | `#D97706` | `#78350F` |
| Informativo | `#F0FDF4` | `#059669` | `#064E3B` |

#### Tema escuro (opt-in)

> Inverter para slate profundo, manter brand/accent vivos. **Nunca preto puro.**

| Token | Hex |
|---|---|
| `--bg` (dark) | `#0F172A` (slate-900) |
| `--surface` (dark) | `#1E293B` (slate-800) |
| `--border` (dark) | `#334155` (slate-700) |
| `--text` (dark) | `#F8FAFC` |
| `--text-muted` (dark) | `#CBD5E1` |
| `--brand-500` (dark) | `#34D399` (mais claro p/ contraste) |
| `--accent-400` (dark) | `#FDBA74` |

---

### 18.3 Tipografia

| Token | Família | Peso | Uso |
|---|---|---|---|
| `--font-display` | `'Space Grotesk', system-ui, sans-serif` | 500/600/700 | Headlines, números grandes, branding |
| `--font-body` | `'Inter', system-ui, sans-serif` | 400/500/600 | Texto corrente, labels, botões |
| `--font-mono` | `ui-monospace, 'JetBrains Mono', Consolas, monospace` | 400/500 | Números crus, código |

**Escala (mobile / desktop):**

| Token | Mobile | Desktop | Uso |
|---|---|---|---|
| `--text-xs` | 12px | 12px | Captions, badges |
| `--text-sm` | 14px | 14px | Texto secundário |
| `--text-base` | 16px | 16px | **Padrão (≥16px previne zoom no iOS)** |
| `--text-lg` | 18px | 18px | Texto destacado |
| `--text-xl` | 20px | 22px | Subtítulos |
| `--text-2xl` | 24px | 28px | h2 |
| `--text-3xl` | 28px | 36px | h1 da página |
| `--text-display` | 40px | 56px | Hero / nota geral |

Line-height: 1.2 para display/headlines; 1.5 para corpo. `font-variant-numeric: tabular-nums` em todos os números (notas, paces, ângulos, contadores).

Carregar fontes via `<link rel="preload" as="font" crossorigin>` com `font-display: swap`.

---

### 18.4 Tokens de Espaçamento, Raios, Sombras e Motion

**Espaçamento (escala 4px):** `--space-1: 4px`, `2: 8`, `3: 12`, `4: 16`, `5: 20`, `6: 24`, `8: 32`, `10: 40`, `12: 48`, `16: 64`, `20: 80`, `24: 96`.

**Raios (concêntricos, child ≤ parent):** `--radius-xs: 4px`, `--radius-sm: 6px`, `--radius-md: 10px`, `--radius-lg: 14px`, `--radius-xl: 20px`, `--radius-2xl: 28px`, `--radius-full: 9999px`.

**Sombras (ambient + direct, 2 camadas):**
- `--shadow-xs`: `0 1px 2px rgba(15,23,42,0.04)`
- `--shadow-sm`: `0 1px 3px rgba(15,23,42,0.08), 0 1px 2px rgba(15,23,42,0.04)`
- `--shadow-md`: `0 4px 8px rgba(15,23,42,0.06), 0 2px 4px rgba(15,23,42,0.04)`
- `--shadow-lg`: `0 12px 24px rgba(15,23,42,0.10), 0 4px 8px rgba(15,23,42,0.06)`
- `--shadow-focus`: `0 0 0 3px rgba(16,185,129,0.35)` (anel de foco verde-emerald)

**Motion:**
- `--duration-fast`: 120ms (hover de botões, mudança de cor)
- `--duration-base`: 200ms (transições padrão)
- `--duration-slow`: 320ms (entrada de cards, mudança de página)
- `--ease-standard`: `cubic-bezier(0.4, 0, 0.2, 1)`
- `--ease-out`: `cubic-bezier(0.16, 1, 0.3, 1)` — entradas
- `--ease-in`: `cubic-bezier(0.4, 0, 1, 1)` — saídas

Sempre animar **somente** `transform` e `opacity` (compositor-friendly). Nunca `width/height/top/left`. Listar propriedades explicitamente — proibido `transition: all`. Honrar `prefers-reduced-motion: reduce` removendo todas as animações decorativas.

---

### 18.5 Inventário do Que Está Quebrado Hoje

Mapeamento concreto do estado atual (referência para as US 18.6):

| Área | Problema atual | Onde está |
|---|---|---|
| Paleta | Roxo `#aa3bff` + dark `#16171d` (quase preto) | `client/src/index.css:7,37` |
| Layout | Largura fixa `1126px` + bordas verticais decorativas | `client/src/index.css:55-62` |
| H1 | 56px sempre — gigante para uma app | `client/src/index.css:80-87` |
| Sem app shell | Cada página é `<main>` solto, sem nav, sem logo, sem rota visível para Histórico | `client/src/App.tsx` (só `<Routes>`) |
| Sem branding | `<title>client</title>`, favicon padrão Vite, sem `theme-color` | `client/index.html` |
| Acessibilidade | Sem `lang="pt-BR"`, sem skip-to-content, sem `prefers-reduced-motion`, sem focus-visible global | `client/index.html`, `client/src/index.css` |
| Formulários | Sem `autocomplete` em todos os campos, sem foco no primeiro erro no submit, mensagem genérica em rede | `client/src/pages/LoginPage.tsx`, `SignupPage.tsx` |
| Upload | `<input type="file">` cru, sem drag-drop, sem preview, validações em texto solto | `client/src/pages/UploadPage.tsx` |
| Status | Barra de progresso minimalista, lista de etapas com bolinhas, sem estimativa de tempo, sem ilustração | `client/src/pages/StatusPage.tsx` |
| Diagnóstico | Cards lineares, gauge horizontal simples, sem iconografia por categoria, sem hero da nota | `client/src/pages/AnalysisPage.tsx` |
| Dados brutos | Recharts já presente, mas tabela densa sem filtros, sem destaque das anomalias | `client/src/pages/AnalysisRawPage.tsx` |
| Histórico | Lista textual, sem tendência visual (mini-sparkline da nota ao longo do tempo), sem filtros | `client/src/pages/HistoricoPage.tsx` |
| Sem componentes | 130 classes CSS espalhadas, lógica visual duplicada em cada página, sem `<Button>`, `<Field>`, `<Card>` | `client/src/index.css` (909 linhas) |
| Sem feedback | Nenhum sistema de toast, banners de erro são `<p>` com classe — não há `role="status"` polite global | (ausente) |
| Estados vazios/erro | Texto puro "Nenhum item." sem ilustração nem CTA de saída | `client/src/pages/HistoricoPage.tsx:90` |
| Performance | Fontes do sistema, mas h1 56px causa layout shift; nenhuma rota é lazy | `client/src/App.tsx` (imports síncronos) |
| Motion | Só 7 transitions no CSS inteiro, todas em `border-color`/`width`/`background-color` | `client/src/index.css:151,188,286,353,718,804,891` |

---

### 18.6 User Stories — Reformulação de UI/UX

> **IDs continuam a partir de US-027** (última US implementada por Ralph).
> Cada US tem prioridade, descrição, critérios de aceitação concretos com referência ao guideline aplicável (ex: `[guideline: Forms]`), e arquivos esperados. Nenhuma US deve ser fechada sem verificação visual no browser em viewport mobile (375×667) **e** desktop (1440×900).

---

#### US-028: Sistema de Design — Tokens Base (Cores, Tipografia, Espaçamento, Sombras, Motion)

**Prioridade:** P1 — fundacional, todas as outras dependem desta.

**Descrição:** Como desenvolvedor frontend, preciso de um conjunto de tokens CSS (custom properties) que centralizem cores, tipografia, espaçamento, raios, sombras e motion, para que cada componente/página consuma os mesmos valores e a paleta possa ser ajustada num único arquivo.

**Acceptance Criteria:**
- [ ] Criar `client/src/styles/tokens.css` com as variáveis CSS das seções 18.2, 18.3 e 18.4 deste PRD (tema light + bloco `@media (prefers-color-scheme: dark)`)
- [ ] Importar `tokens.css` antes de `index.css` em `client/src/main.tsx`
- [ ] `index.css` deixa de declarar cores/sombras hard-coded — todas as referências passam a usar `var(--token)`
- [ ] **Remover** `--accent: #aa3bff` e qualquer referência a roxo
- [ ] **Remover** background `#16171d` do tema dark — substituir por `#0F172A` (slate-900)
- [ ] Adicionar `<meta name="theme-color" content="#10B981">` no `client/index.html` (e o equivalente dark via `media`)
- [ ] Adicionar `color-scheme: light dark` no `:root` (já existe — manter)
- [ ] Carregar Inter + Space Grotesk via `<link rel="preload" as="font" crossorigin>` com `font-display: swap` [guideline: Performance]
- [ ] Documentar a paleta e os tokens em um `client/src/styles/README.md` (1 página, com a tabela da seção 18.2)
- [ ] `npm run build` passa (`tsc -b`)
- [ ] Verificar visualmente: abrir o app e confirmar que **nenhuma** cor roxa permanece e que o "preto" do dark virou slate

**Arquivos esperados:** `client/src/styles/tokens.css` (novo), `client/src/styles/README.md` (novo), `client/src/main.tsx` (import), `client/src/index.css` (refator), `client/index.html` (`theme-color` + preload de fontes).

---

#### US-029: App Shell — Top Nav, Logo, Branding, Footer Mínimo

**Prioridade:** P2.

**Descrição:** Como usuário autenticado, quero uma barra de navegação superior persistente com logo, links principais (Upload, Histórico) e menu de usuário (logout), para navegar entre as funcionalidades sem precisar digitar URLs.

**Acceptance Criteria:**
- [ ] Definir nome do produto (sugestões: "Stride", "Cadence", "PaceLab" — usuário decide; manter o decidido em `client/src/branding.ts` como constante)
- [ ] Criar `<AppShell>` em `client/src/components/AppShell.tsx` com top nav fixa (height 64px, `box-shadow: var(--shadow-sm)`, `bg: var(--surface)`)
- [ ] Logo SVG inline à esquerda (símbolo abstrato de movimento — pode ser geométrico simples; salvar em `client/src/components/Logo.tsx`)
- [ ] Links de navegação primários: **Análise** (`/upload`) e **Histórico** (`/historico`) — `<NavLink>` do react-router com `aria-current="page"` quando ativo
- [ ] Menu do usuário à direita: avatar circular com iniciais do `name` (de `useAuth()`) + dropdown com **Sair** (logout)
- [ ] Em viewport `< 640px`, transformar em hamburger menu (`<dialog>` ou drawer com `inert` aplicado ao body quando aberto) [guideline: Touch & Drag]
- [ ] Atualizar `<title>` por rota via `useEffect` em cada página (ex: "Análise — {brand}", "Histórico — {brand}") [guideline: Content & Accessibility]
- [ ] Atualizar `client/index.html`: `<html lang="pt-BR">`, `<title>{brand}</title>`, favicon SVG novo (substituir o do Vite — pode ser o próprio Logo em SVG)
- [ ] App shell envolve TODAS as rotas privadas (Upload, Status, Analysis, AnalysisRaw, Histórico). Login/Signup ficam fora (apenas card centralizado + branding sutil)
- [ ] Footer mínimo (uma linha, `<footer>`) com créditos e link para "Sobre" (placeholder)
- [ ] Skip-to-content link como primeiro elemento focável no body [guideline: Content & Accessibility]
- [ ] Hit targets do menu mobile ≥ 44px [guideline: Targets & Input]
- [ ] `npm run build` passa
- [ ] Verificar no browser em mobile (375px) e desktop (1440px) que a nav é usável em ambos

**Arquivos esperados:** `client/src/components/AppShell.tsx` (novo), `client/src/components/Logo.tsx` (novo), `client/src/components/UserMenu.tsx` (novo), `client/src/branding.ts` (novo), `client/src/App.tsx` (envolver rotas privadas), `client/index.html`, `client/public/favicon.svg`.

---

#### US-030: Acessibilidade Base — Focus, Reduced-Motion, Skip Link, Hierarquia

**Prioridade:** P3.

**Descrição:** Como usuário com necessidades de acessibilidade (teclado, leitor de tela, sensibilidade a movimento), preciso que todos os fundamentos de a11y do `interfaceguidelines.md` estejam respeitados em toda a aplicação.

**Acceptance Criteria:**
- [ ] Estilo global de `:focus-visible` consistente em **todo** elemento interativo: outline com `var(--shadow-focus)` (anel verde 3px) [guideline: Keyboard]
- [ ] Remover qualquer `outline: none` sem replacement visível [guideline: Keyboard]
- [ ] `@media (prefers-reduced-motion: reduce)` global: definir `transition-duration: 0.01ms !important` e `animation-duration: 0.01ms !important` em `*` [guideline: Animation]
- [ ] Skip-to-content link no topo do `<body>` (`href="#main"`, visualmente oculto até `:focus`) [guideline: Content & Accessibility]
- [ ] Cada página define seu `<main id="main">` — corrigir hierarquia de heading (uma `<h1>` por página)
- [ ] `scroll-margin-top: var(--space-16)` em todos `<h1>`-`<h6>` para compensar a top nav fixa [guideline: Content & Accessibility]
- [ ] Botões icon-only têm `aria-label` descritivo (auditar PaceInput, UserMenu, paginação)
- [ ] Confirmar pelo DevTools: nenhum elemento decorativo sem `aria-hidden="true"`
- [ ] Auditar com Lighthouse Accessibility ≥ 95
- [ ] Verificar no browser: navegação por teclado (Tab, Shift+Tab, Enter, Escape em modais) funciona em todas as telas

**Arquivos esperados:** `client/src/styles/a11y.css` (novo, importado por `index.css`), atualizações pontuais nas páginas para hierarquia de heading.

---

#### US-031: Biblioteca de Componentes Compartilhados

**Prioridade:** P4.

**Descrição:** Como desenvolvedor frontend, preciso de componentes React tipados e reutilizáveis (`Button`, `Input`, `Field`, `Card`, `Badge`, `Banner`, `Skeleton`) para que cada página deixe de carregar markup/CSS duplicado e a UI seja visualmente consistente.

**Acceptance Criteria:**
- [ ] Criar `client/src/components/ui/` contendo:
  - `Button.tsx` — variantes `primary`/`secondary`/`ghost`/`danger`, tamanhos `sm`/`md`/`lg`, prop `loading` que mostra spinner mantendo o label original [guideline: Forms]
  - `Input.tsx` — wrapper de `<input>` com aplicação automática de `font-size: 16px` no mobile [guideline: Targets & Input]
  - `Field.tsx` — composição `<label> + <Input> + <ErrorText>`, prop `error` para estado inválido, `hint` para texto de ajuda
  - `Card.tsx` — surface com `var(--shadow-sm)` e `var(--radius-lg)`; props `as` (h-tag para título)
  - `Badge.tsx` — chip pequeno com variantes semânticas (`success`/`warning`/`danger`/`info`/`neutral`)
  - `Banner.tsx` — alerta horizontal com ícone, variantes idem Badge, com `role="status"` (polite) ou `role="alert"` (assertive)
  - `Skeleton.tsx` — placeholder pulsante para loading; aceita `width`/`height` para mirror layout final [guideline: Content & Accessibility]
- [ ] Cada componente exportado por `client/src/components/ui/index.ts`
- [ ] Cada componente tem teste de utilitário (`*.test.tsx` se aplicável) ou nota de "smoke-tested visualmente"
- [ ] Tipos compatíveis com `verbatimModuleSyntax: true` (importar tipos com `import type`)
- [ ] Documentar a API de cada componente em comentário JSDoc curto no topo do arquivo
- [ ] **Não** migrar páginas nesta US — apenas criar a biblioteca. Migração ocorre em US-035–US-041.
- [ ] `npm run build` passa
- [ ] `npm run lint` passa

**Arquivos esperados:** `client/src/components/ui/{Button,Input,Field,Card,Badge,Banner,Skeleton,index}.tsx`.

---

#### US-032: Sistema de Feedback — Toast, Banners e Confirmações

**Prioridade:** P5.

**Descrição:** Como usuário, preciso de feedback visual claro e não-modal para ações (sucesso de upload, falha de rede, sessão expirada) e de confirmação para ações destrutivas (logout — opcional —, futuras exclusões), para que o sistema não fique mudo nem me surpreenda.

**Acceptance Criteria:**
- [ ] Implementar `<ToastProvider>` em `client/src/context/ToastContext.tsx` + hook `useToast()` com API `toast.success(msg)`, `toast.error(msg)`, `toast.info(msg)`
- [ ] Toasts renderizados em portal no canto inferior-direito (`bottom: 16px; right: 16px`), com `aria-live="polite"` para success/info e `aria-live="assertive"` para error [guideline: Feedback]
- [ ] Auto-dismiss em 5s; pausar dismiss ao hover; botão de fechar manual sempre visível
- [ ] Animação de entrada/saída usando `transform: translateX(...)` + `opacity` (compositor-friendly) [guideline: Animation]
- [ ] Wire-in nas páginas existentes:
  - Upload bem-sucedido → `toast.success("Vídeo enviado. Iniciando análise.")`
  - Login bem-sucedido → toast opcional de boas-vindas
  - 401 em qualquer chamada autenticada → `toast.error("Sessão expirada. Faça login novamente.")` + redirect para `/login`
- [ ] Substituir `alert()` ou `<p className="form-error">` solto fora de formulários por toast quando o erro for global [guideline: Feedback]
- [ ] Verificar no browser: trigger de toast com teclado (não só mouse), e que `prefers-reduced-motion` desativa a animação

**Arquivos esperados:** `client/src/context/ToastContext.tsx` (novo), `client/src/components/ui/Toast.tsx` (novo), uso pontual em `LoginPage`, `UploadPage`, e em `client/src/api/client.ts` (interceptor de 401).

---

#### US-033: Estados Padronizados — Loading (Skeleton), Empty, Error com Recuperação

**Prioridade:** P6.

**Descrição:** Como usuário, em cada tela quero ver placeholders fiéis ao layout final durante carregamentos, ilustrações + CTA em estados vazios, e mensagem clara + ação de recuperação em estados de erro — nunca telas brancas, textos crus ou dead-ends.

**Acceptance Criteria:**
- [ ] Padronizar três componentes em `client/src/components/ui/states/`:
  - `LoadingState.tsx` — usa `Skeleton`s que **espelham** o layout final (mesmas alturas e larguras dos cards reais) [guideline: Content & Accessibility]
  - `EmptyState.tsx` — ilustração SVG (pode ser inline simples), título, descrição, CTA primário
  - `ErrorState.tsx` — ícone de aviso, mensagem do erro, botão "Tentar novamente" + botão "Voltar para…"
- [ ] Substituir loading textual nas páginas existentes:
  - `StatusPage`: usar `LoadingState` no consultar inicial
  - `AnalysisPage`: usar `LoadingState` (esqueleto da nota + cards de métrica + cards de recomendação)
  - `AnalysisRawPage`: usar `LoadingState` (esqueleto da tabela e dos charts)
  - `HistoricoPage`: usar `LoadingState` (skeleton de 5 linhas) e `EmptyState` quando `items.length === 0` [guideline: Content & Accessibility]
- [ ] Garantir que **toda** mensagem de erro oferece um próximo passo (botão ou link) [guideline: Content & Accessibility — "no dead ends"]
- [ ] CLS (Cumulative Layout Shift) ≤ 0.05 medido no DevTools Performance ao trocar de loading → conteúdo
- [ ] Verificar no browser: simular slow-3G no DevTools e ver os skeletons aparecerem por ≥ 1s sem layout shift

**Arquivos esperados:** `client/src/components/ui/states/{LoadingState,EmptyState,ErrorState}.tsx`, atualizações em todas as páginas de leitura.

---

#### US-034: Responsividade Mobile-First & Safe Areas

**Prioridade:** P7.

**Descrição:** Como usuário no celular logo após o treino, preciso que toda a aplicação funcione confortavelmente em viewports estreitas (≥ 360px), respeite os safe areas de iPhones com notch, e tenha hit targets adequados ao toque.

**Acceptance Criteria:**
- [ ] **Eliminar** `width: 1126px` em `#root` — substituir por `max-width: 1280px; margin-inline: auto; padding-inline: var(--space-4)` (mobile) escalando para `var(--space-8)` (lg)
- [ ] Eliminar `border-inline: 1px solid var(--border)` decorativo do `#root`
- [ ] Definir breakpoints em tokens CSS: `--bp-sm: 640px`, `--bp-md: 768px`, `--bp-lg: 1024px`, `--bp-xl: 1280px` (e usar via `@media (min-width: var(--bp-X))` ou container queries onde aplicável) [guideline: Layout]
- [ ] Aplicar `padding: env(safe-area-inset-*)` no top nav (top + esquerda) e em qualquer footer fixo (bottom + esquerda) [guideline: Layout]
- [ ] Mobile: hit targets de toda interação `≥ 44px` (audit: PaceInput, paginação do histórico, botões de página) [guideline: Targets & Input]
- [ ] Mobile: `<input>` com `font-size: 16px` para evitar zoom no iOS [guideline: Targets & Input]
- [ ] Adicionar `touch-action: manipulation` em todos os botões e links para evitar double-tap zoom [guideline: Targets & Input]
- [ ] Adicionar `-webkit-tap-highlight-color: rgba(16,185,129,0.15)` (verde sutil) [guideline: Targets & Input]
- [ ] **Nunca** usar `user-scalable=no` ou `maximum-scale=1` no viewport meta [guideline: Targets & Input]
- [ ] Verificar simulação de ultra-wide a 50% zoom: layout não estoura nem abre vazios cinzentos [guideline: Layout]
- [ ] Verificar no browser nos viewports: 360×640, 375×812 (iPhone X), 414×896 (iPhone 11 Pro Max), 768×1024 (iPad), 1440×900, 2560×1440

**Arquivos esperados:** `client/src/styles/tokens.css` (breakpoints), `client/src/styles/reset.css` (novo — touch-action, tap-highlight, viewport defaults), `client/src/index.css` (refator do `#root`).

---

#### US-035: Redesign — Tela de Login

**Prioridade:** P8.

**Descrição:** Como visitante, quero uma tela de login com identidade visual da marca, formulário acessível e claro, e um caminho óbvio para cadastro.

**Acceptance Criteria:**
- [ ] Layout: card centralizado (`max-width: 400px`) sobre fundo `var(--bg)` com hero lateral à direita em viewports `≥ lg` (ilustração ou imagem esportiva — pode ser gradiente verde sutil + SVG abstrato de movimento)
- [ ] Branding sutil no topo: logo + nome do produto
- [ ] Migrar para `<Field>` + `<Input>` + `<Button>` da biblioteca de componentes (US-031)
- [ ] Inputs: `autocomplete="email"` no e-mail e `autocomplete="current-password"` na senha [guideline: Forms]
- [ ] `inputmode="email"` + `spellcheck="false"` no campo de e-mail [guideline: Forms]
- [ ] Botão **Entrar** com estado loading (spinner inline + label inalterado) [guideline: Forms]
- [ ] Submit com Enter funcionando, foco volta para o primeiro erro no fail [guideline: Forms]
- [ ] Erros inline ao lado dos campos; erro global de credenciais como `<Banner variant="danger">` no topo do form [guideline: Forms]
- [ ] Link **Criar conta** abaixo do botão, navegando para `/signup`
- [ ] Autofocus no campo de e-mail somente em desktop (não em mobile) [guideline: Autofocus]
- [ ] `<title>Entrar — {brand}</title>`
- [ ] `npm run build` passa
- [ ] Verificar no browser em mobile e desktop

**Arquivos esperados:** `client/src/pages/LoginPage.tsx` (refator), `client/src/pages/auth.css` (novo, estilos compartilhados login/signup).

---

#### US-036: Redesign — Tela de Cadastro (Multi-Step Opcional)

**Prioridade:** P9.

**Descrição:** Como novo usuário, quero uma tela de cadastro que não me sobrecarregue com 6 campos de uma vez, e que valide cada bloco antes de avançar.

**Acceptance Criteria:**
- [ ] Avaliar e implementar uma de duas abordagens (definir na US):
  - **Opção A (single-page agrupada):** três `<fieldset>` visualmente agrupados — "Conta" (nome/e-mail/senha), "Perfil físico" (altura/peso), "Experiência" (nível) — com `<legend>` claros
  - **Opção B (multi-step):** três passos com indicador de progresso (3 de 3) e botão "Voltar" sempre disponível
- [ ] Recomendação: começar por **A** (mais simples, menos risco de UX ruim sem usuários reais para validar B)
- [ ] Inputs: `autocomplete` correto em cada campo (`name`, `email`, `new-password`)
- [ ] Toggle "Mostrar senha" no campo de senha (botão com `aria-pressed`)
- [ ] Validação inline: e-mail formato, senha ≥ 8 chars, altura > 0, peso > 0
- [ ] Erros do backend (e-mail duplicado 409) mapeados para o campo correto via `extractApiError`
- [ ] Botão **Criar conta** com loading state; após sucesso → toast + redirect (já implementado em US-021)
- [ ] Link **Já tenho conta** → `/login`
- [ ] `<title>Criar conta — {brand}</title>`
- [ ] `npm run build` passa
- [ ] Verificar no browser

**Arquivos esperados:** `client/src/pages/SignupPage.tsx` (refator).

---

#### US-037: Redesign — Tela de Upload (Drag-Drop, Preview, Validações Ricas)

**Prioridade:** P10.

**Descrição:** Como corredor, quero arrastar o vídeo para a tela, ver um preview do primeiro frame, e receber feedback visual rico sobre cada validação (duração, resolução, FPS, perspectiva) antes de enviar.

**Acceptance Criteria:**
- [ ] Dropzone visual ocupando o card principal, com `border: 2px dashed var(--border-strong)`, hover/active state que destaca a borda em `var(--brand-500)`
- [ ] Suporte a drag-and-drop (`onDragOver`, `onDrop` com `preventDefault`) **e** clique para abrir file picker (mantendo o `<input type="file" accept="video/*">` escondido como fallback acessível)
- [ ] Após selecionar/arrastar arquivo: gerar preview do primeiro frame via `<video>` em memória (já existe `videoMeta.ts` — reutilizar)
- [ ] Painel lateral (ou seção abaixo em mobile) listando as validações como **checklist visual**:
  - ✓ Duração (XX s — entre 30 s e 3 min)
  - ✓ Resolução (1920×1080 — mínimo 640×480)
  - ⚠ FPS (~25 fps — recomendado ≥ 60, validação final no servidor)
  - ─ Perspectiva (validada no servidor)
- [ ] Componente `<PaceInput>` integrado lado-a-lado com a dropzone (em desktop) ou abaixo (em mobile)
- [ ] Botão **Analisar corrida** (substituir o atual "Enviar") — disabled enquanto arquivo ou pace inválidos
- [ ] Indicador de upload com **barra de progresso real** do axios (`onUploadProgress`)
- [ ] Banner com mensagem de validação do servidor (422) se algo falhar — `<Banner variant="danger">` com sugestão de correção [guideline: Content & Accessibility — no dead ends]
- [ ] Hint colapsável "Como gravar o vídeo ideal" com bullets (lateral, 60+ fps, 30+ s, plano fixo)
- [ ] `<title>Nova análise — {brand}</title>`
- [ ] `npm run build` passa
- [ ] Verificar no browser: drag-drop funciona, preview aparece, upload mostra progresso, mensagem de servidor 422 aparece corretamente

**Arquivos esperados:** `client/src/pages/UploadPage.tsx` (refator significativo), `client/src/components/Dropzone.tsx` (novo), `client/src/components/PaceInput.tsx` (refinar visual), `client/src/api/videos.ts` (adicionar `onUploadProgress` ao request).

---

#### US-038: Redesign — Tela de Status (Progresso Visual + Tempo Estimado)

**Prioridade:** P11.

**Descrição:** Como corredor aguardando o processamento, quero ver claramente em qual etapa o sistema está, ter uma estimativa de tempo restante e algo agradável de assistir para reduzir ansiedade.

**Acceptance Criteria:**
- [ ] Hero da tela: ilustração SVG animada (passo de corredor estilizado) que pulsa/anda ao ritmo da etapa ativa — animação respeita `prefers-reduced-motion` [guideline: Animation]
- [ ] Stepper vertical (ou horizontal em desktop) com 4 etapas: **Validando vídeo** → **Detectando pose** → **Calculando métricas** → **Gerando recomendações**
- [ ] Etapa ativa destacada com ícone animado e label em `var(--brand-500)`; etapas concluídas com checkmark; etapas futuras em cinza
- [ ] Tempo decorrido visível ("Há 12 segundos") + estimativa restante baseada em mediana histórica (placeholder estático "~30s" se não houver dados ainda)
- [ ] Animação da barra de progresso usa `transform: scaleX()` (compositor-friendly), não `width` [guideline: Animation]
- [ ] Estado de erro: card vermelho com `<Banner variant="danger">`, mensagem específica do erro, botão **Enviar novo vídeo** + botão **Ver dicas de gravação** [guideline: Content & Accessibility]
- [ ] Quando concluído: mensagem celebratória ("Análise pronta!") + redirect automático para `/analysis/:id` em 1.5s **ou** botão "Ver diagnóstico"
- [ ] `aria-live="polite"` no texto da etapa atual (já existe — manter) [guideline: Feedback]
- [ ] `<title>Processando — {brand}</title>`
- [ ] `npm run build` passa
- [ ] Verificar no browser: stepper responsivo em mobile, animação suave, redirect funciona

**Arquivos esperados:** `client/src/pages/StatusPage.tsx` (refator), `client/src/components/Stepper.tsx` (novo), `client/src/components/RunnerIllustration.tsx` (novo, SVG animado).

---

#### US-039: Redesign — Tela de Diagnóstico Simplificado (Hero da Nota + Cards Visuais)

**Prioridade:** P12.

**Descrição:** Como corredor, quero abrir o diagnóstico e ver imediatamente minha nota geral em destaque, depois um resumo visual das métricas (gauges com a faixa ideal), e por último as recomendações categorizadas com ícones e cores semânticas.

**Acceptance Criteria:**
- [ ] **Hero da nota geral**: card grande com a nota em fonte display (`--text-display`), `tabular-nums`, anel circular ao redor (SVG) preenchido proporcionalmente — verde se ≥ 7, âmbar se 5–7, vermelho se < 5
- [ ] Texto secundário do hero: classificação ("Excelente" / "Bom" / "Atenção") + 1 linha de feedback principal
- [ ] Seção "Métricas principais" em grid de cards (2 colunas em desktop, 1 em mobile):
  - Cada card: ícone da métrica (anatômico — joelho, cotovelo, tronco — via `lucide-react` ou SVG inline), nome, valor grande, gauge horizontal com faixa ideal destacada em verde claro, marker do usuário
  - `font-variant-numeric: tabular-nums` em todos os números [guideline: Content & Accessibility]
- [ ] Seção "Recomendações" agrupada por severidade na ordem **Crítico → Atenção → Informativo**:
  - Cada grupo com `<h2>` colorido conforme severidade
  - Cards de recomendação com ícone semântico (alerta-circle, info, check), título da categoria em negrito, descrição corrente
  - Cards são focáveis via teclado (mesmo que não tenham ação) — para leitor de tela narrar como item de lista [guideline: Content & Accessibility]
- [ ] Footer da página: dois botões — **Ver dados técnicos** (`/analysis/:id/raw`) e **Voltar ao histórico** (`/historico`)
- [ ] Estado vazio: se `recomendacoes.length === 0`, banner informativo verde "Sua corrida está dentro de todos os parâmetros ideais — continue assim."
- [ ] Compartilhamento (futuro, fora desta US): placeholder de botão "Compartilhar" desabilitado com tooltip "em breve"
- [ ] `<title>Diagnóstico #{id} — {brand}</title>`
- [ ] `npm run build` passa
- [ ] Verificar no browser: hero responsivo, cards quebram bem em mobile

**Arquivos esperados:** `client/src/pages/AnalysisPage.tsx` (refator significativo), `client/src/components/NotaHero.tsx` (novo), `client/src/components/MetricaCard.tsx` (novo), `client/src/components/RecomendacaoCard.tsx` (novo).

---

#### US-040: Redesign — Tela de Dados Brutos (Charts Profissionais + Filtros)

**Prioridade:** P13.

**Descrição:** Como corredor avançado ou treinador, quero explorar os dados frame-a-frame em gráficos legíveis, com filtros por métrica e capacidade de comparar lado esquerdo vs direito.

**Acceptance Criteria:**
- [ ] Migrar `recharts` (já instalado) para charts com paleta acessível para color-blind (Okabe-Ito ou similar) [guideline: Design]
- [ ] Charts principais: ângulo do joelho (esq/dir overlay), ângulo do cotovelo (esq/dir overlay), inclinação do tronco — eixo X = frame ou tempo (s)
- [ ] Cada chart: tooltip on-hover, legenda clara (esq verde, dir laranja-tangerine), eixo Y com unidade
- [ ] Filtro de métrica via tabs ou chips no topo (`<Badge>` selecionável)
- [ ] Tabela densa abaixo (paginada client-side, `useDeferredValue` para filtros) — virtualizar se ≥ 50 linhas [guideline: Performance]
- [ ] Destaque visual (background sutil) em frames identificados como "fora da faixa ideal"
- [ ] Botão **Exportar CSV** (gera blob client-side, sem chamada à API) — placeholder se simples
- [ ] Link **Voltar ao diagnóstico** no topo
- [ ] `<title>Dados técnicos #{id} — {brand}</title>`
- [ ] `npm run build` passa
- [ ] Verificar no browser: charts responsivos, tooltip legível, paleta funciona em escala de cinza

**Arquivos esperados:** `client/src/pages/AnalysisRawPage.tsx` (refator significativo), `client/src/components/charts/` (organizar charts em componentes reutilizáveis).

---

#### US-041: Redesign — Tela de Histórico (Mini-Sparklines + Filtros)

**Prioridade:** P14.

**Descrição:** Como corredor que acompanha a evolução, quero ver meu histórico de análises com tendência visual da nota geral ao longo do tempo, e filtrar/ordenar por data e nota.

**Acceptance Criteria:**
- [ ] Hero compacto: card com **mini-sparkline** da nota geral nas últimas N sessões (recharts `LineChart` simples) + estatística "Média 7.2 — +0.8 vs mês passado" [guideline: Design]
- [ ] Lista de sessões em cards (não tabela): cada card mostra data formatada localizada (`Intl.DateTimeFormat('pt-BR')`), pace, badge de status, nota geral em `tabular-nums`
- [ ] Cards `concluido` são clicáveis (link para `/analysis/:id`); cards de erro mostram motivo expandível ao clicar (já existe — manter padrão)
- [ ] Filtros no topo: período (últimos 7d / 30d / todos), status (concluído / erro / todos)
- [ ] URL reflete os filtros e a página atual (`?periodo=30d&status=concluido&page=2`) [guideline: State & Navigation — deep-link]
- [ ] Back/Forward do browser restaura scroll [guideline: State & Navigation]
- [ ] Estado vazio: se 0 sessões → `<EmptyState>` com ilustração e CTA "Enviar primeiro vídeo" → `/upload`
- [ ] Skeleton durante loading espelha o layout de cards [guideline: Content & Accessibility]
- [ ] Paginação acessível (`<nav aria-label="Paginação">`, botões com `aria-disabled`)
- [ ] `<title>Histórico — {brand}</title>`
- [ ] `npm run build` passa
- [ ] Verificar no browser: filtros funcionam, URL atualiza, voltar do diagnóstico restaura scroll

**Arquivos esperados:** `client/src/pages/HistoricoPage.tsx` (refator), `client/src/components/SparklineHero.tsx` (novo), `client/src/utils/dateFmt.ts` (novo, helper `Intl.DateTimeFormat`).

---

#### US-042: Microinterações & Motion Coerentes

**Prioridade:** P15.

**Descrição:** Como usuário, quero microinterações sutis que reforcem o significado das ações (hover de botão, transição de página, entrada de cards) sem tornar a UI "pesada" ou esperar animações para conseguir clicar.

**Acceptance Criteria:**
- [ ] Hover em botões: leve `transform: translateY(-1px)` + sombra `--shadow-md` em `--duration-fast` [guideline: Animation]
- [ ] Active em botões: `transform: translateY(0)` + sombra `--shadow-xs` (efeito "press")
- [ ] Entrada de cards (em listas): `opacity 0→1` + `translateY(8px)→0` escalonado em 30ms por card, **só** na primeira renderização (não a cada re-render) [guideline: Animation]
- [ ] Transição entre rotas: fade simples `opacity 0→1` em 200ms (usar `<Transition>` ou CSS sobre `<Outlet>`) — interruptível [guideline: Animation]
- [ ] Spinner de loading: rotação CSS pura (`@keyframes spin`) em SVG inline; animação pausada se `prefers-reduced-motion`
- [ ] **Nunca** `transition: all` — listar propriedades [guideline: Animation]
- [ ] **Nunca** animar `width/height/top/left` [guideline: Animation]
- [ ] `transform-origin` correto em todas as animações de "abrir" (origem = onde o usuário clicou) [guideline: Animation]
- [ ] Auditar: nenhum overshoot ou bounce desnecessário (animações servem para clarificar causa-efeito, não como decoração)
- [ ] Verificar com DevTools Performance: nenhum reflow durante as animações; tudo na compositor thread

**Arquivos esperados:** `client/src/styles/motion.css` (novo, com `@keyframes` e classes utilitárias), uso pontual nas páginas.

---

#### US-043: Performance & Bundle — Lazy Routes, Preload, Image Dims

**Prioridade:** P16.

**Descrição:** Como usuário em rede móvel, quero que a aplicação carregue rápido na primeira visita e seja responsiva ao trocar de página.

**Acceptance Criteria:**
- [ ] Converter rotas em lazy via `React.lazy()` + `<Suspense fallback={<LoadingState/>}>` em `App.tsx` (todas as páginas exceto Login/Signup) [guideline: Performance]
- [ ] `<link rel="preconnect">` para origem da API se diferente do front (em produção) [guideline: Performance]
- [ ] Fontes com `<link rel="preload" as="font" crossorigin>` (já em US-028) [guideline: Performance]
- [ ] Toda imagem com `width` e `height` explícitos para prevenir CLS [guideline: Performance]
- [ ] Imagens fora da fold com `loading="lazy"` [guideline: Performance]
- [ ] Auditar bundle size: `npm run build` deve gerar bundle inicial **< 250 KB gzipped**; recharts deve estar em chunk separado (lazy import nas páginas de chart) [guideline: Performance]
- [ ] Verificar com Lighthouse: Performance ≥ 85 em mobile (modo "Mobile, slow 4G")
- [ ] Mutações (POST `/upload`, POST `/login`, POST `/register`) têm timeout configurado em axios (sugestão: 30s para upload, 10s para auth) [guideline: Performance — "Mutations target <500ms" não se aplica a upload de vídeo, mas auth sim]
- [ ] `npm run build` passa

**Arquivos esperados:** `client/src/App.tsx` (lazy imports), `client/vite.config.ts` (`build.rollupOptions.output.manualChunks` se necessário separar recharts), `client/src/api/client.ts` (timeouts).

---

### 18.7 Ordem de Execução Recomendada

```
US-028 ─┬─→ US-029 ──→ US-030 ──→ US-031 ──→ US-032 ──→ US-033
        │
        └─→ US-034 (paralelo a US-029)

US-031 + US-033 ──→ US-035 ──→ US-036 ──→ US-037 ──→ US-038 ──→ US-039 ──→ US-040 ──→ US-041

US-042 e US-043 podem ser executadas em paralelo após US-039 (ou no final)
```

Cada US deve ser entregue como **um único commit** seguindo o padrão de Conventional Commits (Seção 12), no mesmo branch `dev/padilha`. **Não** mexer em backend/`server/`, `processing/`, `ralph/` ou `*.md` fora de `client/` durante essas iterações.

---

### 18.8 Critério Visual Global de Aceite

Ao final das US-028 a US-043, ao abrir a aplicação:
- **Nenhuma cor roxa** ou preto puro permanece em uso visível
- A paleta dominante é verde-esmeralda + slate frio, com laranja-tangerina como accent
- Há um app shell consistente em todas as rotas autenticadas
- Cada página tem `<title>` próprio e estados de loading/empty/error desenhados
- Toda interação tem foco visível, todo botão tem hover/active distintos
- Lighthouse: Accessibility ≥ 95, Best Practices ≥ 95, Performance ≥ 85 (mobile)
- O app é confortável de usar em viewport 360×640 (smartphone básico) sem scroll horizontal nem hit targets pequenos
