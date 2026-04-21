"""Gerador de recomendações + nota geral (US-016).

Consome as métricas calculadas pelas histórias anteriores (lista
``(tipo, valor)``) e produz:

    * Uma tupla de :class:`RecomendacaoGerada` (categoria, descrição,
      severidade) — uma por métrica classificável. Métricas com severidade
      ``informativo`` indicam "dentro da faixa ideal"; ``atencao`` e
      ``critico`` sinalizam desvios que o corredor precisa observar.
    * Uma nota geral em [0, 10], calculada como ``10 − ∑pesos`` com
      clamp nos dois extremos. O peso de ``critico`` é maior que o de
      ``atencao``; métricas ideais não contribuem.
    * Um texto curto ``feedback_ia`` resumindo a nota e a contagem por
      severidade, usado como snapshot amigável no endpoint simplificado
      (US-017) e no histórico (US-019).

Classificação por métrica segue a Seção 9 do PRD:

    * Ângulo joelho (contato inicial) — convertido de ``interno`` para
      ``flexão = 180 − interno`` antes de comparar com a tabela do PRD
      (ideal 15°–25°, atenção 10°–15° ou 25°–35°, crítico <10° ou >35°).
    * Ângulo cotovelo — ideal 70°–110°, atenção 60°–70° ou 110°–120°,
      crítico <60° ou >120°.
    * Inclinação do tronco — ideal 4°–8°, atenção 1°–4° ou 8°–15°,
      crítico <1° ou >15° (inclinação negativa ⇒ tronco ereto/para trás
      ⇒ crítico).
    * Overstriding — ``abs(valor)`` é classificado: ideal <5 cm, atenção
      5–15 cm, crítico >15 cm. O sinal é usado apenas na descrição
      textual ("à frente" vs. "atrás" do centro de massa).
    * Oscilação vertical — ideal 5–10 cm, atenção 3–5 ou 10–13 cm,
      crítico <3 ou >13 cm.
    * Simetria (TCS, joelho, oscilação) — ideal <5%, atenção 5%–10%,
      crítico >10%. Mesma tabela para os três tipos.

Métricas ``apenas_informativa=True`` (cadência, TCS absoluto) **não
devem ser passadas** para :func:`analisar_metricas` — o chamador filtra
pelo flag no ORM antes de invocar esta camada. Tipos desconhecidos são
silenciosamente ignorados (sem recomendação, sem penalização).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

SEVERIDADE_INFORMATIVO = "informativo"
SEVERIDADE_ATENCAO = "atencao"
SEVERIDADE_CRITICO = "critico"

PESO_ATENCAO = 0.5
PESO_CRITICO = 1.5
NOTA_MAXIMA = 10.0


@dataclass(frozen=True)
class RecomendacaoGerada:
    """Recomendação pronta para persistência em ``RECOMENDACAO``."""

    categoria: str
    descricao: str
    severidade: str


@dataclass(frozen=True)
class AnaliseResultado:
    """Saída agregada do gerador: nota geral, resumo textual e recomendações."""

    nota_geral: float
    feedback_ia: str
    recomendacoes: tuple[RecomendacaoGerada, ...]


# ---------------- Classificadores por métrica (Seção 9 do PRD) ----------------


def _classificar_joelho_interno(angulo_interno: float) -> str:
    flexao = 180.0 - angulo_interno
    if 15.0 <= flexao <= 25.0:
        return SEVERIDADE_INFORMATIVO
    if flexao < 10.0 or flexao > 35.0:
        return SEVERIDADE_CRITICO
    return SEVERIDADE_ATENCAO


def _classificar_cotovelo(angulo_graus: float) -> str:
    if 70.0 <= angulo_graus <= 110.0:
        return SEVERIDADE_INFORMATIVO
    if angulo_graus < 60.0 or angulo_graus > 120.0:
        return SEVERIDADE_CRITICO
    return SEVERIDADE_ATENCAO


def _classificar_tronco(inclinacao_graus: float) -> str:
    if 4.0 <= inclinacao_graus <= 8.0:
        return SEVERIDADE_INFORMATIVO
    if inclinacao_graus < 1.0 or inclinacao_graus > 15.0:
        return SEVERIDADE_CRITICO
    return SEVERIDADE_ATENCAO


def _classificar_overstriding(valor_cm: float) -> str:
    magnitude = abs(valor_cm)
    if magnitude < 5.0:
        return SEVERIDADE_INFORMATIVO
    if magnitude > 15.0:
        return SEVERIDADE_CRITICO
    return SEVERIDADE_ATENCAO


def _classificar_oscilacao(valor_cm: float) -> str:
    if 5.0 <= valor_cm <= 10.0:
        return SEVERIDADE_INFORMATIVO
    if valor_cm < 3.0 or valor_cm > 13.0:
        return SEVERIDADE_CRITICO
    return SEVERIDADE_ATENCAO


def _classificar_simetria(valor_percentual: float) -> str:
    if valor_percentual < 5.0:
        return SEVERIDADE_INFORMATIVO
    if valor_percentual > 10.0:
        return SEVERIDADE_CRITICO
    return SEVERIDADE_ATENCAO


# -------------------- Texto das recomendações por métrica ---------------------

_LADO_HUMANO = {"esq": "esquerdo", "dir": "direito"}


def _lado_de_tipo(tipo: str) -> str:
    sufixo = tipo.rsplit("_", 1)[-1]
    return _LADO_HUMANO.get(sufixo, "")


def _analisar_joelho(tipo: str, valor: float) -> RecomendacaoGerada:
    severidade = _classificar_joelho_interno(valor)
    lado = _lado_de_tipo(tipo)
    flexao = 180.0 - valor
    categoria = f"Flexão do joelho {lado} no contato inicial"
    if severidade == SEVERIDADE_INFORMATIVO:
        descricao = (
            f"Flexão do joelho {lado} em {flexao:.1f}° no contato inicial — "
            "dentro da faixa ideal (15°–25°)."
        )
    elif severidade == SEVERIDADE_ATENCAO:
        if flexao < 15.0:
            descricao = (
                f"Flexão do joelho {lado} de {flexao:.1f}° é baixa — tente "
                "aterrissar com o joelho levemente flexionado para amortecer "
                "o impacto."
            )
        else:
            descricao = (
                f"Flexão do joelho {lado} de {flexao:.1f}° é alta — verifique "
                "se a passada não está muito longa."
            )
    else:
        if flexao < 10.0:
            descricao = (
                f"Joelho {lado} quase totalmente estendido no contato "
                f"({flexao:.1f}°) — alto risco de lesão por impacto. "
                "Aterrisse com o joelho levemente flexionado."
            )
        else:
            descricao = (
                f"Colapso excessivo do joelho {lado} no contato "
                f"({flexao:.1f}°) — fortaleça quadríceps e glúteos para "
                "controlar a flexão."
            )
    return RecomendacaoGerada(
        categoria=categoria, descricao=descricao, severidade=severidade
    )


def _analisar_cotovelo(tipo: str, valor: float) -> RecomendacaoGerada:
    severidade = _classificar_cotovelo(valor)
    lado = _lado_de_tipo(tipo)
    categoria = f"Ângulo do cotovelo {lado}"
    if severidade == SEVERIDADE_INFORMATIVO:
        descricao = (
            f"Ângulo médio do cotovelo {lado} em {valor:.1f}° — dentro da "
            "faixa ideal (70°–110°)."
        )
    elif severidade == SEVERIDADE_ATENCAO:
        if valor < 70.0:
            descricao = (
                f"Cotovelo {lado} um pouco fechado ({valor:.1f}°) — relaxe "
                "os braços e permita um balanço natural."
            )
        else:
            descricao = (
                f"Cotovelo {lado} um pouco aberto ({valor:.1f}°) — sinal de "
                "tensão no ombro; relaxe o movimento do braço."
            )
    else:
        if valor < 60.0:
            descricao = (
                f"Cotovelo {lado} muito fechado ({valor:.1f}°) — tensão "
                "excessiva; relaxe os braços para melhorar a economia."
            )
        else:
            descricao = (
                f"Cotovelo {lado} muito aberto ({valor:.1f}°) — sinal de "
                "fadiga ou tensão no ombro; ajuste o swing."
            )
    return RecomendacaoGerada(
        categoria=categoria, descricao=descricao, severidade=severidade
    )


def _analisar_tronco(tipo: str, valor: float) -> RecomendacaoGerada:
    severidade = _classificar_tronco(valor)
    categoria = "Inclinação do tronco"
    if severidade == SEVERIDADE_INFORMATIVO:
        descricao = (
            f"Inclinação do tronco em {valor:.1f}° — postura equilibrada "
            "(faixa ideal 4°–8°)."
        )
    elif severidade == SEVERIDADE_ATENCAO:
        if valor < 4.0:
            descricao = (
                f"Tronco muito ereto ({valor:.1f}°) — projete levemente "
                "para frente a partir dos quadris para reduzir as forças "
                "de frenagem."
            )
        else:
            descricao = (
                f"Tronco um pouco inclinado além do ideal ({valor:.1f}°) — "
                "reduza levemente a projeção frontal para poupar o quadril."
            )
    else:
        if valor < 1.0:
            descricao = (
                f"Tronco quase vertical ou inclinado para trás ({valor:.1f}°)"
                " — projete o tronco a partir dos quadris para melhorar a "
                "propulsão."
            )
        else:
            descricao = (
                f"Inclinação excessiva do tronco ({valor:.1f}°) — reduz a "
                "economia de corrida e sobrecarrega o quadril."
            )
    return RecomendacaoGerada(
        categoria=categoria, descricao=descricao, severidade=severidade
    )


def _analisar_overstriding(tipo: str, valor: float) -> RecomendacaoGerada:
    severidade = _classificar_overstriding(valor)
    lado = _lado_de_tipo(tipo)
    direcao = "à frente" if valor >= 0 else "atrás"
    magnitude = abs(valor)
    categoria = f"Overstriding {lado}"
    if severidade == SEVERIDADE_INFORMATIVO:
        descricao = (
            f"Pé {lado} pousa alinhado ao centro de massa "
            f"({valor:.1f} cm) — boa eficiência de passada."
        )
    elif severidade == SEVERIDADE_ATENCAO:
        descricao = (
            f"Pé {lado} pousa {direcao} do centro de massa "
            f"({magnitude:.1f} cm) — encurte levemente a passada para "
            "reduzir frenagem."
        )
    else:
        descricao = (
            f"Overstriding severo no pé {lado} ({magnitude:.1f} cm {direcao} "
            "do centro de massa) — risco elevado de lesão por frenagem; "
            "aumente a cadência e reduza o comprimento do passo."
        )
    return RecomendacaoGerada(
        categoria=categoria, descricao=descricao, severidade=severidade
    )


def _analisar_oscilacao(tipo: str, valor: float) -> RecomendacaoGerada:
    severidade = _classificar_oscilacao(valor)
    categoria = "Oscilação vertical"
    if severidade == SEVERIDADE_INFORMATIVO:
        descricao = (
            f"Oscilação vertical de {valor:.1f} cm — dentro da faixa ideal "
            "(5–10 cm)."
        )
    elif severidade == SEVERIDADE_ATENCAO:
        if valor < 5.0:
            descricao = (
                f"Oscilação vertical baixa ({valor:.1f} cm) — passada "
                "arrastada, sem fase de voo eficiente."
            )
        else:
            descricao = (
                f"Oscilação vertical um pouco alta ({valor:.1f} cm) — "
                "desperdício de energia vertical; procure correr mais rente "
                "ao solo."
            )
    else:
        if valor < 3.0:
            descricao = (
                f"Oscilação vertical muito baixa ({valor:.1f} cm) — passada "
                "sem propulsão; aumente a cadência para recuperar fase de "
                "voo."
            )
        else:
            descricao = (
                f"Oscilação vertical excessiva ({valor:.1f} cm) — corrida "
                "anti-econômica, propensão a fadiga precoce."
            )
    return RecomendacaoGerada(
        categoria=categoria, descricao=descricao, severidade=severidade
    )


_SIMETRIA_ROTULOS = {
    "simetria_tcs": "de tempo de contato com o solo (TCS)",
    "simetria_joelho": "do ângulo do joelho no contato",
    "simetria_oscilacao": "da oscilação vertical",
}


def _analisar_simetria(tipo: str, valor: float) -> RecomendacaoGerada:
    severidade = _classificar_simetria(valor)
    rotulo = _SIMETRIA_ROTULOS.get(tipo, "")
    categoria = f"Simetria {rotulo}".strip()
    if severidade == SEVERIDADE_INFORMATIVO:
        descricao = (
            f"Assimetria {rotulo} de {valor:.1f}% — simetria boa entre os "
            "lados esquerdo e direito."
        )
    elif severidade == SEVERIDADE_ATENCAO:
        descricao = (
            f"Assimetria {rotulo} de {valor:.1f}% — leve desequilíbrio "
            "entre os lados; atente ao seu padrão de apoio."
        )
    else:
        descricao = (
            f"Assimetria {rotulo} de {valor:.1f}% — desequilíbrio "
            "significativo entre os lados e preditor relevante de lesão; "
            "procure avaliação profissional."
        )
    return RecomendacaoGerada(
        categoria=categoria, descricao=descricao, severidade=severidade
    )


_ANALISADORES: dict[str, Callable[[str, float], RecomendacaoGerada]] = {
    "angulo_joelho_esq": _analisar_joelho,
    "angulo_joelho_dir": _analisar_joelho,
    "angulo_cotovelo_esq": _analisar_cotovelo,
    "angulo_cotovelo_dir": _analisar_cotovelo,
    "inclinacao_tronco": _analisar_tronco,
    "overstriding_esq": _analisar_overstriding,
    "overstriding_dir": _analisar_overstriding,
    "oscilacao_vertical": _analisar_oscilacao,
    "simetria_tcs": _analisar_simetria,
    "simetria_joelho": _analisar_simetria,
    "simetria_oscilacao": _analisar_simetria,
}


def _peso_severidade(severidade: str) -> float:
    if severidade == SEVERIDADE_CRITICO:
        return PESO_CRITICO
    if severidade == SEVERIDADE_ATENCAO:
        return PESO_ATENCAO
    return 0.0


def _montar_feedback(
    nota: float, recomendacoes: Sequence[RecomendacaoGerada]
) -> str:
    n_critico = sum(
        1 for r in recomendacoes if r.severidade == SEVERIDADE_CRITICO
    )
    n_atencao = sum(
        1 for r in recomendacoes if r.severidade == SEVERIDADE_ATENCAO
    )
    n_ideal = sum(
        1 for r in recomendacoes if r.severidade == SEVERIDADE_INFORMATIVO
    )
    partes = [f"Nota geral: {nota:.1f}/10."]
    if n_critico:
        partes.append(
            f"{n_critico} ponto(s) crítico(s) identificado(s)."
        )
    if n_atencao:
        partes.append(f"{n_atencao} ponto(s) de atenção.")
    if n_ideal:
        partes.append(f"{n_ideal} métrica(s) dentro da faixa ideal.")
    return " ".join(partes)


def analisar_metricas(
    metricas: Sequence[tuple[str, float]],
) -> AnaliseResultado:
    """Analisa as métricas e produz recomendações + nota geral.

    Recebe pares ``(tipo, valor)`` das métricas **não informativas**
    persistidas em ``METRICA`` (o chamador filtra ``apenas_informativa``
    antes). Para cada métrica conhecida, classifica a severidade via
    tabela de thresholds da Seção 9 do PRD e gera uma
    :class:`RecomendacaoGerada` — inclusive para métricas ``ideal``
    (severidade ``informativo``), permitindo feedback positivo no
    diagnóstico simplificado (US-025).

    A nota geral é ``10 − ∑pesos``, clamped em ``[0, 10]``. Pesos:
    ``informativo = 0``, ``atencao = PESO_ATENCAO``, ``critico =
    PESO_CRITICO`` — crítico é deliberadamente maior que atenção.
    Tipos desconhecidos são ignorados silenciosamente.
    """
    recomendacoes: list[RecomendacaoGerada] = []
    penalizacao = 0.0
    for tipo, valor in metricas:
        analisador = _ANALISADORES.get(tipo)
        if analisador is None:
            continue
        rec = analisador(tipo, valor)
        recomendacoes.append(rec)
        penalizacao += _peso_severidade(rec.severidade)

    nota = NOTA_MAXIMA - penalizacao
    if nota < 0.0:
        nota = 0.0
    elif nota > NOTA_MAXIMA:
        nota = NOTA_MAXIMA

    feedback = _montar_feedback(nota, recomendacoes)
    return AnaliseResultado(
        nota_geral=nota,
        feedback_ia=feedback,
        recomendacoes=tuple(recomendacoes),
    )
